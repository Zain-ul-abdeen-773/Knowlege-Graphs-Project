import pandas as pd
from owlready2 import *
import gc
import os

# Get script directory for relative paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)

# Load ontology
onto = get_ontology(os.path.join(PROJECT_DIR, "owl", "pkg2020_constrained.owl")).load()

Article = onto.Article
Author = onto.Author
Authorship = onto.Authorship
writtenBy = onto.writtenBy
hasAuthorship = onto.hasAuthorship
refersToAuthor = onto.refersToAuthor
hasPMID = onto.hasPMID
lastName = onto.lastName
foreName = onto.foreName
initials = onto.initials
authorOrder = onto.authorOrder

# Process all 50000 rows
NROWS = 50000

# Load CSV with specific columns only to save memory
df = pd.read_csv(os.path.join(PROJECT_DIR, "data", "OA01_Author_List.csv"), 
                 nrows=NROWS,
                 usecols=["PMID", "AND_ID", "LastName", "ForeName", "Initials", "AuOrder"])
print(f"Loaded {len(df)} rows from CSV")

# Caching to prevent duplicate creation
author_cache = set()
article_cache = set()

with onto:
    for idx, row in df.iterrows():
        if idx % 1000 == 0:
            print(f"Processing row {idx}...")

        pmid = str(row["PMID"])
        and_id = str(row["AND_ID"])

        # ----- Article (check cache to avoid duplicates) -----
        article_iri = f"Article_{pmid}"
        if article_iri not in article_cache:
            article = Article(article_iri)
            article.hasPMID = pmid  # FunctionalProperty - single value
            article_cache.add(article_iri)
        else:
            article = onto[article_iri]

        # ----- Author (check cache to avoid duplicates) -----
        author_iri = f"Author_{and_id}"
        if author_iri not in author_cache:
            author = Author(author_iri)
            if pd.notna(row["LastName"]):
                author.lastName = [str(row["LastName"])]
            if pd.notna(row["ForeName"]):
                author.foreName = [str(row["ForeName"])]
            if pd.notna(row["Initials"]):
                author.initials = [str(row["Initials"])]
            author_cache.add(author_iri)
        else:
            author = onto[author_iri]

        # ----- Authorship (reified relation) -----
        auth = Authorship(f"Authorship_{pmid}_{and_id}")
        if pd.notna(row["AuOrder"]):
            auth.authorOrder = [int(row["AuOrder"])]  # Non-functional - needs list

        # ----- Link everything -----
        article.writtenBy.append(author)
        article.hasAuthorship.append(auth)
        auth.refersToAuthor.append(author)

# Free memory
del df
gc.collect()

print(f"Created {len(article_cache)} articles, {len(author_cache)} authors")

# Save populated ontology
onto.save(file=os.path.join(PROJECT_DIR, "owl", "pkg2020_populated_authors.owl"), format="rdfxml")
print("Saved: pkg2020_populated_authors.owl")
