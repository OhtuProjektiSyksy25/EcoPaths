from invoke import task

@task
def format(c):
    """Format code using autopep8"""
    c.run("autopep8 --in-place --recursive src")

@task
def lint(c):
    """Run Pylint on src"""
    c.run("poetry run pylint src")

@task
def test(c):
    """Run all unit tests with coverage tracking"""
    c.run("PYTHONPATH=src poetry run coverage run -m pytest tests")

@task(pre=[test])
def coverage(c):
    """Generate coverage report after tests"""
    c.run("poetry run coverage report -m")
    c.run("poetry run coverage html")

@task
def clean(c):
    """Clean up test artifacts"""
    c.run("rm -rf .coverage htmlcov coverage.xml")

@task(pre=[lint, test])
def check(c):
    """Run lint and tests (quick check)"""
    print("Code checks passed.")

@task(pre=[format, lint, coverage])
def all(c):
    """Run format + lint + coverage"""
    print("All checks done!")
