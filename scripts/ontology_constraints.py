from owlready2 import *

onto = get_ontology("../owl/pkg2020_core.owl").load()

# ===== BIND CLASSES & PROPERTIES FROM ONTOLOGY =====
Article = onto.Article
Author = onto.Author
Authorship = onto.Authorship
writtenBy = onto.writtenBy
careerStartYear = onto.careerStartYear
hasPMID = onto.hasPMID
hasStatus = onto.hasStatus
PublicationStatus = onto.PublicationStatus

with onto:

    # ===== INVERSE FUNCTIONAL PROPERTY =====
    # PMID uniquely identifies an article (inverse functional)
    hasPMID.is_a.append(InverseFunctionalProperty)

    # ===== CARDINALITY RESTRICTIONS =====
    # Every Article must have at least 1 author
    Article.is_a.append(writtenBy.min(1, Author))
    
    # Every Article must have exactly 1 PMID (cardinality = 1)
    Article.is_a.append(hasPMID.exactly(1, str))
    
    # Every Article may have at most 1 status
    Article.is_a.append(hasStatus.max(1, PublicationStatus))

    # ===== INTERSECTION CLASS (Defined Class) =====
    class ActiveAuthor(Author):
        """Author with known career start year = Author ⊓ ∃careerStartYear.int"""
        equivalent_to = [
            Author & careerStartYear.some(int)
        ]

    # ===== UNION CLASS =====
    class ResearchEntity(Thing):
        """Any research-related entity = Author ⊔ Article"""
        equivalent_to = [
            Author | Article
        ]

    # ===== COMPLEMENT CLASS =====
    class AnonymousAuthor(Author):
        """Author without known career info = Author ⊓ ¬ActiveAuthor"""
        equivalent_to = [
            Author & Not(ActiveAuthor)
        ]

    # ===== ADDITIONAL DEFINED CLASSES FOR REASONING =====
    class ProlificAuthor(Author):
        """Author who has written at least 5 articles"""
        equivalent_to = [
            Author & writtenBy.min(5, Article)
        ]

    class SingleAuthorArticle(Article):
        """Article with exactly one author"""
        equivalent_to = [
            Article & writtenBy.exactly(1, Author)
        ]

    class MultiAuthorArticle(Article):
        """Article with more than one author"""
        equivalent_to = [
            Article & writtenBy.min(2, Author)
        ]

# Save updated ontology
onto.save(file="../owl/pkg2020_constrained.owl", format="rdfxml")
print("Saved: pkg2020_constrained.owl with enhanced constraints and defined classes")
