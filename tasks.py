import subprocess
import signal
import socket
from invoke import task
import geopandas as gpd
from pathlib import Path


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
def run_redis(c):
    """Start Redis server locally (only if not already running)"""
    if is_redis_running():
        print("Redis is already running.")
    else:
        print("Starting Redis server...")
        c.run("redis-server", pty=True)

def is_redis_running(host="127.0.0.1", port=6379):
    """Return True if Redis port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex((host, port)) == 0
    
@task
def run_all(c):
    """Run both backend, frontend and Redis in development mode"""
    print("Starting full development environment...")
    print("Backend: http://127.0.0.1:8000")
    print("Frontend: http://localhost:3000")
    print("Redis: redis://localhost:6379")

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

@task
def reset_and_populate_area(c, area: str, network_type: str):
    """
    Drop all tables for a given area and repopulate the database from scratch.

    Usage:
        inv reset-and-populate-area --area=berlin --network-type=walking
    """
    reset_area(c, area, network_type)
    create_all_tables(c, area, network_type)
    populate_database(c, area, network_type, overwrite_edges=True, overwrite_grid=True)


@task
def create_all_tables(c, area: str, network_type: str):
    """
    Create all ORM-defined tables for a specific area and network type.

    Usage:
        inv create-all-tables --area=berlin --network-type=walking
    """
    from backend.src.database.db_client import DatabaseClient
    db = DatabaseClient()
    db.create_tables_for_area(area, network_type)


@task
def populate_database(c, area: str, network_type: str, overwrite_edges=False, overwrite_grid=False):
    """
    Create necessary tables and populate the database with grid and edge data for a specific area.

    Usage:
        inv populate-database --area=berlin --network-type=walking --overwrite-edges --overwrite-grid
    """
    from backend.src.database.db_client import DatabaseClient
    from backend.preprocessor.osm_preprocessor import OSMPreprocessor
    from backend.src.config.settings import get_settings
    from backend.src.utils.grid import Grid

    print(f"Starting database population for area: '{area}', network type: '{network_type}'")

    db_client = DatabaseClient()

    grid_table = f"grid_{area.lower()}"
    edge_table = f"edges_{area.lower()}_{network_type.lower()}"

    if not db_client.table_exists(edge_table):
        raise RuntimeError(f"Edge table '{edge_table}' does not exist. Run 'create-all-tables' first.")

    # GRID
    settings = get_settings(area)
    grid = Grid(settings.area)
    grid_gdf = grid.create_grid()

    if db_client.table_exists(grid_table) and not overwrite_grid:
        print(f"Grid table '{grid_table}' already exists. Skipping (use --overwrite-grid to force).")
    else:
        action = "Overwriting" if overwrite_grid else "Creating"
        print(f"{action} grid for area '{area}'...")
        db_client.save_grid(grid_gdf, area=area, if_exists="replace" if overwrite_grid else "fail")

    # EDGES
    if db_client.table_exists(edge_table) and not overwrite_edges:
        print(f"Edge table '{edge_table}' already exists. Skipping (use --overwrite-edges to force).")
    else:
        action = "Overwriting" if overwrite_edges else "Creating"
        print(f"{action} edge data for table '{edge_table}'...")
        preprocessor = OSMPreprocessor(area=area, network_type=network_type)
        preprocessor.extract_edges() 

    print(f"Database population complete for area '{area}', network type '{network_type}'.")

@task
def drop_table(c, table_name: str):
    """
    Drop a specific table from the database.

    Usage:
        inv drop-table --table-name=edges_berlin_walking
    """
    from backend.src.database.db_client import DatabaseClient

    db = DatabaseClient()
    db.drop_table(table_name)


@task
def reset_area(c, area: str, network_type: str):
    """
    Drop all tables for a given area and repopulate the database.

    Usage:
        inv reset-area --area=berlin --network-type=walking
    """
    from backend.src.database.db_client import DatabaseClient
    db = DatabaseClient()

    tables = [
        f"edges_{area.lower()}_{network_type.lower()}",
        f"grid_{area.lower()}",
        f"nodes_{area.lower()}_{network_type.lower()}"
    ]

    for table in tables:
        if db.table_exists(table):
            print(f"Dropping table: {table}")
            db.drop_table(table)

