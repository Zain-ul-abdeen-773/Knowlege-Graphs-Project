import pandas as pd
from owlready2 import *

onto = get_ontology("pkg2020_step7_bioentities_populated.owl").load()

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

author_cache = {a.name: a for a in Author.instances()}
project_cache = {}

df = pd.read_csv("data/OA07_NIH_Projects.csv", nrows=10000)
print("CSV Columns:", df.columns.tolist())
print(f"Loaded {len(author_cache)} authors")

with onto:
    for idx, row in df.iterrows():
        and_id = str(row["AND_ID"])
        author_iri = f"Author_{and_id}"
        
        if author_iri not in author_cache:
            continue

        author = author_cache[author_iri]
        
        # Create NIHProject individual
        proj_num = str(row["ProjectNumber"]) if "ProjectNumber" in row and pd.notna(row["ProjectNumber"]) else str(row["id"])
        proj_iri = f"NIHProject_{proj_num}".replace(" ", "_").replace("-", "_")
        
        if proj_iri not in project_cache:
            project = NIHProject(proj_iri)
            project.projectNumber = [proj_num]
            if "PI_Name" in row and pd.notna(row["PI_Name"]):
                project.piName = [str(row["PI_Name"])]
            project_cache[proj_iri] = project
        else:
            project = project_cache[proj_iri]
        
        author.hasProject.append(project)
        project.isPrincipalInvestigator.append(author)

print(f"Created {len(list(NIHProject.instances()))} NIH projects")
onto.save(file="pkg2020_final.owl", format="rdfxml")
print("Saved: pkg2020_final.owl")
