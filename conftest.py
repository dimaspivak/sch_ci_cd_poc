import logging

import pytest

logger = logging.getLogger('streamsets.ci_cd_poc')


def pytest_addoption(parser):
    parser.addoption('--pipeline-id')
    parser.addoption('--upgrade-jobs', action='store_true')

@pytest.fixture(scope='session')
def pipeline(sch, request):
    pipeline_ = sch.pipelines.get(pipeline_id=request.config.getoption('pipeline_id'))
    yield pipeline_
    if not request.session.testsfailed:
        if request.config.getoption('upgrade_jobs'):
            jobs_to_upgrade = [job
                               for job in sch.jobs.get_all(pipeline_id=pipeline_.pipeline_id)
                               if job.description != 'CI test job']
            if jobs_to_upgrade:
                logger.info('Upgrading jobs: %s ...', ', '.join(jobs_to_upgrade))
                sch.upgrade_job(*jobs_to_upgrade)
            else:
                logger.warning('No jobs need to be upgraded')
