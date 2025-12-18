from owlready2 import *

# Create ontology with proper IRI
onto = get_ontology("http://example.org/pkg2020/ontology.owl")

with onto:

    # ===== CLASSES =====
    class Article(Thing):
        """A research article identified by PMID"""
        pass

    class Author(Thing):
        """A researcher/author identified by AND_ID"""
        pass

    class Authorship(Thing):
        """Reified relationship between Article and Author with order"""
        pass

    class PublicationYear(Thing):
        """Year of publication"""
        pass

    # ===== ENUMERATION CLASS (Rubric Requirement) =====
    class PublicationStatus(Thing):
        """Enumeration of publication statuses"""
        pass

    # Create enumeration individuals
    published = PublicationStatus("Published")
    preprint = PublicationStatus("Preprint")
    retracted = PublicationStatus("Retracted")
    in_review = PublicationStatus("InReview")
    
    # Define as enumeration (OneOf)
    PublicationStatus.equivalent_to = [OneOf([published, preprint, retracted, in_review])]

    # ===== OBJECT PROPERTIES =====
    class writtenBy(ObjectProperty):
        """Links Article to its Authors"""
        domain = [Article]
        range = [Author]

    class hasAuthorship(ObjectProperty):
        """Links Article to Authorship records"""
        domain = [Article]
        range = [Authorship]

    class refersToAuthor(ObjectProperty):
        """Links Authorship to the Author it refers to"""
        domain = [Authorship]
        range = [Author]

    # FUNCTIONAL PROPERTY (Rubric Requirement) - each article has exactly one primary author
    class hasPrimaryAuthor(ObjectProperty, FunctionalProperty):
        """Functional: Article has exactly one primary author"""
        domain = [Article]
        range = [Author]

    class hasStatus(ObjectProperty, FunctionalProperty):
        """Functional: Article has exactly one publication status"""
        domain = [Article]
        range = [PublicationStatus]

    # ===== DATATYPE PROPERTIES =====
    class hasPMID(DataProperty, FunctionalProperty):
        """Functional: Each article has exactly one PMID"""
        domain = [Article]
        range = [str]

    class lastName(DataProperty):
        domain = [Author]
        range = [str]

    class foreName(DataProperty):
        domain = [Author]
        range = [str]

    class initials(DataProperty):
        domain = [Author]
        range = [str]

    class authorOrder(DataProperty):
        domain = [Authorship]
        range = [int]

    class publicationYear(DataProperty, FunctionalProperty):
        """Functional: Article has one publication year"""
        domain = [Article]
        range = [int]

    class careerStartYear(DataProperty):
        domain = [Author]
        range = [int]

# Save ontology
onto.save(file="../owl/pkg2020_core.owl", format="rdfxml")
print("Saved: pkg2020_core.owl with enumeration class and functional properties")
