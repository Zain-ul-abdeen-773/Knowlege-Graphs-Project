"""
PKG2020 OWL to TTL Converter - Format Conversion for GraphDB Upload
PURPOSE: Converts the final OWL ontology (RDF/XML format) to Turtle (TTL) format for GraphDB upload.
HOW: Loads pkg2020_final.owl using OWLReady2, then saves as N-Triples format which GraphDB can import.
USAGE: Run after all populate scripts complete. Output file is pkg2020_final.ttl (~291MB).
NOTE: GraphDB Sandbox has file size limits; use sample TTL for smaller uploads if needed.
OUTPUT: Saves pkg2020_final.ttl in the owl/ directory ready for GraphDB import.
"""
from owlready2 import *
import os

# Get script directory for relative paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)

def convert_owl_to_ttl():
    """Convert OWL file to Turtle format for GraphDB"""
    
    owl_path = os.path.join(PROJECT_DIR, "owl", "pkg2020_final.owl")
    ttl_path = os.path.join(PROJECT_DIR, "owl", "pkg2020_final.ttl")
    
    print("=" * 60)
    print("OWL TO TTL CONVERTER")
    print("=" * 60)
    
    # Check if source file exists
    if not os.path.exists(owl_path):
        print(f"❌ ERROR: Source file not found: {owl_path}")
        return False
    
    print(f"\n📥 Loading: {owl_path}")
    print("   (This may take a while for large files...)")
    
    try:
        onto = get_ontology(owl_path).load()
        print(f"   ✅ Loaded successfully")
        
        # Get statistics
        classes = list(onto.classes())
        individuals = list(onto.individuals())
        print(f"\n📊 Statistics:")
        print(f"   Classes: {len(classes)}")
        print(f"   Individuals: {len(individuals):,}")
        
    except Exception as e:
        print(f"❌ ERROR loading ontology: {e}")
        return False
    
    print(f"\n📤 Converting to TTL format...")
    print(f"   Output: {ttl_path}")
    
    try:
        # Save as ntriples (compatible with GraphDB)
        onto.save(file=ttl_path, format="ntriples")
        
        # Get file size
        size_bytes = os.path.getsize(ttl_path)
        size_mb = size_bytes / (1024 * 1024)
        
        print(f"\n   ✅ Conversion complete!")
        print(f"   File size: {size_mb:.2f} MB")
        
    except Exception as e:
        print(f"❌ ERROR saving TTL: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("=" * 60)
    print("1. Go to GraphDB Sandbox: https://graphdb.ontotext.com/")
    print("2. Create a new repository or use existing")
    print("3. Import > Upload RDF files > Select pkg2020_final.ttl")
    print("4. Wait for import to complete")
    print("5. Test with SPARQL queries")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    convert_owl_to_ttl()
