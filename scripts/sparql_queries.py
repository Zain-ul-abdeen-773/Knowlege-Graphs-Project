"""
SPARQL Queries for PKG2020 KRR Ontology
Competency questions answered via SPARQL
"""

# Note: To run these queries, load the OWL file into a SPARQL endpoint like:
# - GraphDB
# - Apache Jena Fuseki
# - Or use rdflib in Python

SPARQL_QUERIES = {
    "1_authors_multiple_institutions": """
        # Which authors worked in multiple institutions?
        PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
        
        SELECT ?author (COUNT(DISTINCT ?org) AS ?orgCount)
        WHERE {
            ?author a pkg:Author .
            ?author pkg:hasAffiliation ?aff .
            ?aff pkg:affiliatedWith ?org .
        }
        GROUP BY ?author
        HAVING (COUNT(DISTINCT ?org) > 1)
        ORDER BY DESC(?orgCount)
        LIMIT 100
    """,
    
    "2_articles_with_bioentity": """
        # Which articles mention a specific bio-entity (e.g., Gene)?
        PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
        
        SELECT ?article ?entityName ?entityType
        WHERE {
            ?article a pkg:Article .
            ?article pkg:mentionsBioEntity ?entity .
            ?entity pkg:entityName ?entityName .
            ?entity pkg:entityType ?entityType .
            FILTER (?entityType = "Gene")
        }
        LIMIT 100
    """,
    
    "3_author_collaborations": """
        # Which authors collaborated on articles?
        PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
        
        SELECT ?author1 ?author2 (COUNT(?article) AS ?collaborations)
        WHERE {
            ?article a pkg:Article .
            ?article pkg:writtenBy ?author1 .
            ?article pkg:writtenBy ?author2 .
            FILTER (?author1 != ?author2)
        }
        GROUP BY ?author1 ?author2
        HAVING (COUNT(?article) > 1)
        ORDER BY DESC(?collaborations)
        LIMIT 100
    """,
    
    "4_authors_with_nih_funding": """
        # Which authors have NIH project funding?
        PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
        
        SELECT ?author ?projectNumber ?piName
        WHERE {
            ?author a pkg:Author .
            ?author pkg:hasProject ?project .
            ?project pkg:projectNumber ?projectNumber .
            OPTIONAL { ?project pkg:piName ?piName }
        }
        LIMIT 100
    """,
    
    "5_education_by_institution": """
        # Authors educated at specific institutions
        PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
        
        SELECT ?institution (COUNT(?author) AS ?authorCount)
        WHERE {
            ?author a pkg:Author .
            ?author pkg:hasEducation ?edu .
            ?edu pkg:educatedAt ?institution .
        }
        GROUP BY ?institution
        ORDER BY DESC(?authorCount)
        LIMIT 50
    """,
    
    "6_employment_timeline": """
        # Author employment history with years
        PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
        
        SELECT ?author ?org ?startYear ?endYear
        WHERE {
            ?author a pkg:Author .
            ?author pkg:hasEmployment ?emp .
            ?emp pkg:employedAt ?org .
            OPTIONAL { ?emp pkg:startYear ?startYear }
            OPTIONAL { ?emp pkg:endYear ?endYear }
        }
        ORDER BY ?author ?startYear
        LIMIT 100
    """,
    
    "7_mutation_disease_articles": """
        # Articles mentioning both mutations and diseases
        PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
        
        SELECT ?article ?mutation ?disease
        WHERE {
            ?article a pkg:Article .
            ?article pkg:mentionsBioEntity ?mutation .
            ?mutation a pkg:Mutation .
            ?article pkg:mentionsBioEntity ?disease .
            ?disease a pkg:Disease .
        }
        LIMIT 100
    """
}

# Print queries
if __name__ == "__main__":
    print("="*60)
    print("PKG2020 SPARQL COMPETENCY QUERIES")
    print("="*60)
    
    for name, query in SPARQL_QUERIES.items():
        print(f"\n📌 {name.upper()}")
        print("-"*50)
        print(query.strip())
        print()
