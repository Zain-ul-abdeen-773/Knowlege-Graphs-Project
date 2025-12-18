"""
Validation script for PKG2020 KRR Ontology
Validates the final populated ontology and prints statistics
"""
from owlready2 import *

# Load the final ontology
print("Loading ontology...")
onto = get_ontology("pkg2020_final.owl").load()

print("\n" + "="*60)
print("PKG2020 ONTOLOGY VALIDATION REPORT")
print("="*60)

# Count individuals per class
print("\n📊 INDIVIDUAL COUNTS BY CLASS:")
print("-"*40)

classes_to_check = [
    "Article", "Author", "Authorship",
    "Affiliation", "Organization",
    "Employment", "Education", "Institution",
    "BioEntity", "Gene", "Chemical", "Disease", "Species", "Mutation",
    "NIHProject"
]

for class_name in classes_to_check:
    cls = getattr(onto, class_name, None)
    if cls:
        count = len(list(cls.instances()))
        print(f"  {class_name}: {count:,}")
    else:
        print(f"  {class_name}: (not defined)")

# Count properties
print("\n📊 PROPERTY COUNTS:")
print("-"*40)
print(f"  Object Properties: {len(list(onto.object_properties()))}")
print(f"  Data Properties: {len(list(onto.data_properties()))}")

# List all classes
print("\n📋 ALL CLASSES:")
print("-"*40)
for cls in onto.classes():
    print(f"  - {cls.name}")

# List object properties
print("\n📋 OBJECT PROPERTIES:")
print("-"*40)
for prop in onto.object_properties():
    print(f"  - {prop.name}")

# List data properties
print("\n📋 DATA PROPERTIES:")
print("-"*40)
for prop in onto.data_properties():
    print(f"  - {prop.name}")

# Optional: Run reasoner
print("\n🧠 RUNNING REASONER (Pellet)...")
print("-"*40)
try:
    with onto:
        sync_reasoner_pellet(infer_property_values=True, infer_data_property_values=True)
    print("  ✅ Reasoner completed successfully - ontology is consistent")
except Exception as e:
    print(f"  ⚠️ Reasoner error: {e}")

print("\n" + "="*60)
print("VALIDATION COMPLETE")
print("="*60)
