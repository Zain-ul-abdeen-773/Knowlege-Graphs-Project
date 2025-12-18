from owlready2 import *

# Create ontology
onto = get_ontology("http://example.org/pkg2020/ontology.owl")

with onto:

    # ===== CLASSES =====
    class Article(Thing):
        pass

    class Author(Thing):
        pass

    class Authorship(Thing):
        pass

    class PublicationYear(Thing):
        pass

    # ===== OBJECT PROPERTIES =====
    class writtenBy(ObjectProperty):
        domain = [Article]
        range = [Author]

    class hasAuthorship(ObjectProperty):
        domain = [Article]
        range = [Authorship]

    class refersToAuthor(ObjectProperty):
        domain = [Authorship]
        range = [Author]

    # ===== DATATYPE PROPERTIES =====
    class hasPMID(DataProperty):
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

    class publicationYear(DataProperty):
        domain = [PublicationYear]
        range = [int]

    class careerStartYear(DataProperty):
        domain = [Author]
        range = [int]

# Save ontology
onto.save(file="pkg2020_core.owl", format="rdfxml")
