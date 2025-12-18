from owlready2 import *

onto = get_ontology("pkg2020_core.owl").load()

# ===== BIND CLASSES & PROPERTIES FROM ONTOLOGY =====
Article = onto.Article
Author = onto.Author
Authorship = onto.Authorship
writtenBy = onto.writtenBy
careerStartYear = onto.careerStartYear
hasPMID = onto.hasPMID

with onto:

    # ===== INVERSE FUNCTIONAL PROPERTY =====
    hasPMID.is_a.append(InverseFunctionalProperty)

    # ===== CARDINALITY RESTRICTION =====
    Article.is_a.append(writtenBy.min(1, Author))

    # ===== INTERSECTION CLASS =====
    class ActiveAuthor(Author):
        equivalent_to = [
            Author & careerStartYear.some(int)
        ]

    # ===== UNION CLASS =====
    class ResearchEntity(Thing):
        equivalent_to = [
            Author | Article
        ]

    # ===== COMPLEMENT CLASS =====
    class AnonymousAuthor(Author):
        equivalent_to = [
            Author & Not(ActiveAuthor)
        ]

# Save updated ontology
onto.save(file="pkg2020_constrained.owl", format="rdfxml")
