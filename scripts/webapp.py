"""
PKG2020 Knowledge Graph - Web Application with GraphDB SPARQL Endpoint
Uses external GraphDB Sandbox for live SPARQL queries with authentication
"""
from flask import Flask, request, jsonify, Response, render_template
from flask_cors import CORS
from SPARQLWrapper import SPARQLWrapper, JSON
import json
import os

app = Flask(__name__)
CORS(app)

# ============================================================
# GRAPHDB SPARQL ENDPOINT CONFIGURATION WITH CREDENTIALS
# ============================================================
GRAPHDB_ENDPOINT = "https://x1327f4041a654297998.sandbox.graphwise.ai/repositories/KRR-Project"
GRAPHDB_USERNAME = "zainulabdeenfaisal69@gmail.com"
GRAPHDB_PASSWORD = "Eu^bm^8mKM"

# Namespace prefix for queries
PKG_PREFIX = "http://example.org/pkg2020/ontology.owl#"

# All 23 Classes
ALL_CLASSES = [
    "Article", "Author", "Authorship", "PublicationYear", "PublicationStatus",
    "Organization", "Institution", "Affiliation", "Employment", "Education",
    "NIHProject", "BioEntity", "Gene", "Chemical", "Disease", "Species", "Mutation",
    "ActiveAuthor", "AnonymousAuthor", "ResearchEntity", 
    "ProlificAuthor", "SingleAuthorArticle", "MultiAuthorArticle"
]

# Cache for stats
STATS_CACHE = None

# ============================================================
# SPARQL QUERY HELPER FUNCTION
# ============================================================
def execute_sparql(query, timeout=60):
    """Execute SPARQL query against GraphDB endpoint with authentication"""
    try:
        sparql = SPARQLWrapper(GRAPHDB_ENDPOINT)
        sparql.setCredentials(GRAPHDB_USERNAME, GRAPHDB_PASSWORD)
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        sparql.setTimeout(timeout)
        
        results = sparql.query().convert()
        return results
        
    except Exception as e:
        print(f"SPARQL Error: {e}")
        return None

def sparql_results_to_table(results):
    """Convert SPARQL JSON results to table format"""
    if not results or 'results' not in results:
        return {"columns": [], "rows": [], "count": 0}
    
    bindings = results.get('results', {}).get('bindings', [])
    variables = results.get('head', {}).get('vars', [])
    
    rows = []
    for binding in bindings:
        row = []
        for var in variables:
            if var in binding:
                value = binding[var].get('value', '')
                # Clean up URIs to show just the local name
                if value.startswith('http://example.org/pkg2020/ontology.owl#'):
                    value = value.replace('http://example.org/pkg2020/ontology.owl#', '')
                elif value.startswith('http://'):
                    value = value.split('#')[-1].split('/')[-1]
                row.append(value)
            else:
                row.append('')
        rows.append(row)
    
    return {"columns": variables, "rows": rows, "count": len(rows)}

# ============================================================
# STATISTICS ENDPOINT
# ============================================================
@app.route('/api/stats')
def get_stats():
    global STATS_CACHE
    
    if STATS_CACHE is not None:
        return jsonify(STATS_CACHE)
    
    print("📊 Fetching statistics from GraphDB...")
    
    # Query to count all entity types
    count_query = """
    PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
    SELECT ?class (COUNT(?instance) AS ?count)
    WHERE {
        ?instance a ?class .
        FILTER(STRSTARTS(STR(?class), "http://example.org/pkg2020/"))
    }
    GROUP BY ?class
    ORDER BY DESC(?count)
    """
    
    results = execute_sparql(count_query)
    
    if results:
        individuals = {}
        total_count = 0
        
        for binding in results.get('results', {}).get('bindings', []):
            class_uri = binding.get('class', {}).get('value', '')
            class_name = class_uri.replace('http://example.org/pkg2020/ontology.owl#', '')
            count = int(binding.get('count', {}).get('value', 0))
            individuals[class_name] = count
            total_count += count
        
        # Get triple count
        triple_query = "SELECT (COUNT(*) AS ?count) WHERE { ?s ?p ?o }"
        triple_results = execute_sparql(triple_query)
        triple_count = 0
        if triple_results:
            bindings = triple_results.get('results', {}).get('bindings', [])
            if bindings:
                triple_count = int(bindings[0].get('count', {}).get('value', 0))
        
        STATS_CACHE = {
            "classes": len(ALL_CLASSES),
            "triples": triple_count,
            "individuals": individuals,
            "endpoint": GRAPHDB_ENDPOINT,
            "live": True
        }
        print(f"✅ Connected to GraphDB! {triple_count:,} triples found.")
    else:
        # Fallback stats
        STATS_CACHE = {
            "classes": 23,
            "triples": 0,
            "individuals": {cls: 0 for cls in ALL_CLASSES},
            "endpoint": GRAPHDB_ENDPOINT,
            "live": False,
            "error": "Could not fetch live stats"
        }
        print("⚠️ Could not connect to GraphDB")
    
    return jsonify(STATS_CACHE)

# ============================================================
# SPARQL QUERY ENDPOINT
# ============================================================
@app.route('/api/query', methods=['POST'])
def run_query():
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query.strip():
            return jsonify({"error": "Empty query", "columns": [], "rows": []})
        
        print(f"🔍 Executing SPARQL query...")
        results = execute_sparql(query)
        
        if results:
            table = sparql_results_to_table(results)
            table['endpoint'] = GRAPHDB_ENDPOINT
            table['live'] = True
            return jsonify(table)
        else:
            return jsonify({
                "error": "Query failed or timed out",
                "columns": [],
                "rows": [],
                "endpoint": GRAPHDB_ENDPOINT
            })
            
    except Exception as e:
        return jsonify({"error": str(e), "columns": [], "rows": []})

# ============================================================
# RAW SPARQL ENDPOINT (for direct access)
# ============================================================
@app.route('/sparql', methods=['GET', 'POST'])
def sparql_endpoint():
    """W3C compliant SPARQL endpoint proxy"""
    if request.method == 'GET':
        query = request.args.get('query', '')
    else:
        query = request.form.get('query', '') or request.data.decode('utf-8')
    
    if not query:
        return jsonify({"error": "No query provided"}), 400
    
    results = execute_sparql(query)
    
    if results:
        return jsonify(results)
    else:
        return jsonify({"error": "Query execution failed"}), 500

# ============================================================
# COMPETENCY QUERIES (12 Queries)
# ============================================================
COMPETENCY_QUERIES = {
    "cq1": {
        "title": "1. Authors with Multiple Institutions",
        "description": "Which authors have published in multiple institutions?",
        "query": """PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
SELECT ?author (COUNT(DISTINCT ?org) AS ?orgCount)
WHERE {
    ?author a pkg:Author .
    ?author pkg:hasAffiliation ?aff .
    ?aff pkg:affiliatedWith ?org .
}
GROUP BY ?author
HAVING (COUNT(DISTINCT ?org) > 1)
ORDER BY DESC(?orgCount)
LIMIT 20"""
    },
    "cq2": {
        "title": "2. Articles Mentioning Genes",
        "description": "Which articles mention specific bio-entities (genes)?",
        "query": """PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
SELECT ?article ?pmid ?gene ?geneName
WHERE {
    ?article a pkg:Article .
    ?article pkg:hasPMID ?pmid .
    ?article pkg:mentionsBioEntity ?gene .
    ?gene a pkg:Gene .
    OPTIONAL { ?gene pkg:entityName ?geneName }
}
LIMIT 50"""
    },
    "cq3": {
        "title": "3. Author Collaborations",
        "description": "Which authors have collaborated on joint publications?",
        "query": """PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
SELECT ?author1 ?author2 (COUNT(?article) AS ?collaborations)
WHERE {
    ?article a pkg:Article .
    ?article pkg:writtenBy ?author1 .
    ?article pkg:writtenBy ?author2 .
    FILTER (str(?author1) < str(?author2))
}
GROUP BY ?author1 ?author2
ORDER BY DESC(?collaborations)
LIMIT 30"""
    },
    "cq4": {
        "title": "4. Authors with NIH Funding",
        "description": "Which authors have NIH funding?",
        "query": """PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
SELECT ?author ?project ?projectNumber
WHERE {
    ?author a pkg:Author .
    ?author pkg:hasProject ?project .
    ?project pkg:projectNumber ?projectNumber .
}
LIMIT 50"""
    },
    "cq5": {
        "title": "5. Prolific Authors",
        "description": "Most prolific authors by article count",
        "query": """PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
SELECT ?author ?lastName (COUNT(?article) AS ?articleCount)
WHERE {
    ?article a pkg:Article .
    ?article pkg:writtenBy ?author .
    OPTIONAL { ?author pkg:lastName ?lastName }
}
GROUP BY ?author ?lastName
ORDER BY DESC(?articleCount)
LIMIT 20"""
    },
    "cq6": {
        "title": "6. Top Organizations",
        "description": "Organizations with most affiliated authors",
        "query": """PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
SELECT ?org (COUNT(DISTINCT ?author) AS ?authorCount)
WHERE {
    ?author a pkg:Author .
    ?author pkg:hasAffiliation ?aff .
    ?aff pkg:affiliatedWith ?org .
}
GROUP BY ?org
ORDER BY DESC(?authorCount)
LIMIT 20"""
    },
    "cq7": {
        "title": "7. Articles with Mutations",
        "description": "Articles mentioning mutations",
        "query": """PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
SELECT ?article ?pmid ?mutation ?mutationName
WHERE {
    ?article a pkg:Article .
    ?article pkg:hasPMID ?pmid .
    ?article pkg:mentionsBioEntity ?mutation .
    ?mutation a pkg:Mutation .
    OPTIONAL { ?mutation pkg:entityName ?mutationName }
}
LIMIT 50"""
    },
    "cq8": {
        "title": "8. Dataset Statistics",
        "description": "Count of all entity types in the knowledge graph",
        "query": """PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
SELECT ?class (COUNT(?instance) AS ?count)
WHERE {
    ?instance a ?class .
    FILTER(STRSTARTS(STR(?class), "http://example.org/pkg2020/"))
}
GROUP BY ?class
ORDER BY DESC(?count)"""
    },
    "cq9": {
        "title": "9. All Classes in Ontology",
        "description": "List all classes defined in the ontology",
        "query": """PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
SELECT DISTINCT ?class
WHERE {
    { ?class a owl:Class } UNION { ?class a rdfs:Class }
    FILTER(STRSTARTS(STR(?class), "http://example.org/pkg2020/"))
}
ORDER BY ?class"""
    },
    "cq10": {
        "title": "10. Sample Graph Triples",
        "description": "Sample triples from the dataset",
        "query": """PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
SELECT ?subject ?predicate ?object
WHERE {
    ?subject ?predicate ?object .
    FILTER(STRSTARTS(STR(?subject), "http://example.org/pkg2020/"))
}
LIMIT 100"""
    },
    "cq11": {
        "title": "11. Diseases in Articles",
        "description": "Articles mentioning diseases",
        "query": """PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
SELECT ?article ?pmid ?disease ?diseaseName
WHERE {
    ?article a pkg:Article .
    ?article pkg:hasPMID ?pmid .
    ?article pkg:mentionsBioEntity ?disease .
    ?disease a pkg:Disease .
    OPTIONAL { ?disease pkg:entityName ?diseaseName }
}
LIMIT 50"""
    },
    "cq12": {
        "title": "12. Author Education",  
        "description": "Authors with their education records",
        "query": """PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
SELECT ?author ?lastName ?degree ?institution
WHERE {
    ?author a pkg:Author .
    ?author pkg:lastName ?lastName .
    ?author pkg:hasEducation ?edu .
    ?edu pkg:degree ?degree .
    ?edu pkg:educatedAt ?institution .
}
LIMIT 50"""
    }
}

@app.route('/api/competency-queries')
def get_competency_queries():
    return jsonify(COMPETENCY_QUERIES)

@app.route('/api/classes')
def get_classes():
    return jsonify({"classes": ALL_CLASSES, "count": len(ALL_CLASSES)})

# ============================================================
# GRAPH VISUALIZATION DATA
# ============================================================
@app.route('/api/graph-data')
def get_graph_data():
    """Get data for D3.js force-directed graph"""
    nodes = []
    links = []
    
    class_colors = {
        "Article": "#e94560", "Author": "#0f3460", "Authorship": "#16213e",
        "Organization": "#1a1a2e", "Institution": "#533483", "Affiliation": "#e94560",
        "Employment": "#f39c12", "Education": "#3498db", "NIHProject": "#2ecc71",
        "BioEntity": "#9b59b6", "Gene": "#e74c3c", "Chemical": "#1abc9c",
        "Disease": "#f1c40f", "Species": "#34495e", "Mutation": "#e67e22",
        "PublicationYear": "#95a5a6", "PublicationStatus": "#7f8c8d",
        "ActiveAuthor": "#27ae60", "AnonymousAuthor": "#c0392b",
        "ResearchEntity": "#2980b9", "ProlificAuthor": "#8e44ad",
        "SingleAuthorArticle": "#d35400", "MultiAuthorArticle": "#16a085"
    }
    
    for i, cls in enumerate(ALL_CLASSES):
        nodes.append({
            "id": cls,
            "group": i % 5,
            "color": class_colors.get(cls, "#666"),
            "size": 30 if cls in ["Article", "Author", "Organization"] else 20
        })
    
    relationships = [
        ("Article", "Author", "writtenBy"),
        ("Article", "Authorship", "hasAuthorship"),
        ("Article", "BioEntity", "mentionsBioEntity"),
        ("Article", "PublicationStatus", "hasStatus"),
        ("Authorship", "Author", "refersToAuthor"),
        ("Author", "Affiliation", "hasAffiliation"),
        ("Author", "Employment", "hasEmployment"),
        ("Author", "Education", "hasEducation"),
        ("Author", "NIHProject", "hasProject"),
        ("Affiliation", "Organization", "affiliatedWith"),
        ("Employment", "Organization", "employedAt"),
        ("Education", "Institution", "educatedAt"),
        ("Gene", "BioEntity", "subClassOf"),
        ("Chemical", "BioEntity", "subClassOf"),
        ("Disease", "BioEntity", "subClassOf"),
        ("Species", "BioEntity", "subClassOf"),
        ("Mutation", "BioEntity", "subClassOf"),
        ("ActiveAuthor", "Author", "subClassOf"),
        ("AnonymousAuthor", "Author", "subClassOf"),
        ("ProlificAuthor", "Author", "subClassOf"),
        ("SingleAuthorArticle", "Article", "subClassOf"),
        ("MultiAuthorArticle", "Article", "subClassOf"),
    ]
    
    for source, target, label in relationships:
        links.append({"source": source, "target": target, "label": label})
    
    return jsonify({"nodes": nodes, "links": links})

# ============================================================
# ENDPOINT INFO
# ============================================================
@app.route('/api/endpoint')
def get_endpoint_info():
    """Return current SPARQL endpoint info"""
    return jsonify({
        "endpoint": GRAPHDB_ENDPOINT,
        "type": "GraphDB Sandbox",
        "prefix": PKG_PREFIX,
        "authenticated": True
    })

# ============================================================
# MAIN PAGE
# ============================================================
@app.route('/')
def index():
    return render_template('index.html')

# ============================================================
# STARTUP
# ============================================================
if __name__ == '__main__':
    print("="*60)
    print("PKG2020 Knowledge Graph Explorer - GraphDB Edition")
    print("="*60)
    print(f"\n🔗 SPARQL Endpoint: {GRAPHDB_ENDPOINT}")
    print(f"🔐 Authenticated: Yes")
    print("\n🧬 Features:")
    print("  - Live SPARQL queries to GraphDB")
    print("  - Dashboard with real-time statistics")
    print("  - 12 competency queries")
    print("  - Full graph visualization (23 classes)")
    print("  - D3.js chart visualizations")
    print("\n🌐 Open http://localhost:5000 in your browser")
    print("\nPress Ctrl+C to stop\n")
    app.run(debug=True, port=5000, host='0.0.0.0')
