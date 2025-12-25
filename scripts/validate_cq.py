"""
PKG2020 Competency Question Validation - Live Query Testing
PURPOSE: Executes all 15 competency queries against live GraphDB endpoint and reports pass/fail status with sample results.
HOW: Uses SPARQLWrapper with HTTP Basic Auth to connect to GraphDB Sandbox, runs each query, counts results, displays summary.
AUTHENTICATION: Uses GRAPHDB_ENDPOINT, GRAPHDB_USERNAME, GRAPHDB_PASSWORD for authenticated SPARQL access.
OUTPUT: For each CQ: ✅ PASSED (N results) with sample, ⚠️ NO RESULTS, or ❌ QUERY ERROR. Final summary shows pass/fail counts.
USAGE: Run standalone to validate all queries work correctly before demo/viva presentation.
"""
from SPARQLWrapper import SPARQLWrapper, JSON
import sys

# GraphDB Endpoint Configuration
GRAPHDB_ENDPOINT = "https://x1327f4041a654297998.sandbox.graphwise.ai/repositories/KRR-Project"
GRAPHDB_USERNAME = "zainulabdeenfaisal69@gmail.com"
GRAPHDB_PASSWORD = "Eu^bm^8mKM"

# All 15 Competency Question Queries
COMPETENCY_QUERIES = {
    "CQ1": {
        "question": "Which authors have worked in multiple institutions?",
        "query": """
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
LIMIT 20
"""
    },
    "CQ2": {
        "question": "Who are the most prolific authors by article count?",
        "query": """
PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>

SELECT ?author ?lastName (COUNT(?article) AS ?articleCount)
WHERE {
    ?author a pkg:Author .
    OPTIONAL { ?author pkg:lastName ?lastName }
    ?article pkg:writtenBy ?author .
}
GROUP BY ?author ?lastName
ORDER BY DESC(?articleCount)
LIMIT 20
"""
    },
    "CQ3": {
        "question": "Which authors frequently collaborate together?",
        "query": """
PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>

SELECT ?author1 ?author2 (COUNT(?article) AS ?collaborations)
WHERE {
    ?article a pkg:Article .
    ?article pkg:writtenBy ?author1 .
    ?article pkg:writtenBy ?author2 .
    FILTER (STR(?author1) < STR(?author2))
}
GROUP BY ?author1 ?author2
ORDER BY DESC(?collaborations)
LIMIT 20
"""
    },
    "CQ4": {
        "question": "Which articles mention specific genes?",
        "query": """
PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>

SELECT ?article ?pmid ?entityName
WHERE {
    ?article a pkg:Article .
    ?article pkg:hasPMID ?pmid .
    ?article pkg:mentionsBioEntity ?entity .
    ?entity a pkg:Gene .
    OPTIONAL { ?entity pkg:entityName ?entityName }
}
LIMIT 20
"""
    },
    "CQ5": {
        "question": "Which articles mention species?",
        "query": """
PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>

SELECT ?article ?pmid ?speciesName
WHERE {
    ?article a pkg:Article .
    ?article pkg:hasPMID ?pmid .
    ?article pkg:mentionsBioEntity ?entity .
    ?entity a pkg:Species .
    OPTIONAL { ?entity pkg:entityName ?speciesName }
}
LIMIT 20
"""
    },
    "CQ6": {
        "question": "Which articles mention both genes and mutations?",
        "query": """
PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>

SELECT ?article ?pmid ?geneName ?mutationName
WHERE {
    ?article a pkg:Article .
    ?article pkg:hasPMID ?pmid .
    ?article pkg:mentionsBioEntity ?g .
    ?g a pkg:Gene .
    OPTIONAL { ?g pkg:entityName ?geneName }
    ?article pkg:mentionsBioEntity ?m .
    ?m a pkg:Mutation .
    OPTIONAL { ?m pkg:entityName ?mutationName }
}
LIMIT 20
"""
    },
    "CQ7": {
        "question": "What is the distribution of bio-entity types?",
        "query": """
PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?type (COUNT(?entity) AS ?count)
WHERE {
    ?entity rdf:type ?type .
    FILTER(STRSTARTS(STR(?type), "http://example.org/pkg2020/"))
}
GROUP BY ?type
ORDER BY DESC(?count)
LIMIT 30
"""
    },
    "CQ8": {
        "question": "Which organizations have the most affiliated authors?",
        "query": """
PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>

SELECT ?org (COUNT(DISTINCT ?author) AS ?authorCount)
WHERE {
    ?author a pkg:Author .
    ?author pkg:hasAffiliation ?aff .
    ?aff pkg:affiliatedWith ?org .
}
GROUP BY ?org
ORDER BY DESC(?authorCount)
LIMIT 20
"""
    },
    "CQ9": {
        "question": "How are author affiliations distributed by country?",
        "query": """
PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>

SELECT ?country (COUNT(?aff) AS ?affiliationCount)
WHERE {
    ?aff a pkg:Affiliation .
    ?aff pkg:country ?country .
}
GROUP BY ?country
ORDER BY DESC(?affiliationCount)
LIMIT 20
"""
    },
    "CQ10": {
        "question": "Which institutions produced the most researchers?",
        "query": """
PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>

SELECT ?institution (COUNT(DISTINCT ?author) AS ?authorCount)
WHERE {
    ?author a pkg:Author .
    ?author pkg:hasEducation ?edu .
    ?edu pkg:educatedAt ?institution .
}
GROUP BY ?institution
ORDER BY DESC(?authorCount)
LIMIT 20
"""
    },
    "CQ11": {
        "question": "What is the career timeline of researchers?",
        "query": """
PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>

SELECT ?author ?lastName ?org ?startYear ?endYear
WHERE {
    ?author a pkg:Author .
    OPTIONAL { ?author pkg:lastName ?lastName }
    ?author pkg:hasEmployment ?emp .
    ?emp pkg:employedAt ?org .
    OPTIONAL { ?emp pkg:startYear ?startYear }
    OPTIONAL { ?emp pkg:endYear ?endYear }
}
LIMIT 20
"""
    },
    "CQ12": {
        "question": "Which authors have education records?",
        "query": """
PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>

SELECT ?author ?lastName ?institution
WHERE {
    ?author a pkg:Author .
    OPTIONAL { ?author pkg:lastName ?lastName }
    ?author pkg:hasEducation ?edu .
    ?edu pkg:educatedAt ?institution .
}
LIMIT 20
"""
    },
    "CQ13": {
        "question": "Which authors have NIH project funding?",
        "query": """
PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>

SELECT ?author ?lastName ?projectNumber ?piName
WHERE {
    ?author a pkg:Author .
    OPTIONAL { ?author pkg:lastName ?lastName }
    ?author pkg:hasProject ?project .
    OPTIONAL { ?project pkg:projectNumber ?projectNumber }
    OPTIONAL { ?project pkg:piName ?piName }
}
LIMIT 20
"""
    },
    "CQ14": {
        "question": "Who are the principal investigators?",
        "query": """
PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>

SELECT ?project ?piName ?projectNumber
WHERE {
    ?project a pkg:NIHProject .
    OPTIONAL { ?project pkg:piName ?piName }
    OPTIONAL { ?project pkg:projectNumber ?projectNumber }
}
LIMIT 20
"""
    },
    "CQ15": {
        "question": "Get complete author profile with all relationships?",
        "query": """
PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>

SELECT ?author ?lastName ?foreName ?article ?org ?project
WHERE {
    ?author a pkg:Author .
    OPTIONAL { ?author pkg:lastName ?lastName }
    OPTIONAL { ?author pkg:foreName ?foreName }
    OPTIONAL { ?article pkg:writtenBy ?author }
    OPTIONAL {
        ?author pkg:hasAffiliation ?aff .
        ?aff pkg:affiliatedWith ?org .
    }
    OPTIONAL { ?author pkg:hasProject ?project }
}
LIMIT 20
"""
    }
}


def execute_query(query, timeout=30):
    """Execute a SPARQL query and return results"""
    try:
        sparql = SPARQLWrapper(GRAPHDB_ENDPOINT)
        sparql.setCredentials(GRAPHDB_USERNAME, GRAPHDB_PASSWORD)
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        sparql.setTimeout(timeout)
        
        results = sparql.query().convert()
        bindings = results.get('results', {}).get('bindings', [])
        return bindings
    except Exception as e:
        print(f"    ERROR: {e}")
        return None


def validate_all_queries():
    """Validate all competency queries"""
    print("=" * 70)
    print("COMPETENCY QUESTIONS VALIDATION")
    print("GraphDB Endpoint:", GRAPHDB_ENDPOINT)
    print("=" * 70)
    
    passed = 0
    failed = 0
    errors = 0
    
    for cq_id, cq_data in COMPETENCY_QUERIES.items():
        print(f"\n📌 {cq_id}: {cq_data['question']}")
        print("-" * 50)
        
        results = execute_query(cq_data['query'])
        
        if results is None:
            print("    ❌ QUERY ERROR")
            errors += 1
        elif len(results) == 0:
            print("    ⚠️  NO RESULTS (0 rows)")
            failed += 1
        else:
            print(f"    ✅ PASSED: {len(results)} results")
            # Show sample result
            if results:
                sample = results[0]
                sample_str = ", ".join([f"{k}={v.get('value', '')[:30]}" for k, v in list(sample.items())[:3]])
                print(f"    Sample: {sample_str}...")
            passed += 1
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"✅ Passed: {passed}")
    print(f"⚠️  No Results: {failed}")
    print(f"❌ Errors: {errors}")
    print(f"Total: {passed + failed + errors}")
    
    return passed, failed, errors


if __name__ == "__main__":
    validate_all_queries()
