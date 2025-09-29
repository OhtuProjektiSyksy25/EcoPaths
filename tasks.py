from invoke import task

# ========================
# Code formatting & linting
# ========================

@task
def format(c):
    """Format backend code using autopep8"""
    with c.cd("backend"):
        c.run("autopep8 --in-place --recursive src")
    print("Code formatted.")


@task
def lint(c):
    """Run Pylint on backend/src"""
    with c.cd("backend"):
        c.run("poetry run pylint src")
    print("Linting completed.")


# ========================
# Testing & coverage
# ========================

@task
def backend_test(c):
    """Run backend tests with coverage tracking"""
    with c.cd("backend"):
        c.run(
            "poetry run pytest --cov=src --cov-report=term-missing "
            "--cov-report=xml:../coverage_reports/backend/coverage.xml tests"
        )
        c.run("poetry run coverage html -d ../coverage_reports/backend/htmlcov")
    print("Backend coverage reports generated in coverage_reports/backend/")


@task
def frontend_test(c):
    """Run frontend tests (currently not available)"""
    print("Frontend tests not run yet")
    # When frontend tests are ready, you can enable:
    # with c.cd("frontend"):
    #     c.run("npm test -- --watchAll=false")
    #     # optionally generate coverage in coverage_reports/frontend/


# ========================
# Utility tasks
# ========================

@task
def clean(c):
    """Clean backend test artifacts and coverage reports"""
    with c.cd("backend"):
        c.run("rm -rf .coverage")
    c.run("rm -rf coverage_reports/backend/")
    print("Removed backend test artifacts and coverage reports")


# ========================
# Higher-level convenience tasks
# ========================

@task(pre=[backend_test, frontend_test])
def coverage(c):
    """Run all tests and generate coverage reports"""
    print("All tests completed and coverage reports generated.")


@task(pre=[backend_test, lint])
def backend_check(c):
    """Run lint and backend tests with coverage"""
    print("Backend checked.")


@task(pre=[format, backend_check])
def full(c):
    """Format code, lint, run tests, and generate coverage"""
    print("Code formatted and fully checked!")


# ========================
# Development server
# ========================

@task
def run(c):
    """Run backend in development mode"""
    with c.cd("backend"):
        c.run("poetry run uvicorn src.main:app --reload", pty=True)
