import os
import sys
import gc
import subprocess
import signal
import socket
from invoke import task
from backend.src.database.db_client import DatabaseClient

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
    inv fill-area-tables --area=berlin --network-type=walking --overwrite-edges
"""

@task
def reset_and_populate_area(c, area: str):
    """
    Reset and repopulate all tables for a given area.
    Runs driving and walking networks separately to avoid memory accumulation.
    """
    network_types = ["driving", "walking"]

    print(f"\n[AREA] Resetting grid and tables for area '{area}'")
    reset_grid(c, area)

    for i, network_type in enumerate(network_types):
        print(f"\n[NETWORK] Starting network '{network_type}'\n")

        subprocess.run([
            sys.executable, "-m", "invoke",
            "reset-area", "--area", area, "--network-type", network_type
        ], check=True)

        subprocess.run([
            sys.executable, "-m", "invoke",
            "create-all-tables", "--area", area, "--network-type", network_type
        ], check=True)

        subprocess.run([
            sys.executable, "-m", "invoke",
            "fill-area-tables", "--area", area,
            "--network-type", network_type,
            "--overwrite-edges",
            *(["--overwrite-grid"] if i == 0 else [])
        ], check=True)

        gc.collect()
        print(f"[NETWORK] Completed network '{network_type}'\n")


@task
def create_all_tables(c, area: str, network_type: str):
    """
    Create all ORM-defined tables for a specific area and network type.
    """
    db = DatabaseClient()
    db.create_tables_for_area(area, network_type)
    print(f"[DB] Tables ensured for area '{area}' ({network_type})")


@task
def fill_area_tables(c, area: str, network_type: str, overwrite_edges=False, overwrite_grid=False):
    """
    Populate grid and edge tables for a specific area and network type.
    Prints summarized output of actions performed.
    """
    from backend.preprocessor.osm_preprocessor import OSMPreprocessor
    from backend.src.config.settings import get_settings
    from backend.src.utils.grid import Grid

    print(f"\n[DB] Starting database population for area '{area}', network '{network_type}'")
    
    db_client = DatabaseClient()
    grid_table = f"grid_{area.lower()}"
    edge_table = f"edges_{area.lower()}_{network_type.lower()}"

    if not db_client.table_exists(edge_table):
        raise RuntimeError(f"[ERROR] Edge table '{edge_table}' does not exist. Run 'create-all-tables' first.")

    # GRID
    grid = Grid(get_settings(area).area)
    grid_gdf = grid.create_grid()
    grid_action = "Skipped"
    if not db_client.table_exists(grid_table) or overwrite_grid:
        db_client.save_grid(grid_gdf, area=area, if_exists="replace" if overwrite_grid else "fail")
        grid_action = "Created"

    # EDGES
    edges_action = "Skipped"
    if not db_client.table_exists(edge_table) or overwrite_edges:
        preprocessor = OSMPreprocessor(area=area, network_type=network_type)
        preprocessor.extract_edges()
        edges_action = "Created"

    print(f"[GRID] Table: {grid_action}")
    print(f"[EDGES] Table: {edges_action}")
    print(f"[DB] Database population complete for area '{area}', network '{network_type}'\n")

@task
def drop_table(c, table_name: str):
    """
    Drop a specific table from the database.
    """
    db = DatabaseClient()
    db.drop_table(table_name)


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
        f"nodes_{area.lower()}_{network_type.lower()}"
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
def reset_grid(c, area: str):
    """
    Drop grid table and its index for a given area, summarized output.
    """
    from backend.src.database.db_client import DatabaseClient
    db = DatabaseClient()

    grid_table = f"grid_{area.lower()}"
    grid_index = f"idx_{grid_table}_geometry"

    dropped_items = []

    if db.table_exists(grid_table):
        db.drop_table(grid_table)
        dropped_items.append(grid_table)

    try:
        db.execute(f"DROP INDEX IF EXISTS {grid_index};")
        dropped_items.append(grid_index)
    except Exception as e:
        print(f"Warning: failed to drop index {grid_index}: {e}")

    if dropped_items:
        print(f"Dropped items: {', '.join(dropped_items)}")
    else:
        print(f"No grid table or index existed for area '{area}'")
