# preprocessor/run_preprocessor.py

from osm_preprocessing import OSMPreprocessor

if __name__ == "__main__":
    pre = OSMPreprocessor(area="la", network_type="walking")
    pre.extract_edges()
