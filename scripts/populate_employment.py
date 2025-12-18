import pandas as pd
from owlready2 import *

onto = get_ontology("pkg2020_step4_affiliations_populated.owl").load()

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

    class jobTitle(DataProperty):
        domain = [Employment]
        range = [str]

    class startYear(DataProperty):
        domain = [Employment]
        range = [int]

    class endYear(DataProperty):
        domain = [Employment]
        range = [int]

    class orcid(DataProperty):
        domain = [onto.Author]
        range = [str]

# Load caches
Author = onto.Author
Employment = onto.Employment
Organization = onto.Organization

author_cache = {a.name: a for a in Author.instances()}
org_cache = {o.name: o for o in Organization.instances()}

df = pd.read_csv("data/OA05_Researcher_Employment.csv", nrows=10000)
print("CSV Columns:", df.columns.tolist())
print(f"Loaded {len(author_cache)} authors, {len(org_cache)} organizations")

with onto:
    for idx, row in df.iterrows():
        and_id = str(row["AND_ID"])
        author_iri = f"Author_{and_id}"
        
        if author_iri not in author_cache:
            continue

        author = author_cache[author_iri]
        
        # Create Employment individual
        emp = Employment(f"Employment_{row['id']}")
        
        # Add ORCID to author if available
        if "ORCID" in row and pd.notna(row["ORCID"]):
            author.orcid = [str(row["ORCID"])]
        
        # Link to organization
        org_name = str(row["Organization"]) if pd.notna(row["Organization"]) else "Unknown"
        org_iri = org_name.replace(" ", "_").replace(",", "")
        if org_iri not in org_cache:
            org_cache[org_iri] = Organization(org_iri)
        
        emp.employedAt.append(org_cache[org_iri])
        author.hasEmployment.append(emp)
        
        # Add years
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
onto.save(file="pkg2020_step5_employment_populated.owl", format="rdfxml")
print("Saved: pkg2020_step5_employment_populated.owl")
