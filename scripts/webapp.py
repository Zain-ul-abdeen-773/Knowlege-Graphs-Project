"""
PKG2020 Knowledge Graph Web Application - Flask + GraphDB Integration (BONUS)
PURPOSE: Interactive web dashboard for exploring the biomedical knowledge graph with live SPARQL queries and D3.js visualization.
HOW: Flask backend proxies authenticated SPARQL queries to GraphDB Sandbox, serves HTML/JS frontend with graph explorer and query builder.
ENDPOINTS: / (dashboard), /sparql (raw SPARQL), /api/query (execute query), /api/stats (graph statistics), /api/competency-queries (15 CQs).
VISUALIZATION: D3.js force-directed graph showing 23 classes and their relationships, interactive query results table, entity statistics.
DEPLOYMENT: Configured for Heroku (Procfile), connects to GraphDB at https://x1327f4041a654297998.sandbox.graphwise.ai/repositories/KRR-Project.
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
# COMPETENCY QUERIES (15 Validated Queries)
# ============================================================
COMPETENCY_QUERIES = {
    "cq1": {
        "title": "CQ1: Authors at Multiple Institutions",
        "description": "Which authors have worked in multiple institutions?",
        "query": """PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
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
LIMIT 30"""
    },
    "cq2": {
        "title": "CQ2: Most Prolific Authors",
        "description": "Who are the most prolific authors by article count?",
        "query": """PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
SELECT ?author ?lastName (COUNT(?article) AS ?articleCount)
WHERE {
    ?author a pkg:Author .
    OPTIONAL { ?author pkg:lastName ?lastName }
    ?article pkg:writtenBy ?author .
}
GROUP BY ?author ?lastName
ORDER BY DESC(?articleCount)
LIMIT 30"""
    },
    "cq3": {
        "title": "CQ3: Author Collaborations",
        "description": "Which authors frequently collaborate together?",
        "query": """PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
SELECT ?author1 ?author2 (COUNT(?article) AS ?collaborations)
WHERE {
    ?article a pkg:Article .
    ?article pkg:writtenBy ?author1 .
    ?article pkg:writtenBy ?author2 .
    FILTER (STR(?author1) < STR(?author2))
}
GROUP BY ?author1 ?author2
ORDER BY DESC(?collaborations)
LIMIT 30"""
    },
    "cq4": {
        "title": "CQ4: Articles with Genes",
        "description": "Which articles mention specific genes?",
        "query": """PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
SELECT ?article ?pmid ?entityName
WHERE {
    ?article a pkg:Article .
    ?article pkg:hasPMID ?pmid .
    ?article pkg:mentionsBioEntity ?entity .
    ?entity a pkg:Gene .
    OPTIONAL { ?entity pkg:entityName ?entityName }
}
LIMIT 50"""
    },
    "cq5": {
        "title": "CQ5: Articles with Species",
        "description": "Which articles mention species?",
        "query": """PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
SELECT ?article ?pmid ?speciesName
WHERE {
    ?article a pkg:Article .
    ?article pkg:hasPMID ?pmid .
    ?article pkg:mentionsBioEntity ?entity .
    ?entity a pkg:Species .
    OPTIONAL { ?entity pkg:entityName ?speciesName }
}
LIMIT 50"""
    },
    "cq6": {
        "title": "CQ6: Gene-Mutation Correlations",
        "description": "Which articles mention both genes and mutations?",
        "query": """PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
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
LIMIT 50"""
    },
    "cq7": {
        "title": "CQ7: Entity Type Distribution",
        "description": "What is the distribution of entity types?",
        "query": """PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
SELECT ?type (COUNT(?entity) AS ?count)
WHERE {
    ?entity rdf:type ?type .
    FILTER(STRSTARTS(STR(?type), "http://example.org/pkg2020/"))
}
GROUP BY ?type
ORDER BY DESC(?count)"""
    },
    "cq8": {
        "title": "CQ8: Top Organizations",
        "description": "Which organizations have the most affiliated authors?",
        "query": """PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
SELECT ?org (COUNT(DISTINCT ?author) AS ?authorCount)
WHERE {
    ?author a pkg:Author .
    ?author pkg:hasAffiliation ?aff .
    ?aff pkg:affiliatedWith ?org .
}
GROUP BY ?org
ORDER BY DESC(?authorCount)
LIMIT 30"""
    },
    "cq9": {
        "title": "CQ9: Affiliations by Country",
        "description": "How are author affiliations distributed by country?",
        "query": """PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
SELECT ?country (COUNT(?aff) AS ?affiliationCount)
WHERE {
    ?aff a pkg:Affiliation .
    ?aff pkg:country ?country .
}
GROUP BY ?country
ORDER BY DESC(?affiliationCount)
LIMIT 30"""
    },
    "cq10": {
        "title": "CQ10: Top Education Institutions",
        "description": "Which institutions produced the most researchers?",
        "query": """PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
SELECT ?institution (COUNT(DISTINCT ?author) AS ?authorCount)
WHERE {
    ?author a pkg:Author .
    ?author pkg:hasEducation ?edu .
    ?edu pkg:educatedAt ?institution .
}
GROUP BY ?institution
ORDER BY DESC(?authorCount)
LIMIT 30"""
    },
    "cq11": {
        "title": "CQ11: Employment Timeline",
        "description": "What is the career timeline of researchers?",
        "query": """PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
SELECT ?author ?lastName ?org ?startYear ?endYear
WHERE {
    ?author a pkg:Author .
    OPTIONAL { ?author pkg:lastName ?lastName }
    ?author pkg:hasEmployment ?emp .
    ?emp pkg:employedAt ?org .
    OPTIONAL { ?emp pkg:startYear ?startYear }
    OPTIONAL { ?emp pkg:endYear ?endYear }
}
LIMIT 50"""
    },
    "cq12": {
        "title": "CQ12: Authors with Education",
        "description": "Which authors have education records?",
        "query": """PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
SELECT ?author ?lastName ?institution
WHERE {
    ?author a pkg:Author .
    OPTIONAL { ?author pkg:lastName ?lastName }
    ?author pkg:hasEducation ?edu .
    ?edu pkg:educatedAt ?institution .
}
LIMIT 50"""
    },
    "cq13": {
        "title": "CQ13: NIH Funded Authors",
        "description": "Which authors have NIH project funding?",
        "query": """PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
SELECT ?author ?lastName ?projectNumber ?piName
WHERE {
    ?author a pkg:Author .
    OPTIONAL { ?author pkg:lastName ?lastName }
    ?author pkg:hasProject ?project .
    OPTIONAL { ?project pkg:projectNumber ?projectNumber }
    OPTIONAL { ?project pkg:piName ?piName }
}
LIMIT 50"""
    },
    "cq14": {
        "title": "CQ14: Principal Investigators",
        "description": "Who are the principal investigators?",
        "query": """PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
SELECT ?project ?piName ?projectNumber
WHERE {
    ?project a pkg:NIHProject .
    OPTIONAL { ?project pkg:piName ?piName }
    OPTIONAL { ?project pkg:projectNumber ?projectNumber }
}
LIMIT 50"""
    },
    "cq15": {
        "title": "CQ15: Complete Author Profile",
        "description": "Get complete author profile with all relationships",
        "query": """PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
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
LIMIT 30"""
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
