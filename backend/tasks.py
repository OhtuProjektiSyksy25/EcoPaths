from invoke import task

@task
def format(c):
    """Format code using autopep8"""
    c.run("autopep8 --in-place --recursive src")
    print("Code formatted.")

@task
def lint(c):
    """Run Pylint on src"""
    c.run("poetry run pylint src")

@task
def test(c):
    """Run all tests with coverage tracking"""
    c.run("poetry run pytest --cov=src tests")

@task(pre=[test])
def coverage(c):
    """Generate coverage reports after tests"""
    c.run("poetry run coverage html")
    c.run("poetry run coverage xml -o coverage.xml")

@task
def clean(c):
    """Clean up test artifacts"""
    c.run("rm -rf .coverage htmlcov coverage.xml")

@task(pre=[lint, test])
def check(c):
    """Run lint and tests"""
    print("Check done.")

@task(pre=[format, lint, coverage])
def full(c):
    """Run format + lint + coverage"""
    print("Formatted and checked!")

@task
def run(ctx):
    """Run backend in development mode"""
    ctx.run("poetry run uvicorn src.main:app --reload", pty=True)
