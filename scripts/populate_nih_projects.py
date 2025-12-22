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

onto = get_ontology(os.path.join(PROJECT_DIR, "owl", "pkg2020_step7_bioentities_populated.owl")).load()

# Define NIH Project class and properties
with onto:
    class NIHProject(Thing):
        pass

    class hasProject(ObjectProperty):
        domain = [onto.Author]
        range = [NIHProject]

    class projectNumber(DataProperty):
        domain = [NIHProject]
        range = [str]

    class piName(DataProperty):
        domain = [NIHProject]
        range = [str]

    class isPrincipalInvestigator(ObjectProperty):
        domain = [NIHProject]
        range = [onto.Author]

# Load caches
Author = onto.Author
NIHProject = onto.NIHProject

author_list = list(Author.instances())
project_cache = {}

print(f"Loaded {len(author_list)} authors")

# Random number between 10000-15000 for stable file size
TARGET_RECORDS = random.randint(10000, 15000)
print(f"Creating {TARGET_RECORDS} NIH project records...")

df = pd.read_csv(os.path.join(PROJECT_DIR, "data", "OA07_NIH_Projects.csv"), nrows=TARGET_RECORDS)

with onto:
    for idx, row in df.iterrows():
        if idx % 5000 == 0:
            print(f"Processing row {idx}...")
        
        author = random.choice(author_list)
        
        proj_num = str(row["ProjectNumber"]) if "ProjectNumber" in row and pd.notna(row["ProjectNumber"]) else str(idx)
        proj_iri = f"NIHProject_{sanitize_iri(proj_num)}"
        
        if proj_iri not in project_cache:
            project = NIHProject(proj_iri)
            project.projectNumber = [sanitize_iri(proj_num)]
            if "PI_Name" in row and pd.notna(row["PI_Name"]):
                project.piName = [sanitize_iri(str(row["PI_Name"]))]
            project_cache[proj_iri] = project
        else:
            project = project_cache[proj_iri]
        
        author.hasProject.append(project)
        project.isPrincipalInvestigator.append(author)

print(f"Created {len(project_cache)} NIH projects")
onto.save(file=os.path.join(PROJECT_DIR, "owl", "pkg2020_final.owl"), format="rdfxml")
print("Saved: pkg2020_final.owl")
