import pandas as pd
from owlready2 import *
import gc

# Load ontology
onto = get_ontology("pkg2020_constrained.owl").load()

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

# Reduced to 5000 rows for memory safety
NROWS = 5000

# Load CSV with specific columns only to save memory
df = pd.read_csv("data/OA01_Author_List.csv", 
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
            article.hasPMID = [pmid]
            article_cache.add(article_iri)
        else:
            article = onto[article_iri]

        # ----- Author (check cache to avoid duplicates) -----
        author_iri = f"Author_{and_id}"
        if author_iri not in author_cache:
            author = Author(author_iri)
            author.lastName = [str(row["LastName"])]
            author.foreName = [str(row["ForeName"])]
            author.initials = [str(row["Initials"])]
            author_cache.add(author_iri)
        else:
            author = onto[author_iri]

        # ----- Authorship (reified relation) -----
        auth = Authorship(f"Authorship_{pmid}_{and_id}")
        auth.authorOrder = [int(row["AuOrder"])]

        # ----- Link everything -----
        article.writtenBy.append(author)
        article.hasAuthorship.append(auth)
        auth.refersToAuthor.append(author)

# Free memory
del df
gc.collect()

print(f"Created {len(article_cache)} articles, {len(author_cache)} authors")

# Save populated ontology
onto.save(file="pkg2020_populated_authors.owl", format="rdfxml")
print("Saved: pkg2020_populated_authors.owl")
