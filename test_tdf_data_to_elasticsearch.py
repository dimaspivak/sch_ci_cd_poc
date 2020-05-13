import logging
import string
import time

import pytest
import sqlalchemy
from elasticsearch_dsl import Index
from streamsets.testframework.utils import get_random_string

logger = logging.getLogger(__name__)

SAMPLE_DATA = [dict(year=1903, rank=1, name='MAURICE GARIN', number=1, team='TDF 1903',
                    time='94h 33m 14s', hours=94, mins=33, secs=14),
               dict(year=1903, rank=2, name='LUCIEN POTHIER', number=37, team='TDF 1903',
                    time='97h 32m 35s', hours=97, mins=32, secs=35),
               dict(year=1903, rank=3, name='FERNAND AUGEREAU', number=39, team='TDF 1903',
                    time='99h 02m 38s', hours=99, mins=2, secs=38)]


def test_complete(elasticsearch_data):
    """Smoke test for the tdf_data_to_elasticsearch pipeline."""
    # Data in Elasticsearch should be identical except that the "name" field should be split and prettified.
    EXPECTED_RECORDS = [dict(year=1903, rank=1, firstName='Maurice', lastName='Garin', number=1, team='TDF 1903',
                             time='94h 33m 14s', hours=94, mins=33, secs=14),
                        dict(year=1903, rank=2, firstName='Lucien', lastName='Pothier', number=37, team='TDF 1903',
                             time='97h 32m 35s', hours=97, mins=32, secs=35),
                        dict(year=1903, rank=3, firstName='Fernand', lastName='Augereau', number=39, team='TDF 1903',
                             time='99h 02m 38s', hours=99, mins=2, secs=38)]
    assert EXPECTED_RECORDS == elasticsearch_data


def test_remove_id_field(elasticsearch_data):
    """Test to assert that ID was removed."""
    assert all('id' not in record for record in elasticsearch_data)


def test_split_name(elasticsearch_data):
    """Test that first name and last name are split as expected."""
    EXPECTED_NAMES = [dict(firstName='Maurice', lastName='Garin'),
                      dict(firstName='Lucien', lastName='Pothier'),
                      dict(firstName='Fernand', lastName='Augereau')]
    assert EXPECTED_NAMES == [{key: record[key] for key in ['firstName', 'lastName']}
                              for record in elasticsearch_data]


@pytest.fixture(scope='module')
def elasticsearch_data(sch, pipeline, database, elasticsearch):
    """Carry out test job actions and yield the data in the test Elasticsearch environment.

    1. Create table and load sample data into database.
    2. Create and run job using pipeline.
    3. Pull data from Elasticsearch and assert on its correctness.
    """
    table_name = get_random_string()
    index = get_random_string(string.ascii_lowercase)

    table = sqlalchemy.Table(table_name,
                             sqlalchemy.MetaData(),
                             sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),
                             sqlalchemy.Column('year', sqlalchemy.Integer),
                             sqlalchemy.Column('rank', sqlalchemy.Integer),
                             sqlalchemy.Column('name', sqlalchemy.String(100)),
                             sqlalchemy.Column('number', sqlalchemy.Integer),
                             sqlalchemy.Column('team', sqlalchemy.String(100)),
                             sqlalchemy.Column('time', sqlalchemy.String(100)),
                             sqlalchemy.Column('hours', sqlalchemy.Integer),
                             sqlalchemy.Column('mins', sqlalchemy.Integer),
                             sqlalchemy.Column('secs', sqlalchemy.Integer))
    try:
        logger.info('Creating table (%s) in database ...', table_name)
        table.create(database.engine)

        logger.info('Inserting sample data ...')
        connection = database.engine.connect()
        connection.execute(table.insert(), SAMPLE_DATA)

        logger.info('Creating test job ...')
        job_builder = sch.get_job_builder()
        runtime_parameters=dict(JDBC_CONNECTION_STRING=database.jdbc_connection_string,
                                JDBC_USERNAME=database.username,
                                JDBC_PASSWORD=database.password,
                                ELASTICSEARCH_URI=f'{elasticsearch.hostname}:{elasticsearch.port}',
                                ELASTICSEARCH_CREDENTIALS=f'{elasticsearch.username}:{elasticsearch.password}',
                                ELASTICSEARCH_INDEX=index,
                                TABLE_NAME_PATTERN=f'%{table_name}%')
        job = job_builder.build('Test job for tdf_data_to_elasticsearch pipeline',
                                pipeline=pipeline,
                                runtime_parameters=runtime_parameters)
        job.description = 'CI/CD test job'
        job.data_collector_labels = ['CI/CD Test']
        sch.add_job(job)
        sch.start_job(job)

        # Wait for records to be written.
        time.sleep(10)

        data_in_elasticsearch = [hit.to_dict() for hit in elasticsearch.search(index=index).sort('rank').execute()]
        yield data_in_elasticsearch
    finally:
        sch.stop_job(job)

        logger.info('Deleting Elasticsearch index %s ...', index)
        Index(index, using=elasticsearch.client).delete()

        logger.info('Dropping table %s ...', table_name)
        table.drop(database.engine)

