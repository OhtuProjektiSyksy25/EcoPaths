import subprocess
import signal
from invoke import task

# ========================
# Code formatting & linting
# ========================

@task
def format_backend(c):
    """Format backend code using autopep8"""
    with c.cd("backend"):
        c.run("autopep8 --in-place --recursive src")
    print("Code formatted.")


@task
def lint_backend(c):
    """Run Pylint on backend/src"""
    with c.cd("backend"):
        c.run("poetry run pylint src")
    print("Linting completed.")


# ========================
# Testing & coverage
# ========================

@task
def test_backend(c):
    """Run backend unit tests with coverage tracking"""
    with c.cd("backend"):
        c.run(
            "poetry run pytest --cov=src --cov-report=term-missing "
            "--cov-report=xml:../coverage_reports/backend/coverage.xml tests"
        )
        c.run("poetry run coverage html -d ../coverage_reports/backend/htmlcov")
    print("Backend coverage reports generated in coverage_reports/backend/")


@task
def test_frontend(c):
    """Run frontend tests with coverage tracking"""
    with c.cd("frontend"):
        c.run("npm test -- --watchAll=false")
    print("Frontend coverage reports generated in coverage_reports/frontend/")

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

@task(pre=[test_backend, test_frontend])
def coverage(c):
    """Run backend and frontend tests and generate coverage reports"""
    print("All tests completed and coverage reports generated.")


@task(pre=[test_backend, lint_backend])
def check_backend(c):
    """Run lint and unit tests with coverage"""
    print("Backend checked.")


@task(pre=[format_backend, check_backend])
def full(c):
    """Format code, lint, run tests, and generate coverage"""
    print("Code formatted and fully checked!")


# ========================
# Development server
# ========================

@task
def run_backend(c):
    """Run backend in development mode"""
    with c.cd("backend"):
        c.run("poetry run uvicorn src.main:app --reload --port 8000", pty=True)
    
@task
def run_frontend(c):
    """Run frontend in development mode"""
    with c.cd("frontend"):
        c.run("npm start", pty=True)

@task
def run_all(c):
    """Run both backend and frontend in development mode"""
    print("Starting full development environment...")
    print("Backend: http://127.0.0.1:8000")
    print("Frontend: http://localhost:3000")

    backend_proc = subprocess.Popen(
        ["poetry", "run", "uvicorn", "src.main:app", "--reload"],
        cwd="backend"
    )
    frontend_proc = subprocess.Popen(
        ["npm", "start"],
        cwd="frontend"
    )

    try:
        backend_proc.wait()
        frontend_proc.wait()
    except KeyboardInterrupt:
        print("\nStopping development environment...")
        backend_proc.send_signal(signal.SIGINT)
        frontend_proc.send_signal(signal.SIGINT)
        backend_proc.wait()
        frontend_proc.wait()
        print("Development environment stopped.")


# ========================
# OSM Preprocessor tasks
# ========================

@task
def preprocess_osm(c, area="berlin", network="walking", dry_run=False, format="parquet"):
    """Run OSM preprocessing for a given area and network type"""
    from backend.preprocessor.osm_preprocessor import OSMPreprocessor

    print(f"Preprocessing area '{area}' with network '{network}'...")
    processor = OSMPreprocessor(area=area, network_type=network)
    graph = processor.extract_edges()

    print(f"Network processed: {len(graph)} edges")

    if dry_run:
        print("Dry-run enabled: output not saved.")

    if format == "gpkg":
        gpkg_path = processor.output_path.with_suffix(".gpkg")
        graph.to_file(gpkg_path, driver="GPKG")
        print(f"Saved to GeoPackage: {gpkg_path}")

    print("Preprocessing complete.")
