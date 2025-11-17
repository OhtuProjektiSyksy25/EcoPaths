import os
import sys
import gc
import subprocess
import signal
import socket
from invoke import task
from backend.src.database.db_client import DatabaseClient
from backend.preprocessor.osm_pipeline_runner import OSMPipelineRunner

# ========================
# Code formatting & linting
# ========================

@task
def format_backend(c):
    """Format backend code using autopep8 for src, preprocessor, and tests"""
    with c.cd("backend"):
        c.run("autopep8 --in-place --recursive src preprocessor tests")
    print("Code formatted.")


@task
def lint_backend(c):
    """Run Pylint on all backend modules: src, preprocessor, and tests."""
    with c.cd("backend"):
        c.run("poetry run pylint src preprocessor tests")
    print("Linting completed.")

@task
def format_frontend(c):
    """Format frontend code using prettier"""
    with c.cd("frontend"):
        c.run("npm run format")

@task
def lint_frontend(c):
    """Run prettier check on frontend"""
    with c.cd("frontend"):
        c.run("npm run check-format")


# ========================
# Testing & coverage
# ========================

@task
def test_backend(c):
    """Run backend unit tests with coverage tracking"""
    with c.cd("backend"):
        env = {"ENV": "test"}
        c.run(
            "poetry run pytest --cov=src --cov=preprocessor --cov-report=term-missing "
            "--cov-report=xml:../coverage_reports/backend/coverage.xml tests",
            env=env,
        )
        c.run(
            "poetry run coverage html -d ../coverage_reports/backend/htmlcov",
            env=env,
        )
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


@task(pre=[lint_backend, test_backend])
def check_backend(c):
    """Run lint and unit tests with coverage"""
    print("Backend checked.")

@task(pre=[lint_frontend, test_frontend])
def check_frontend(c):
    """Run lint and tests for frontend"""
    print("Frontend checked")

@task(pre=[format_backend, check_backend, format_frontend, check_frontend])
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
def run_redis(c):
    """Start Redis server locally"""
    if is_redis_running():
        print("Redis is already running.")
    else:
        print("Starting Redis server...")
        c.run("redis-server", pty=True)

def is_redis_running(host="127.0.0.1", port=6379):
    """Return True if Redis port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex((host, port)) == 0
    
def is_container_running(name):
    result = subprocess.run(
        ["docker", "ps", "--filter", f"name={name}", "--filter", "status=running", "--format", "{{.Names}}"],
        capture_output=True, text=True
    )
    return name in result.stdout.strip().split("\n")


@task
def run_all(c):
    """Run both backend, frontend, Redis and database in development mode"""
    db_user = os.getenv("DB_USER_TEST", "pathplanner")
    db_name = os.getenv("DB_NAME_TEST", "ecopaths_test")

    print("Starting full development environment...")
    print("Backend: http://127.0.0.1:8000")
    print("Frontend: http://localhost:3000")
    print("Redis: redis://localhost:6379")
    print(f"Database: postgresql://{db_user}@localhost:5432/{db_name}")

    # Start Docker Compose
    container_name = "my_postgis"

    if is_container_running(container_name):
        print(f"Docker container '{container_name}' is already running.")
    else:
        print(f"Starting Docker container '{container_name}'...")
        c.run("docker compose up -d", pty=True)

    # Start Redis
    redis_proc = None
    if is_redis_running():
        print("Redis already running.")
    else:
        print("Starting Redis...")
        redis_proc = subprocess.Popen(["redis-server"])

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
        for proc in [frontend_proc, backend_proc, redis_proc]:
            if proc is not None:
                proc.send_signal(signal.SIGINT)
                proc.wait()
        print("Development environment stopped.")



# ========================
# OSM Preprocessor and database tasks
# ========================

"""
OSM Preprocessor tasks for managing database setup.

Includes commands to:
- Drop and recreate grid and edge tables
- Populate edge data from OSM
- Ensure consistent setup for walking and driving networks

Usage:
    inv reset-and-populate-area --area=berlin
    inv create-all-tables --area=berlin --network-type=walking
"""

@task
def reset_and_populate_area(c, area: str):
    """
    Reset and repopulate all tables for a given area.
    Runs grid, green, driving and walking networks.
    """
    print(f"\n[AREA] Resetting tables for area '{area}'")
    reset_grid_and_green(c, area)
    create_grid_and_green_tables(c, area)

    for network_type in ["driving", "walking"]:
        reset_area(c, area, network_type)
        create_network_tables(c, area, network_type)


    runner = OSMPipelineRunner(area)
    runner.run()


@task
def create_grid_and_green_tables(c, area: str):
    """
    Create grid and green tables for a specific area.
    """
    db = DatabaseClient()
    db.create_grid_table(area)
    db.create_green_table(area)
    print(f"[DB] Grid and green tables ensured for area '{area}'")


@task
def create_network_tables(c, area: str, network_type: str):
    """
    Create edge and node tables for a specific area and network type.
    """
    db = DatabaseClient()
    db.create_network_tables(area, network_type)
    print(f"[DB] Network tables ensured for area '{area}' ({network_type})")

@task
def reset_area(c, area: str, network_type: str):
    """
    Drop all tables for a given area, summarized output.

    Usage:
        inv reset-area --area=berlin --network-type=walking
    """
    db = DatabaseClient()

    tables = [
        f"edges_{area.lower()}_{network_type.lower()}",
        f"nodes_{area.lower()}_{network_type.lower()}",
    ]

    dropped_tables = []
    for table in tables:
        if db.table_exists(table):
            db.drop_table(table)
            dropped_tables.append(table)

    if dropped_tables:
        print(f"[DB] Dropped tables: {', '.join(dropped_tables)}")
    else:
        print(f"[DB] No tables existed for area '{area}' and network '{network_type}'")


@task
def reset_grid_and_green(c, area: str):
    """
    Drop grid and green tables for a given area.
    """
    db = DatabaseClient()

    grid_table = f"grid_{area.lower()}"
    green_table = f"green_{area.lower()}"

    dropped_items = []

    for table in [grid_table, green_table]:
        if db.table_exists(table):
            db.drop_table(table)
            dropped_items.append(table)

    if dropped_items:
        print(f"[DB] Dropped tables: {', '.join(dropped_items)}")
    else:
        print(f"[DB] No grid or green tables existed for area '{area}'")
