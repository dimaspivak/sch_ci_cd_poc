This repository contains code that shows an example on how [CI/CD](https://en.wikipedia.org/wiki/CI/CD) can be achieved for [StreamSets Control Hub](https://streamsets.com/products/dataops-platform/control-hub/).

# Prerequisites

* [Python 3.4+](https://docs.python.org/3/using/index.html) and pip3 installed
* StreamSets for SDK [Installed and activated](https://streamsets.com/documentation/sdk/latest/installation.html)
* StreamSets Test Framework [installed](https://streamsets.com/documentation/stf/latest/installation.html) 
* [Access to StreamSets Control Hub](https://streamsets.com/documentation/controlhub/latest/help/controlhub/UserGuide/OrganizationSecurity/OrgSecurity_Overview.html#concept_q5z_jkl_wy) with an user account in your  organization 
* At least one [StreamSets Data Collector](https://streamsets.com/products/dataops-platform/data-collector/) instance registered with the above StreamSets Control Hub instance
and has a label = 'CI/CD test'

# Goal
**Brief:** Validate a pipeline before deploying

**Details:**
Test if a newer version of a pipeline, breaks the functioning.

If it does not, upgrade any StreamSets Control Hub Job which runs that pipeline with the latest version. In essence, deploy it.

If it breaks, do not upgrade the job and hence avoid data loss and headache ina all aspects. In essence, do not deploy it.

# Overview
The following is a workflow that happens with code in this repo:

1. For testing, creates a [StreamSets Control Hub Job](https://streamsets.com/documentation/controlhub/latest/help/controlhub/UserGuide/Jobs/Jobs_title.html)
   using the latest version of the pipeline that has new changes which need to be validated.
   
2. Runs the job against a different environment 
e.g. dev - which consists of in this case, MySQL and Kinesis on a different instance than production.

3. Inserts test data in dev MySQL instance.

4. Runs the job against this dev  MySQL instance and dev Kinesis instance.

5. After the job run is completed, verifes data in dev Kinesis by running tests from this repo.

6. If tests pass, upgrades any StreamSets Control Hub Jobs which run that pipeline with the latest version. In essence, deploy it.

7. Else if any of the tests fail, does not upgrade the job and hence avoid data loss and headache in all aspects. In essence, do not deploy it.
 
# Sample way to execute tests
Replace parameter values specified inside <> according to your setup.

Note: Run the tests using dev. instances of Kinesis and MySQL and not production ones.

```
stf test -vs --sch-server-url=<SCH_SERVER_URL> \

    --sch-username=<SCH_USERNAME> \ 

    --sch-password=<SCH_PASSWORD> \

    --pipeline-id <PIPELINE_ID> \

    --elasticsearch-url 'http://<ELASTCSEARCH_USER>:<ELASTCSEARCH_PASSWORD>@<ELASTCSEARCH_IP>:<ELASTCSEARCH_PORT>/' \

    --database 'mysql://<MYSQL_IP>:<MYSQL_PORT>/<MYSQL_DATABASE_NAME>' \

    --upgrade-jobs
```

# Some important concepts used in this repo

## CI/CD
In software engineering, CI/CD(https://en.wikipedia.org/wiki/CI/CD) or CICD generally refers to the combined practices of continuous integration and either continuous delivery or continuous deployment.

CI = [Continuous Integration](https://en.wikipedia.org/wiki/Continuous_integration)
In software engineering, **continuous integration (CI)** is the practice of merging all developers' working copies to a shared mainline several times a day.

CD = [continuous delivery](https://en.wikipedia.org/wiki/Continuous_delivery) or [continuous deployment](https://en.wikipedia.org/wiki/Continuous_deployment)

**Continuous delivery (CD)** is a software engineering approach in which teams produce software in short cycles, ensuring that the software can be reliably released at any time and, when releasing the software, doing so manually.

**Continuous deployment (CD)** is a software engineering approach in which software functionalities are delivered frequently through automated deployments. CD contrasts with continuous delivery, a similar approach in which software functionalities are also frequently delivered and deemed to be potentially capable of being deployed but are actually not deployed. 
   
## pytest fixtures
[Pytest fixtures](https://docs.pytest.org/en/stable/fixture.html) - Software test fixtures initialize test functions. Initialization may setup services, state, or other operating environments. 

These are accessed by test functions through arguments; for each fixture used by a test function there is typically a parameter (named after the fixture) in the test function’s definition.
   
## yield in Python
The big difference between [yield](https://docs.python.org/3/howto/functional.html#generators) and a return statement is that on reaching a yield the generator’s state of execution is suspended and local variables are preserved. On the next call to the generator’s __next__() method, the function will resume executing.   

## pytest request fixture
A good tutorial on [pytest request fixture](https://docs.pytest.org/en/stable/reference.html#std-fixture-request)
is available [here](https://docs.pytest.org/en/stable/example/simple.html#request-example).   
