from invoke import task

@task
def lint(c):
    """Run Pylint on src"""
    c.run("poetry run pylint src")

@task
def test(c):
    """Run all unit tests"""
    c.run("poetry run pytest src/tests")

@task
def coverage(c):
    """Run tests with coverage and generate report"""
    c.run("poetry run coverage run -m pytest src/tests")
    c.run("poetry run coverage report")
    c.run("poetry run coverage html")

@task
def clean(c):
    """Clean up test artifacts"""
    c.run("rm -rf .coverage htmlcov coverage.xml")

@task(pre=[lint, coverage])
def all(c):
    """Run lint + coverage"""
    print("All checks done!")
