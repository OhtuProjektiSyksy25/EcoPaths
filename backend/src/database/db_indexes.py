"""
Database index definitions for spatial tables.

Provides helper functions to create indexes for edges, grid, nodes, and green tables.
"""

from sqlalchemy import text


def create_edge_indexes(conn, area: str, network_type: str):
    """Create indexes for an edge table of a given area and network type."""
    conn.execute(text(f"""
        CREATE INDEX IF NOT EXISTS idx_edges_{area}_{network_type}_edge_id
        ON edges_{area}_{network_type} (edge_id);
    """))
    conn.execute(text(f"""
        CREATE INDEX IF NOT EXISTS idx_edges_{area}_{network_type}_tile_id
        ON edges_{area}_{network_type} (tile_id);
    """))
    conn.execute(text(f"""
        CREATE INDEX IF NOT EXISTS idx_edges_{area}_{network_type}_geometry
        ON edges_{area}_{network_type} USING GIST (geometry);
    """))
    conn.execute(text(f"""
        CREATE INDEX IF NOT EXISTS idx_edges_{area}_{network_type}_from_node
        ON edges_{area}_{network_type} (from_node);
    """))
    conn.execute(text(f"""
        CREATE INDEX IF NOT EXISTS idx_edges_{area}_{network_type}_to_node
        ON edges_{area}_{network_type} (to_node);
    """))


def create_grid_indexes(conn, area: str):
    """Create indexes for a grid table of a given area."""
    conn.execute(text(f"""
        CREATE INDEX IF NOT EXISTS idx_grid_{area}_tile_id
        ON grid_{area} (tile_id);
    """))
    conn.execute(text(f"""
        CREATE INDEX IF NOT EXISTS idx_grid_{area}_geometry
        ON grid_{area} USING GIST (geometry);
    """))


def create_node_indexes(conn, area: str, network_type: str):
    """Create indexes for a node table of a given area and network type."""
    conn.execute(text(f"""
        CREATE INDEX IF NOT EXISTS idx_nodes_{area}_{network_type}_node_id
        ON nodes_{area}_{network_type} (node_id);
    """))
    conn.execute(text(f"""
        CREATE INDEX IF NOT EXISTS idx_nodes_{area}_{network_type}_geometry
        ON nodes_{area}_{network_type} USING GIST (geometry);
    """))
    conn.execute(text(f"""
        CREATE INDEX IF NOT EXISTS idx_nodes_{area}_{network_type}_tile_id
        ON nodes_{area}_{network_type} (tile_id);
    """))


def create_green_indexes(conn, area: str):
    """Create indexes for a green landuse table of a given area."""
    conn.execute(text(f"""
        CREATE INDEX IF NOT EXISTS idx_green_{area}_geometry
        ON green_{area} USING GIST (geometry);
    """))
    conn.execute(text(f"""
        CREATE INDEX IF NOT EXISTS idx_green_{area}_tile_id
        ON green_{area} (tile_id);
    """))
