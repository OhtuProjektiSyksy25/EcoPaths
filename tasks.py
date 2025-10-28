import subprocess
import signal
 
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
        c.run(
            "poetry run pytest --cov=src --cov=preprocessor --cov-report=term-missing "
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
# Grid generation
# ========================

@task
def create_grid(c, area=None):
    """
    Create a grid for the specified area.
    """
    if area is None:
        print("Error: --area parameter is required")
        print("Usage: inv create-grid --area=<city>")
        return

    print(f"Creating grid for {area}...")

    with c.cd("backend"):
        c.run(f"""
poetry run python -c "
from src.utils.grid import Grid
from src.config.settings import AreaConfig

try:
    config = AreaConfig('{area}')
    grid = Grid(config)
    
    # Check if grid already exists
    if config.grid_file.exists():
        print('Grid already exists.')
    
    grid_gdf = grid.create_grid()
    print(f'Loaded {{len(grid_gdf)}} tiles')
    print(f'File: {{config.grid_file}}')
    
except ValueError as e:
    print(f'Error: {{e}}')
    print('Area not available. Check available areas in settings.py.')
"
        """, warn=True)

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
    c.run("redis-server", pty=True)

@task
def run_all(c):
    """Run both backend, frontend and Redis in development mode"""
    print("Starting full development environment...")
    print("Backend: http://127.0.0.1:8000")
    print("Frontend: http://localhost:3000")
    print("Redis: redis://localhost:6379")

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
            proc.send_signal(signal.SIGINT)
            proc.wait()
        print("Development environment stopped.")


# ========================
# OSM Preprocessor and database tasks
# ========================

@task
def populate_database(c, area: str, network_type: str = "walking", overwrite_edges=False, overwrite_grid=False):
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
    db_client.create_tables_for_area(area, network_type)

    grid_table = f"grid_{area.lower()}"
    edge_table = f"edges_{area.lower()}_{network_type.lower()}"

    # GRID
    if db_client.table_exists(grid_table):
        if not overwrite_grid:
            print(f"Grid table '{grid_table}' already exists. Skipping grid creation.")
            print("To overwrite, use: --overwrite-grid")
        else:
            print(f"Overwriting existing grid in table '{grid_table}'...")
            settings = get_settings(area)
            grid = Grid(settings.area)
            grid_gdf = grid.create_grid()
            db_client.save_grid(grid_gdf, area=area, if_exists="replace")
    else:
        print(f"Creating new grid for area '{area}'...")
        settings = get_settings(area)
        grid = Grid(settings.area)
        grid_gdf = grid.create_grid()
        db_client.save_grid(grid_gdf, area=area, if_exists="fail")

    # EDGES
    if db_client.table_exists(edge_table):
        if not overwrite_edges:
            print(f"Edge table '{edge_table}' already exists. Skipping edge extraction.")
            print("To overwrite, use: --overwrite-edges")
        else:
            print(f"Overwriting edge data in table '{edge_table}'...")
            preprocessor = OSMPreprocessor(area=area, network_type=network_type)
            edges_gdf = preprocessor.extract_edges()
            db_client.save_edges(edges_gdf, area=area, network_type=network_type, if_exists="replace")
    else:
        print(f"Creating edge data for table '{edge_table}'...")
        preprocessor = OSMPreprocessor(area=area, network_type=network_type)
        edges_gdf = preprocessor.extract_edges()
        db_client.save_edges(edges_gdf, area=area, network_type=network_type, if_exists="fail")

    print(f"Database population complete for area '{area}', network type '{network_type}'.")

