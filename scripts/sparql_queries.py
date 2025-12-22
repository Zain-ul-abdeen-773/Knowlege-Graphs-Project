"""
SPARQL Queries for PKG2020 KRR Ontology
15 Competency questions answered via SPARQL
"""

# Note: To run these queries, load the OWL file into a SPARQL endpoint like:
# - GraphDB
# - Apache Jena Fuseki
# - Or use rdflib in Python

SPARQL_QUERIES = {
    # ===== AUTHOR QUERIES =====
    "1_authors_multiple_institutions": """
        # CQ1: Which authors worked in multiple institutions?
        PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
        
        SELECT ?author ?lastName (COUNT(DISTINCT ?org) AS ?orgCount)
        WHERE {
            ?author a pkg:Author .
            ?author pkg:lastName ?lastName .
            ?author pkg:hasAffiliation ?aff .
            ?aff pkg:affiliatedWith ?org .
        }
        GROUP BY ?author ?lastName
        HAVING (COUNT(DISTINCT ?org) > 1)
        ORDER BY DESC(?orgCount)
        LIMIT 100
    """,
    
    "2_prolific_authors": """
        # CQ2: Who are the most prolific authors (by article count)?
        PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
        
        SELECT ?author ?lastName ?foreName (COUNT(?article) AS ?articleCount)
        WHERE {
            ?author a pkg:Author .
            ?author pkg:lastName ?lastName .
            OPTIONAL { ?author pkg:foreName ?foreName }
            ?article pkg:writtenBy ?author .
        }
        GROUP BY ?author ?lastName ?foreName
        ORDER BY DESC(?articleCount)
        LIMIT 50
    """,
    
    "3_author_collaborations": """
        # CQ3: Which authors frequently collaborate together?
        PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
        
        SELECT ?author1 ?author2 (COUNT(?article) AS ?collaborations)
        WHERE {
            ?article a pkg:Article .
            ?article pkg:writtenBy ?author1 .
            ?article pkg:writtenBy ?author2 .
            FILTER (STR(?author1) < STR(?author2))
        }
        GROUP BY ?author1 ?author2
        HAVING (COUNT(?article) > 1)
        ORDER BY DESC(?collaborations)
        LIMIT 100
    """,
    
    # ===== ARTICLE & BIOENTITY QUERIES =====
    "4_articles_with_genes": """
        # CQ4: Which articles mention genes?
        PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
        
        SELECT ?article ?pmid ?entityName
        WHERE {
            ?article a pkg:Article .
            ?article pkg:hasPMID ?pmid .
            ?article pkg:mentionsBioEntity ?entity .
            ?entity a pkg:Gene .
            ?entity pkg:entityName ?entityName .
        }
        LIMIT 100
    """,
    
    "5_articles_with_diseases": """
        # CQ5: Which articles discuss diseases?
        PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
        
        SELECT ?article ?pmid ?diseaseName
        WHERE {
            ?article a pkg:Article .
            ?article pkg:hasPMID ?pmid .
            ?article pkg:mentionsBioEntity ?entity .
            ?entity a pkg:Disease .
            ?entity pkg:entityName ?diseaseName .
        }
        LIMIT 100
    """,
    
    "6_mutation_disease_correlation": """
        # CQ6: Which articles mention both mutations and diseases (potential research correlations)?
        PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
        
        SELECT ?article ?pmid ?mutation ?disease
        WHERE {
            ?article a pkg:Article .
            ?article pkg:hasPMID ?pmid .
            ?article pkg:mentionsBioEntity ?m .
            ?m a pkg:Mutation .
            ?m pkg:entityName ?mutation .
            ?article pkg:mentionsBioEntity ?d .
            ?d a pkg:Disease .
            ?d pkg:entityName ?disease .
        }
        LIMIT 100
    """,
    
    "7_bioentity_distribution": """
        # CQ7: What is the distribution of bio-entity types in the corpus?
        PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
        
        SELECT ?entityType (COUNT(?entity) AS ?count)
        WHERE {
            ?entity a pkg:BioEntity .
            ?entity pkg:entityType ?entityType .
        }
        GROUP BY ?entityType
        ORDER BY DESC(?count)
    """,
    
    # ===== ORGANIZATION & AFFILIATION QUERIES =====
    "8_top_organizations": """
        # CQ8: Which organizations have the most affiliated authors?
        PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
        
        SELECT ?org (COUNT(DISTINCT ?author) AS ?authorCount)
        WHERE {
            ?author a pkg:Author .
            ?author pkg:hasAffiliation ?aff .
            ?aff pkg:affiliatedWith ?org .
        }
        GROUP BY ?org
        ORDER BY DESC(?authorCount)
        LIMIT 50
    """,
    
    "9_affiliation_by_country": """
        # CQ9: How are author affiliations distributed by country?
        PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
        
        SELECT ?country (COUNT(?aff) AS ?affiliationCount)
        WHERE {
            ?aff a pkg:Affiliation .
            ?aff pkg:country ?country .
        }
        GROUP BY ?country
        ORDER BY DESC(?affiliationCount)
        LIMIT 30
    """,

    # ===== EMPLOYMENT & EDUCATION QUERIES =====
    "10_education_by_institution": """
        # CQ10: Which institutions produced the most researchers?
        PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
        
        SELECT ?institution (COUNT(DISTINCT ?author) AS ?authorCount)
        WHERE {
            ?author a pkg:Author .
            ?author pkg:hasEducation ?edu .
            ?edu pkg:educatedAt ?institution .
        }
        GROUP BY ?institution
        ORDER BY DESC(?authorCount)
        LIMIT 50
    """,
    
    "11_employment_timeline": """
        # CQ11: What is the career timeline of authors (employment history)?
        PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
        
        SELECT ?author ?lastName ?org ?startYear ?endYear
        WHERE {
            ?author a pkg:Author .
            ?author pkg:lastName ?lastName .
            ?author pkg:hasEmployment ?emp .
            ?emp pkg:employedAt ?org .
            OPTIONAL { ?emp pkg:startYear ?startYear }
            OPTIONAL { ?emp pkg:endYear ?endYear }
        }
        ORDER BY ?author ?startYear
        LIMIT 100
    """,
    
    "12_authors_with_phd": """
        # CQ12: Which authors have doctoral degrees?
        PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
        
        SELECT ?author ?lastName ?degree ?institution
        WHERE {
            ?author a pkg:Author .
            ?author pkg:lastName ?lastName .
            ?author pkg:hasEducation ?edu .
            ?edu pkg:degree ?degree .
            ?edu pkg:educatedAt ?institution .
            FILTER (CONTAINS(LCASE(?degree), "phd") || CONTAINS(LCASE(?degree), "doctor"))
        }
        LIMIT 100
    """,

    # ===== NIH PROJECT QUERIES =====
    "13_authors_with_nih_funding": """
        # CQ13: Which authors have NIH project funding?
        PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
        
        SELECT ?author ?lastName ?projectNumber ?piName
        WHERE {
            ?author a pkg:Author .
            ?author pkg:lastName ?lastName .
            ?author pkg:hasProject ?project .
            ?project pkg:projectNumber ?projectNumber .
            OPTIONAL { ?project pkg:piName ?piName }
        }
        LIMIT 100
    """,
    
    "14_principal_investigators": """
        # CQ14: Who are the principal investigators and how many projects do they lead?
        PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
        
        SELECT ?piName (COUNT(DISTINCT ?project) AS ?projectCount)
        WHERE {
            ?project a pkg:NIHProject .
            ?project pkg:piName ?piName .
        }
        GROUP BY ?piName
        ORDER BY DESC(?projectCount)
        LIMIT 50
    """,

    # ===== COMPLEX ANALYTICAL QUERIES =====
    "15_author_complete_profile": """
        # CQ15: Get complete profile of an author (all relationships)
        PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
        
        SELECT ?author ?lastName ?foreName ?org ?institution ?project ?article
        WHERE {
            ?author a pkg:Author .
            ?author pkg:lastName ?lastName .
            OPTIONAL { ?author pkg:foreName ?foreName }
            OPTIONAL {
                ?author pkg:hasAffiliation ?aff .
                ?aff pkg:affiliatedWith ?org .
            }
            OPTIONAL {
                ?author pkg:hasEducation ?edu .
                ?edu pkg:educatedAt ?institution .
            }
            OPTIONAL {
                ?author pkg:hasProject ?project .
            }
            OPTIONAL {
                ?article pkg:writtenBy ?author .
            }
        }
        LIMIT 50
    """
}

# Print queries
if __name__ == "__main__":
    print("="*60)
    print("PKG2020 SPARQL COMPETENCY QUERIES (15 Questions)")
    print("="*60)
    
    for name, query in SPARQL_QUERIES.items():
        print(f"\n📌 {name.upper()}")
        print("-"*50)
        print(query.strip())
        print()
