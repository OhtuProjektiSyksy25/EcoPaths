from invoke import task

@task
def lint(c):
    """Run Pylint on src"""
    c.run("poetry run pylint src")

@task
def test(c):
    """Run all unit tests"""
    c.run("poetry run pytest tests")

@task
def coverage(c):
    """Run tests with coverage and generate report"""
    c.run("poetry run coverage run -m pytest tests")
    c.run("poetry run coverage report")
    c.run("poetry run coverage html")

@task(pre=[lint, coverage])
def all(c):
    """Run lint + coverage"""
    print("All checks done!")
