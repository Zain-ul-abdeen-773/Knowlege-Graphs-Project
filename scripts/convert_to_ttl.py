"""
Script to convert the final OWL ontology to TTL format for GraphDB upload.
"""
from owlready2 import *
import os

# Get script directory for relative paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)

# Load the final ontology
print("Loading pkg2020_final.owl...")
onto = get_ontology(os.path.join(PROJECT_DIR, "owl", "pkg2020_final.owl")).load()

# Save as Turtle (TTL) format
ttl_path = os.path.join(PROJECT_DIR, "owl", "pkg2020_final.ttl")
print(f"Converting to TTL format...")
onto.save(file=ttl_path, format="ntriples")  # owlready2 supports ntriples which works with GraphDB

print(f"Saved: {ttl_path}")
print("\nYou can now upload this TTL file to GraphDB Sandbox!")
