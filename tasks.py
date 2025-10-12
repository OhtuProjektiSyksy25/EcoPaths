import subprocess
import signal
from invoke import task
from shapely import area, box
import geopandas as gpd
from pathlib import Path

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
def preprocess_osm(c, area="berlin", network="walking", overwrite=False):
    """Run OSM preprocessing for a given area and network type"""
    from backend.preprocessor.osm_preprocessor import OSMPreprocessor
    from backend.src.config.settings import AreaConfig

    print(f"Preprocessing area '{area}' with network '{network}'...")
    config = AreaConfig(area)
    processor = OSMPreprocessor(area=area, network_type=network)
    output_path = config.edges_output_file

    if output_path.exists() and not overwrite:
        print(f"File already exists: {output_path}. Use --overwrite to regenerate.")
        return
    
    graph = processor.extract_edges()

    print(f"Network processed: {len(graph)} edges")

    graph.to_parquet(output_path)
    print(f"Saved to Parquet: {output_path}")


# ========================
# Edge enricher tasks
# ========================

@task
def enrich_edges(c, area="berlin", overwrite=False):
    """Run EdgeEnricher and export enriched edges to file"""
    from backend.src.core.edge_enricher import EdgeEnricher

    model = EdgeEnricher(area)
    model.load_data()
    model.get_enriched_edges(overwrite=overwrite)

    print(f"Edge enrichment complete. Saved to {model.config.enriched_output_file}")


@task
def generate_aq_data(c, area="berlin", overwrite=False):
    """
    Generate synthetic air quality data as a 500x500m grid over the road network area.
    """
    import geopandas as gpd
    import numpy as np
    from shapely.geometry import box
    from backend.src.config.settings import AreaConfig

    config = AreaConfig(area)
    output_path = config.aq_output_file

    if output_path.exists() and not overwrite:
        print(f"AQ file already exists: {output_path}. Use --overwrite to regenerate.")
        return

    print(f"Generating synthetic AQ data for '{area}'...")

    # Load road network and get bounding box
    road_gdf = gpd.read_parquet(config.edges_output_file)
    minx, miny, maxx, maxy = road_gdf.total_bounds

    # Create grid
    cell_size = 500
    x_coords = np.arange(minx, maxx, cell_size)
    y_coords = np.arange(miny, maxy, cell_size)

    polygons = []
    aq_values = []

    for x in x_coords:
        for y in y_coords:
            polygons.append(box(x, y, x + cell_size, y + cell_size))
            aq_values.append(np.random.randint(20, 100))

    aq_gdf = gpd.GeoDataFrame({
        "aq_value": aq_values,
        "geometry": polygons
    }, crs=config.crs)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    aq_gdf.to_file(output_path, driver="GeoJSON")

    print(f"AQ data saved to: {output_path}")


@task
def convert_parquet(c, input_path, output_path=None, overwrite=False):
    """Convert a Parquet file to GeoPackage format."""
    input_path = Path(input_path)
    output_path = Path(output_path) if output_path else input_path.with_suffix(".gpkg")

    if not input_path.exists():
        print(f"Input file not found: {input_path}")
        return

    if output_path.exists() and not overwrite:
        print(f"GeoPackage already exists: {output_path}. Use --overwrite to regenerate.")
        return

    print(f"Converting {input_path.name} → {output_path.name}...")
    gdf = gpd.read_parquet(input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(output_path, driver="GPKG")
    print(f"Saved to GeoPackage: {output_path}")

