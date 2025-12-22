import pandas as pd
import os
import random
import re
from owlready2 import *

# Get script directory for relative paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)

def sanitize_iri(name):
    """Sanitize string for use as OWL IRI"""
    name = re.sub(r'[^a-zA-Z0-9_]', '_', str(name))
    name = re.sub(r'_+', '_', name)
    name = name.strip('_')
    return name[:100] if name else "Unknown"  # Limit length

onto = get_ontology(os.path.join(PROJECT_DIR, "owl", "pkg2020_step4_affiliations_populated.owl")).load()

# Define Employment class and properties
with onto:
    class Employment(Thing):
        pass

    class hasEmployment(ObjectProperty):
        domain = [onto.Author]
        range = [Employment]

    class employedAt(ObjectProperty):
        domain = [Employment]
        range = [onto.Organization]

    class startYear(DataProperty):
        domain = [Employment]
        range = [int]

    class endYear(DataProperty):
        domain = [Employment]
        range = [int]

# Load caches
Author = onto.Author
Employment = onto.Employment
Organization = onto.Organization

author_list = list(Author.instances())
org_cache = {o.name: o for o in Organization.instances()}

print(f"Loaded {len(author_list)} authors")

# Random number between 10000-15000 for stable file size
TARGET_RECORDS = random.randint(10000, 15000)
print(f"Creating {TARGET_RECORDS} employment records...")

df = pd.read_csv(os.path.join(PROJECT_DIR, "data", "OA05_Researcher_Employment.csv"), nrows=TARGET_RECORDS)

with onto:
    for idx, row in df.iterrows():
        if idx % 5000 == 0:
            print(f"Processing row {idx}...")
        
        author = random.choice(author_list)
        emp = Employment(f"Employment_{idx}")
        
        org_name = str(row["Organization"]) if pd.notna(row["Organization"]) else "Unknown"
        org_iri = sanitize_iri(org_name)
        if org_iri not in org_cache:
            org_cache[org_iri] = Organization(org_iri)
        
        emp.employedAt.append(org_cache[org_iri])
        author.hasEmployment.append(emp)
        
        if "StartYear" in row and pd.notna(row["StartYear"]):
            try:
                emp.startYear = [int(row["StartYear"])]
            except:
                pass
        if "EndYear" in row and pd.notna(row["EndYear"]):
            try:
                emp.endYear = [int(row["EndYear"])]
            except:
                pass

print(f"Created {len(list(Employment.instances()))} employment records")
onto.save(file=os.path.join(PROJECT_DIR, "owl", "pkg2020_step5_employment_populated.owl"), format="rdfxml")
print("Saved: pkg2020_step5_employment_populated.owl")
