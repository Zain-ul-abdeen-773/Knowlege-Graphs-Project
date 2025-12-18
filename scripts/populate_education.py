import pandas as pd
from owlready2 import *

onto = get_ontology("pkg2020_step5_employment_populated.owl").load()

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

    class role(DataProperty):
        domain = [Education]
        range = [str]

# Load caches
Author = onto.Author
Education = onto.Education
Institution = onto.Institution

author_cache = {a.name: a for a in Author.instances()}
institution_cache = {}

df = pd.read_csv("data/OA06_Researcher_Education.csv", nrows=10000)
print("CSV Columns:", df.columns.tolist())
print(f"Loaded {len(author_cache)} authors")

with onto:
    for idx, row in df.iterrows():
        and_id = str(row["AND_ID"])
        author_iri = f"Author_{and_id}"
        
        if author_iri not in author_cache:
            continue

        author = author_cache[author_iri]
        
        # Create Education individual
        edu = Education(f"Education_{row['id']}")
        
        # Link to institution
        inst_name = str(row["Institution"]) if "Institution" in row and pd.notna(row["Institution"]) else "Unknown"
        inst_iri = inst_name.replace(" ", "_").replace(",", "").replace("(", "").replace(")", "")
        if inst_iri not in institution_cache:
            institution_cache[inst_iri] = Institution(inst_iri)
        
        edu.educatedAt.append(institution_cache[inst_iri])
        author.hasEducation.append(edu)
        
        # Add degree
        if "Degree" in row and pd.notna(row["Degree"]):
            edu.degree = [str(row["Degree"])]
        
        # Add role
        if "Role" in row and pd.notna(row["Role"]):
            edu.role = [str(row["Role"])]
        
        # Add years
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
onto.save(file="pkg2020_step6_education_populated.owl", format="rdfxml")
print("Saved: pkg2020_step6_education_populated.owl")
