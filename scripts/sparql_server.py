"""
PKG2020 Knowledge Graph - SPARQL Server Module
Provides a local SPARQL endpoint using RDFLib
"""
import os
import json
import time
import threading
from functools import lru_cache
from rdflib import Graph, Namespace
from rdflib.plugins.sparql import prepareQuery

# Namespace for our ontology
PKG = Namespace("http://example.org/pkg2020/ontology.owl#")

# Global graph instance with thread lock
_graph = None
_graph_loaded = False
_graph_lock = threading.Lock()

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TTL_PATH = os.path.join(SCRIPT_DIR, "..", "owl", "pkg2020_final.ttl")
OWL_PATH = os.path.join(SCRIPT_DIR, "..", "owl", "pkg2020_final.owl")

def get_best_ontology_path():
    """Get the best available ontology file (prefer TTL for faster loading)"""
    if os.path.exists(TTL_PATH):
        return TTL_PATH, "turtle"
    elif os.path.exists(OWL_PATH):
        return OWL_PATH, "xml"
    else:
        raise FileNotFoundError("No ontology file found in owl/ directory")

def load_graph(force_reload=False):
    """
    Load the RDF graph from the TTL/OWL file.
    Uses lazy loading - only loads when first needed.
    Thread-safe with locking.
    """
    global _graph, _graph_loaded
    
    with _graph_lock:
        if _graph_loaded and not force_reload:
            return _graph
        
        print("=" * 60)
        print("🔄 Loading Knowledge Graph...")
        print("=" * 60)
        
        _graph = Graph()
        
        # Bind common namespaces
        _graph.bind("pkg", PKG)
        _graph.bind("owl", "http://www.w3.org/2002/07/owl#")
        _graph.bind("rdfs", "http://www.w3.org/2000/01/rdf-schema#")
        _graph.bind("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#")
        
        ontology_path, format_type = get_best_ontology_path()
        file_size_mb = os.path.getsize(ontology_path) / (1024 * 1024)
        
        print(f"📁 File: {os.path.basename(ontology_path)}")
        print(f"📊 Size: {file_size_mb:.1f} MB")
        print(f"📝 Format: {format_type}")
        print()
        print("⏳ This may take a few minutes for large files...")
        print()
        
        start_time = time.time()
        _graph.parse(ontology_path, format=format_type)
        elapsed = time.time() - start_time
        
        triple_count = len(_graph)
        print(f"✅ Loaded {triple_count:,} triples in {elapsed:.1f} seconds")
        print("=" * 60)
        
        _graph_loaded = True
        return _graph

def execute_sparql(query_string, format="json"):
    """
    Execute a SPARQL query and return results.
    
    Args:
        query_string: SPARQL query to execute
        format: Output format - "json", "dict", or "raw"
    
    Returns:
        Query results in the specified format
    """
    graph = load_graph()
    
    try:
        results = graph.query(query_string)
        
        if format == "raw":
            return results
        
        # Convert to list of dicts
        result_list = []
        for row in results:
            row_dict = {}
            for var in results.vars:
                value = getattr(row, str(var), None)
                if value is not None:
                    # Convert to string, strip URI prefix if needed
                    str_val = str(value)
                    if str_val.startswith("http://example.org/pkg2020/ontology.owl#"):
                        str_val = str_val.replace("http://example.org/pkg2020/ontology.owl#", "")
                    row_dict[str(var)] = str_val
                else:
                    row_dict[str(var)] = None
            result_list.append(row_dict)
        
        if format == "dict":
            return result_list
        
        # JSON format (default)
        return {
            "head": {"vars": [str(v) for v in results.vars]},
            "results": {
                "bindings": result_list
            },
            "metadata": {
                "count": len(result_list)
            }
        }
    
    except Exception as e:
        return {
            "error": True,
            "message": str(e),
            "query": query_string[:500]
        }

def get_graph_statistics():
    """Get statistics about the loaded graph"""
    try:
        graph = load_graph()
        
        # Count triples
        total_triples = len(graph)
        
        # Count by type - simplified query
        type_query = """
            SELECT ?type (COUNT(?s) AS ?count)
            WHERE {
                ?s a ?type .
            }
            GROUP BY ?type
            ORDER BY DESC(?count)
        """
        
        results = graph.query(type_query)
        
        # Extract class counts directly from results
        class_counts = {}
        for row in results:
            # Access by index since named access might vary
            type_uri = str(row[0])
            count_val = row[1]
            
            # Only include our ontology classes
            if "example.org/pkg2020" in type_uri:
                type_name = type_uri.split("#")[-1] if "#" in type_uri else type_uri.split("/")[-1]
                try:
                    count = int(count_val)
                except (ValueError, TypeError):
                    count = 0
                if type_name and count > 0:
                    class_counts[type_name] = count
        
        return {
            "total_triples": total_triples,
            "class_counts": class_counts
        }
    except Exception as e:
        import traceback
        return {
            "total_triples": 0,
            "class_counts": {},
            "error": str(e),
            "traceback": traceback.format_exc()
        }

# Pre-defined competency queries
COMPETENCY_QUERIES = {
    "authors_multiple_institutions": {
        "title": "Authors with Multiple Institutions",
        "description": "Find authors who have worked in multiple institutions",
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
            LIMIT 50
        """
    },
    "prolific_authors": {
        "title": "Most Prolific Authors",
        "description": "Authors ranked by number of publications",
        "query": """
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
        """
    },
    "articles_with_genes": {
        "title": "Articles Mentioning Genes",
        "description": "Find articles that mention gene entities",
        "query": """
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
        """
    },
    "articles_with_diseases": {
        "title": "Articles Discussing Diseases",
        "description": "Find articles that mention disease entities",
        "query": """
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
        """
    },
    "bioentity_distribution": {
        "title": "BioEntity Type Distribution",
        "description": "Count of each type of biological entity",
        "query": """
            PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
            
            SELECT ?entityType (COUNT(?entity) AS ?count)
            WHERE {
                ?entity a pkg:BioEntity .
                ?entity pkg:entityType ?entityType .
            }
            GROUP BY ?entityType
            ORDER BY DESC(?count)
        """
    },
    "top_organizations": {
        "title": "Top Organizations by Affiliations",
        "description": "Organizations with the most affiliated authors",
        "query": """
            PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
            
            SELECT ?org (COUNT(?aff) AS ?affCount)
            WHERE {
                ?aff a pkg:Affiliation .
                ?aff pkg:affiliatedWith ?org .
            }
            GROUP BY ?org
            ORDER BY DESC(?affCount)
            LIMIT 30
        """
    },
    "author_collaborations": {
        "title": "Author Collaborations",
        "description": "Pairs of authors who frequently collaborate",
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
            HAVING (COUNT(?article) > 1)
            ORDER BY DESC(?collaborations)
            LIMIT 50
        """
    },
    "nih_projects": {
        "title": "NIH Projects Overview",
        "description": "List of NIH funded projects with principal investigators",
        "query": """
            PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
            
            SELECT ?project ?projectNumber ?piName
            WHERE {
                ?project a pkg:NIHProject .
                OPTIONAL { ?project pkg:projectNumber ?projectNumber }
                OPTIONAL { ?project pkg:piName ?piName }
            }
            LIMIT 50
        """
    },
    "education_by_degree": {
        "title": "Education by Degree Type",
        "description": "Distribution of degree types in education records",
        "query": """
            PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
            
            SELECT ?degree (COUNT(?edu) AS ?count)
            WHERE {
                ?edu a pkg:Education .
                ?edu pkg:degree ?degree .
            }
            GROUP BY ?degree
            ORDER BY DESC(?count)
        """
    },
    "geographic_distribution": {
        "title": "Geographic Distribution",
        "description": "Affiliations by country",
        "query": """
            PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
            
            SELECT ?country (COUNT(?aff) AS ?count)
            WHERE {
                ?aff a pkg:Affiliation .
                ?aff pkg:country ?country .
            }
            GROUP BY ?country
            ORDER BY DESC(?count)
            LIMIT 30
        """
    }
}

def get_competency_queries():
    """Return list of available competency queries"""
    return {
        key: {
            "title": val["title"],
            "description": val["description"]
        }
        for key, val in COMPETENCY_QUERIES.items()
    }

def run_competency_query(query_key):
    """Run a predefined competency query"""
    if query_key not in COMPETENCY_QUERIES:
        return {"error": True, "message": f"Unknown query: {query_key}"}
    
    query_info = COMPETENCY_QUERIES[query_key]
    result = execute_sparql(query_info["query"])
    result["title"] = query_info["title"]
    result["description"] = query_info["description"]
    return result


# Test the module
if __name__ == "__main__":
    print("\n🧪 Testing SPARQL Server Module\n")
    
    # Test loading
    graph = load_graph()
    print(f"\n📊 Graph has {len(graph)} triples")
    
    # Test a simple query
    test_query = """
        PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
        SELECT (COUNT(?author) AS ?count)
        WHERE {
            ?author a pkg:Author .
        }
    """
    
    print("\n🔍 Running test query...")
    result = execute_sparql(test_query)
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Get statistics
    print("\n📈 Getting statistics...")
    stats = get_graph_statistics()
    print(f"Stats: {json.dumps(stats, indent=2)}")
