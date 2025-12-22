"""
PKG2020 Knowledge Graph - Professional Web Application
Modern UI with D3.js graphs, animations, and SPARQL query visualization
"""
from flask import Flask, request, jsonify, Response, render_template
from flask_cors import CORS
from rdflib import Graph, Namespace, URIRef
import json
import os

app = Flask(__name__)
CORS(app)

# Configuration
TTL_PATH = "../owl/pkg2020_final.ttl"
OWL_PATH = "../owl/pkg2020_final.owl"

# All 23 Classes (moved up for preloading)
ALL_CLASSES = [
    "Article", "Author", "Authorship", "PublicationYear", "PublicationStatus",
    "Organization", "Institution", "Affiliation", "Employment", "Education",
    "NIHProject", "BioEntity", "Gene", "Chemical", "Disease", "Species", "Mutation",
    "ActiveAuthor", "AnonymousAuthor", "ResearchEntity", 
    "ProlificAuthor", "SingleAuthorArticle", "MultiAuthorArticle"
]

# Global RDF Graph - loaded at startup
g = None
STATS_CACHE = None

def load_graph():
    global g
    if g is None:
        print("\n" + "="*60)
        print("📂 Loading RDF graph (please wait)...")
        print("="*60)
        g = Graph()
        if os.path.exists(TTL_PATH):
            print(f"   Loading from: {TTL_PATH}")
            g.parse(TTL_PATH, format="turtle")
            print(f"   ✅ Loaded {len(g):,} triples from TTL")
        elif os.path.exists(OWL_PATH):
            print(f"   Loading from: {OWL_PATH}")
            g.parse(OWL_PATH, format="xml")
            print(f"   ✅ Loaded {len(g):,} triples from OWL")
        else:
            print("   ⚠️ WARNING: No ontology file found!")
        print("="*60 + "\n")
    return g

def compute_stats():
    global STATS_CACHE
    if STATS_CACHE is None:
        print("📊 Computing statistics from complete data...")
        graph = load_graph()
        
        STATS_CACHE = {
            "classes": 23,
            "triples": len(graph),
            "individuals": {}
        }
        
        for cls in ALL_CLASSES:
            query = f"""
            PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
            SELECT (COUNT(?s) AS ?count) WHERE {{ ?s a pkg:{cls} }}
            """
            try:
                result = list(graph.query(query))
                if result:
                    count = int(result[0][0])
                    STATS_CACHE["individuals"][cls] = count
                    print(f"   {cls}: {count:,}")
            except Exception as e:
                STATS_CACHE["individuals"][cls] = 0
        
        print("✅ Stats computation complete!\n")
    return STATS_CACHE


# Preload graph and compute stats at startup
print("\n🚀 Initializing PKG2020 Knowledge Graph Explorer...")
load_graph()
compute_stats()
print("🎉 Ready to serve requests!\n")

# Competency Questions with SPARQL Queries
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
SELECT ?author (COUNT(?article) AS ?articleCount)
WHERE {
    ?article a pkg:Article .
    ?article pkg:writtenBy ?author .
}
GROUP BY ?author
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
        "description": "Articles mentioning mutations and diseases",
        "query": """PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
SELECT ?article ?pmid ?mutation
WHERE {
    ?article a pkg:Article .
    ?article pkg:hasPMID ?pmid .
    ?article pkg:mentionsBioEntity ?mutation .
    ?mutation a pkg:Mutation .
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
        "description": "List all 23 classes defined in the ontology",
        "query": """PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
SELECT DISTINCT ?class ?label
WHERE {
    { ?class a owl:Class } UNION { ?class a rdfs:Class }
    FILTER(STRSTARTS(STR(?class), "http://example.org/pkg2020/"))
    OPTIONAL { ?class rdfs:label ?label }
}
ORDER BY ?class"""
    },
    "cq10": {
        "title": "10. Complete Graph Sample",
        "description": "Sample of the entire dataset structure",
        "query": """PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
SELECT ?subject ?predicate ?object
WHERE {
    ?subject ?predicate ?object .
    FILTER(STRSTARTS(STR(?subject), "http://example.org/pkg2020/"))
}
LIMIT 100"""
    }
}

@app.route('/api/stats')
def get_stats():
    # Return precomputed stats from complete data
    return jsonify(STATS_CACHE)

@app.route('/api/query', methods=['POST'])
def run_query():
    try:
        graph = load_graph()
        data = request.get_json()
        query = data.get('query', '')
        
        results = graph.query(query)
        
        # Convert to JSON-serializable format
        columns = [str(v) for v in results.vars] if results.vars else []
        rows = []
        for row in results:
            rows.append([str(cell) if cell else "" for cell in row])
        
        return jsonify({"columns": columns, "rows": rows, "count": len(rows)})
    except Exception as e:
        return jsonify({"error": str(e), "columns": [], "rows": []})

@app.route('/api/competency-queries')
def get_competency_queries():
    return jsonify(COMPETENCY_QUERIES)

@app.route('/api/classes')
def get_classes():
    return jsonify({"classes": ALL_CLASSES, "count": len(ALL_CLASSES)})

@app.route('/api/graph-data')
def get_graph_data():
    """Get data for D3.js force-directed graph showing all classes and relationships"""
    nodes = []
    links = []
    
    # Add all 23 classes as nodes
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
    
    # Define relationships between classes
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


from flask import render_template

@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    print("="*60)
    print("PKG2020 Knowledge Graph Explorer - Professional Edition")
    print("="*60)
    print("\n🧬 Features:")
    print("  - Dashboard with animated statistics")
    print("  - Full graph visualization (23 classes)")
    print("  - SPARQL query editor with dropdown")
    print("  - 10 competency queries")
    print("  - Data provenance proof")
    print("  - D3.js chart visualizations")
    print("\n🌐 Open http://localhost:5000 in your browser")
    print("\nPress Ctrl+C to stop\n")
    app.run(debug=True, port=5000, host='0.0.0.0')
