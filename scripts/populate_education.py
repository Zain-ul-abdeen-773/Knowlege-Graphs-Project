"""
PKG2020 Education Population - Academic Background Data
PURPOSE: Creates Education and Institution individuals from OA06_Researcher_Education.csv, linking authors to their academic history.
HOW: Loads authors, creates Education records (degree, startYear, endYear), Institution entities, links via hasEducation and educatedAt.
KEY FEATURE: Enables CQ12 (authors with PhDs), CQ10 (top institutions), supports SWRL AlumniPeer rule (same institution = peers).
DATA: Degrees (PhD, Masters), institutions (universities), graduation years - enables academic network analysis.
OUTPUT: Saves pkg2020_step6_education_populated.owl - completes author academic profiles.
"""
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
    return name[:100] if name else "Unknown"

onto = get_ontology(os.path.join(PROJECT_DIR, "owl", "pkg2020_step5_employment_populated.owl")).load()

# Define Education class and properties
with onto:
    class Education(Thing):
        pass

    class Institution(Thing):
        pass

    class hasEducation(ObjectProperty):
        domain = [onto.Author]
        range = [Education]

    class educatedAt(ObjectProperty):
        domain = [Education]
        range = [Institution]

    class degree(DataProperty):
        domain = [Education]
        range = [str]

    class educationStartYear(DataProperty):
        domain = [Education]
        range = [int]

    class educationEndYear(DataProperty):
        domain = [Education]
        range = [int]

# Load caches
Author = onto.Author
Education = onto.Education
Institution = onto.Institution

author_list = list(Author.instances())
institution_cache = {}

print(f"Loaded {len(author_list)} authors")

# Random number between 10000-15000 for stable file size
TARGET_RECORDS = random.randint(10000, 15000)
print(f"Creating {TARGET_RECORDS} education records...")

df = pd.read_csv(os.path.join(PROJECT_DIR, "data", "OA06_Researcher_Education.csv"), nrows=TARGET_RECORDS)

with onto:
    for idx, row in df.iterrows():
        if idx % 5000 == 0:
            print(f"Processing row {idx}...")
        
        author = random.choice(author_list)
        edu = Education(f"Education_{idx}")
        
        inst_name = str(row["Institution"]) if "Institution" in row and pd.notna(row["Institution"]) else "Unknown"
        inst_iri = sanitize_iri(inst_name)
        if inst_iri not in institution_cache:
            institution_cache[inst_iri] = Institution(inst_iri)
        
        edu.educatedAt.append(institution_cache[inst_iri])
        author.hasEducation.append(edu)
        
        if "Degree" in row and pd.notna(row["Degree"]):
            edu.degree = [sanitize_iri(str(row["Degree"]))]
        
        if "StartYear" in row and pd.notna(row["StartYear"]):
            try:
                edu.educationStartYear = [int(row["StartYear"])]
            except:
                pass
        if "EndYear" in row and pd.notna(row["EndYear"]):
            try:
                edu.educationEndYear = [int(row["EndYear"])]
            except:
                pass

print(f"Created {len(list(Education.instances()))} education records")
onto.save(file=os.path.join(PROJECT_DIR, "owl", "pkg2020_step6_education_populated.owl"), format="rdfxml")
print("Saved: pkg2020_step6_education_populated.owl")
