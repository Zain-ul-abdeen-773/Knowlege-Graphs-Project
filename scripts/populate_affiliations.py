import pandas as pd
import re
import os
from owlready2 import *

# Get script directory for relative paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)

def sanitize_iri(name):
    """Sanitize string for use as OWL IRI"""
    name = re.sub(r'[^a-zA-Z0-9_]', '_', str(name))
    name = re.sub(r'_+', '_', name)
    name = name.strip('_')
    return name if name else "Unknown"

onto = get_ontology(os.path.join(PROJECT_DIR, "owl", "pkg2020_populated_authors.owl")).load()

# Define new classes and properties for affiliations
with onto:
    class Affiliation(Thing):
        pass

    class Organization(Thing):
        pass

    class hasAffiliation(ObjectProperty):
        domain = [onto.Author]
        range = [Affiliation]

    class affiliatedWith(ObjectProperty):
        domain = [Affiliation]
        range = [Organization]

    class city(DataProperty):
        domain = [Affiliation]
        range = [str]

    class state(DataProperty):
        domain = [Affiliation]
        range = [str]

    class country(DataProperty):
        domain = [Affiliation]
        range = [str]

# Load caches
Author = onto.Author
Affiliation = onto.Affiliation
Organization = onto.Organization

author_cache = {a.name: a for a in Author.instances()}
org_cache = {}

# Process all 50000 rows
df = pd.read_csv(os.path.join(PROJECT_DIR, "data", "OA04_Affiliations.csv"), nrows=50000)
print("CSV Columns:", df.columns.tolist())
print(f"Loaded {len(author_cache)} authors from ontology")

with onto:
    for idx, row in df.iterrows():
        if idx % 1000 == 0:
            print(f"Processing row {idx}...")
            
        and_id = str(row["AND_ID"])
        affil_id = str(row["id"])
        org_name = str(row["Affiliation"])

        author_iri = f"Author_{and_id}"
        if author_iri not in author_cache:
            continue

        author = author_cache[author_iri]

        aff = Affiliation(f"Affiliation_{affil_id}")
        
        # Add location data if available
        if "City" in row and pd.notna(row["City"]):
            aff.city = [str(row["City"])]
        if "State" in row and pd.notna(row["State"]):
            aff.state = [str(row["State"])]
        if "Country" in row and pd.notna(row["Country"]):
            aff.country = [str(row["Country"])]

        if org_name not in org_cache:
            org_cache[org_name] = Organization(sanitize_iri(org_name))

        author.hasAffiliation.append(aff)
        aff.affiliatedWith.append(org_cache[org_name])

print(f"Created {len(list(Affiliation.instances()))} affiliations")
onto.save(file=os.path.join(PROJECT_DIR, "owl", "pkg2020_step4_affiliations_populated.owl"), format="rdfxml")
print("Saved: pkg2020_step4_affiliations_populated.owl")
