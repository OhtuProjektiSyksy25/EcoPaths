from src.core.osm_preprocessing import OSMPreprocessor
from src.core.compute_model import ComputeModel

# Valitse alue, esim. 'la' tai 'berlin'
area = "berlin"

# 1. Esikäsittely
print("Preprocessing OSM data...")
preprocessor = OSMPreprocessor(area=area)
edges = preprocessor.preprocess()

print(f"Preprocessed {len(edges)} edges.")

# 2. Laskenta
print("Computing edge lengths...")
model = ComputeModel(area=area)
processed = model.compute_lengths(edges)

# 3. Tulostus
print(processed.head())
print(f"Computed lengths for {len(processed)} edges.")

