# run_pipeline_compute.py

from src.core.compute_model import ComputeModel

def main():
    area = "berlin"
    model = ComputeModel(area=area)
    edges = model.get_data_for_algorithm()

    print(f"\nEdge count: {len(edges)}")
    print(f"Length stats:\n{edges['length_m'].describe()}")
    print("\n Sample row:")
    print(edges.iloc[0].to_dict())

    # === Edge data summary for algorithm developers ===
    # Format: GeoDataFrame with 6 columns
    # CRS: Projected (EPSG:25833 for Berlin)
    # Geometry: MultiLineString
    # Lengths: Computed in meters (column: length_m)
    # Tags: highway, bicycle, access
    # Sample row:
    # {
    #     'edge_id': 0,
    #     'geometry': <MULTILINESTRING (...)>,
    #     'length_m': 522.5,
    #     'highway': 'residential',
    #     'bicycle': None,
    #     'access': None
    # }

if __name__ == "__main__":
    main()