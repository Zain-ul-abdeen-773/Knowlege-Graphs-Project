"""
PKG2020 Knowledge Graph - Web Application with SPARQL Endpoint
Full-featured Flask application with embedded SPARQL endpoint and query interface
"""
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import os
import json
import sys

# Add scripts directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sparql_server import (
    load_graph, execute_sparql, get_graph_statistics,
    get_competency_queries, run_competency_query, COMPETENCY_QUERIES
)

app = Flask(__name__)
CORS(app)  # Enable CORS for external access

# ============================================================
# SPARQL ENDPOINT ROUTES
# ============================================================

@app.route('/sparql', methods=['GET', 'POST'])
def sparql_endpoint():
    """
    Standard SPARQL 1.1 endpoint
    Supports both GET and POST requests
    """
    # Get query from request
    if request.method == 'POST':
        if request.content_type == 'application/sparql-query':
            query = request.data.decode('utf-8')
        else:
            query = request.form.get('query', request.args.get('query', ''))
    else:
        query = request.args.get('query', '')
    
    if not query:
        return jsonify({
            "error": True,
            "message": "No query provided. Use ?query= parameter or POST body."
        }), 400
    
    # Execute query
    result = execute_sparql(query)
    
    # Check for error
    if isinstance(result, dict) and result.get("error"):
        return jsonify(result), 400
    
    # Return results based on Accept header
    accept = request.headers.get('Accept', 'application/json')
    
    if 'application/json' in accept or 'application/sparql-results+json' in accept:
        return jsonify(result)
    else:
        # Default to JSON
        return jsonify(result)

@app.route('/api/endpoint-info')
def endpoint_info():
    """Return information about the SPARQL endpoint"""
    return jsonify({
        "endpoint": "/sparql",
        "methods": ["GET", "POST"],
        "formats": ["application/json", "application/sparql-results+json"],
        "example": "/sparql?query=SELECT * WHERE { ?s ?p ?o } LIMIT 10",
        "namespaces": {
            "pkg": "http://example.org/pkg2020/ontology.owl#",
            "owl": "http://www.w3.org/2002/07/owl#",
            "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
            "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
        }
    })

# ============================================================
# KNOWLEDGE GRAPH API ROUTES
# ============================================================

@app.route('/api/stats')
def api_stats():
    """Get graph statistics"""
    try:
        stats = get_graph_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": True, "message": str(e)}), 500

@app.route('/api/queries')
def api_queries():
    """Get list of available competency queries"""
    return jsonify(get_competency_queries())

@app.route('/api/query/<query_key>')
def api_run_query(query_key):
    """Run a predefined competency query"""
    result = run_competency_query(query_key)
    if result.get("error"):
        return jsonify(result), 400
    return jsonify(result)

@app.route('/api/query-code/<query_key>')
def api_get_query_code(query_key):
    """Get the SPARQL code for a predefined query"""
    if query_key not in COMPETENCY_QUERIES:
        return jsonify({"error": True, "message": "Query not found"}), 404
    
    query_info = COMPETENCY_QUERIES[query_key]
    return jsonify({
        "key": query_key,
        "title": query_info["title"],
        "description": query_info["description"],
        "query": query_info["query"].strip()
    })

@app.route('/api/search')
def api_search():
    """Search entities by type and query"""
    entity_type = request.args.get('type', 'Author')
    search_term = request.args.get('q', '')
    limit = request.args.get('limit', 50, type=int)
    
    query = f"""
        PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
        
        SELECT DISTINCT ?entity ?label
        WHERE {{
            ?entity a pkg:{entity_type} .
            BIND(STR(?entity) AS ?label)
            FILTER(CONTAINS(LCASE(?label), LCASE("{search_term}")))
        }}
        LIMIT {limit}
    """
    
    return jsonify(execute_sparql(query))

@app.route('/api/graph/schema')
def api_graph_schema():
    """Get ontology schema for visualization"""
    query = """
        PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        
        SELECT DISTINCT ?class ?label
        WHERE {
            ?class a owl:Class .
            FILTER(STRSTARTS(STR(?class), "http://example.org/pkg2020/"))
            BIND(STRAFTER(STR(?class), "#") AS ?label)
        }
    """
    return jsonify(execute_sparql(query))

@app.route('/api/graph/sample')
def api_graph_sample():
    """Get a sample of the graph for visualization"""
    entity_type = request.args.get('type', 'Author')
    limit = request.args.get('limit', 50, type=int)
    
    # Get entities with their relationships
    query = f"""
        PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
        
        SELECT ?subject ?predicate ?object
        WHERE {{
            ?s a pkg:{entity_type} .
            ?s ?predicate ?object .
            BIND(STRAFTER(STR(?s), "#") AS ?subject)
            FILTER(STRSTARTS(STR(?predicate), "http://example.org/pkg2020/"))
        }}
        LIMIT {limit * 3}
    """
    
    result = execute_sparql(query, format="dict")
    
    nodes = {}
    edges = []
    
    if isinstance(result, list):
        for row in result:
            subj = row.get('subject', '')
            pred = row.get('predicate', '').split('#')[-1] if row.get('predicate') else ''
            obj = str(row.get('object', '')).split('#')[-1] if row.get('object') else ''
            
            if subj and subj not in nodes:
                nodes[subj] = {'id': subj, 'label': subj[:20], 'group': entity_type}
            if obj and obj not in nodes and not obj.startswith('http'):
                nodes[obj] = {'id': obj, 'label': obj[:20], 'group': 'property'}
            if subj and obj and pred:
                edges.append({'from': subj, 'to': obj, 'label': pred, 'arrows': 'to'})
    
    return jsonify({
        'nodes': list(nodes.values())[:limit],
        'edges': edges[:limit * 2]
    })

@app.route('/api/graph/explore')
def api_graph_explore():
    """Explore graph centered on an entity"""
    entity = request.args.get('entity', '')
    depth = request.args.get('depth', 1, type=int)
    
    if not entity:
        return jsonify({'nodes': [], 'edges': []})
    
    query = f"""
        PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
        
        SELECT ?s ?p ?o ?sType ?oType
        WHERE {{
            {{
                ?s ?p ?o .
                FILTER(CONTAINS(STR(?s), "{entity}"))
                OPTIONAL {{ ?s a ?sType . FILTER(STRSTARTS(STR(?sType), "http://example.org/pkg2020/")) }}
                OPTIONAL {{ ?o a ?oType . FILTER(STRSTARTS(STR(?oType), "http://example.org/pkg2020/")) }}
            }}
            UNION
            {{
                ?s ?p ?o .
                FILTER(CONTAINS(STR(?o), "{entity}"))
                OPTIONAL {{ ?s a ?sType . FILTER(STRSTARTS(STR(?sType), "http://example.org/pkg2020/")) }}
                OPTIONAL {{ ?o a ?oType . FILTER(STRSTARTS(STR(?oType), "http://example.org/pkg2020/")) }}
            }}
        }}
        LIMIT 100
    """
    
    result = execute_sparql(query, format="dict")
    
    nodes = {}
    edges = []
    
    type_colors = {
        'Author': '#e94560',
        'Article': '#00d4ff',
        'Organization': '#7b2cbf',
        'Affiliation': '#f39c12',
        'BioEntity': '#2ecc71',
        'Education': '#9b59b6',
        'Employment': '#3498db',
        'NIHProject': '#1abc9c',
        'Institution': '#e67e22'
    }
    
    if isinstance(result, list):
        for row in result:
            s = str(row.get('s', '')).split('#')[-1]
            p = str(row.get('p', '')).split('#')[-1]
            o = str(row.get('o', '')).split('#')[-1]
            sType = str(row.get('sType', '')).split('#')[-1] if row.get('sType') else 'Entity'
            oType = str(row.get('oType', '')).split('#')[-1] if row.get('oType') else 'Literal'
            
            if s and s not in nodes:
                nodes[s] = {
                    'id': s, 
                    'label': s[:25] + ('...' if len(s) > 25 else ''),
                    'title': s,
                    'group': sType,
                    'color': type_colors.get(sType, '#888')
                }
            if o and o not in nodes and len(o) < 100:
                nodes[o] = {
                    'id': o, 
                    'label': o[:25] + ('...' if len(o) > 25 else ''),
                    'title': o,
                    'group': oType,
                    'color': type_colors.get(oType, '#666')
                }
            if s and o and p and p not in ['type'] and len(o) < 100:
                edges.append({'from': s, 'to': o, 'label': p, 'arrows': 'to', 'font': {'size': 10}})
    
    return jsonify({
        'nodes': list(nodes.values()),
        'edges': edges
    })

@app.route('/api/graph/overview')
def api_graph_overview():
    """Get overview visualization of entity types and their relationships"""
    # Get class counts
    stats = get_graph_statistics()
    counts = stats.get('class_counts', {})
    
    # Create nodes for each class
    nodes = []
    type_colors = {
        'Author': '#e94560',
        'Article': '#00d4ff', 
        'Organization': '#7b2cbf',
        'Affiliation': '#f39c12',
        'BioEntity': '#2ecc71',
        'Education': '#9b59b6',
        'Employment': '#3498db',
        'NIHProject': '#1abc9c',
        'Institution': '#e67e22',
        'Gene': '#27ae60',
        'Disease': '#c0392b',
        'Chemical': '#8e44ad',
        'Mutation': '#d35400'
    }
    
    for cls, count in counts.items():
        if count > 0:
            nodes.append({
                'id': cls,
                'label': f"{cls}\n({count:,})",
                'title': f"{cls}: {count:,} instances",
                'value': min(count / 100, 50),  # Size based on count
                'color': type_colors.get(cls, '#888'),
                'font': {'color': '#fff'}
            })
    
    # Define relationships between classes
    edges = [
        {'from': 'Author', 'to': 'Article', 'label': 'writes', 'arrows': 'to'},
        {'from': 'Author', 'to': 'Affiliation', 'label': 'hasAffiliation', 'arrows': 'to'},
        {'from': 'Affiliation', 'to': 'Organization', 'label': 'affiliatedWith', 'arrows': 'to'},
        {'from': 'Author', 'to': 'Education', 'label': 'hasEducation', 'arrows': 'to'},
        {'from': 'Education', 'to': 'Institution', 'label': 'educatedAt', 'arrows': 'to'},
        {'from': 'Author', 'to': 'Employment', 'label': 'hasEmployment', 'arrows': 'to'},
        {'from': 'Author', 'to': 'NIHProject', 'label': 'hasProject', 'arrows': 'to'},
        {'from': 'Article', 'to': 'BioEntity', 'label': 'mentionsBioEntity', 'arrows': 'to'},
        {'from': 'Gene', 'to': 'BioEntity', 'label': 'subClassOf', 'dashes': True},
        {'from': 'Disease', 'to': 'BioEntity', 'label': 'subClassOf', 'dashes': True},
        {'from': 'Chemical', 'to': 'BioEntity', 'label': 'subClassOf', 'dashes': True},
        {'from': 'Mutation', 'to': 'BioEntity', 'label': 'subClassOf', 'dashes': True},
    ]
    
    # Filter edges to only include nodes that exist
    node_ids = {n['id'] for n in nodes}
    edges = [e for e in edges if e['from'] in node_ids and e['to'] in node_ids]
    
    return jsonify({'nodes': nodes, 'edges': edges})

# ============================================================
# HTML TEMPLATES
# ============================================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PKG2020 Knowledge Graph - SPARQL Explorer</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/codemirror.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/theme/dracula.min.css">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 50%, #0f2847 100%);
            min-height: 100vh;
            color: #fff;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 1.5rem; }
        
        /* Header */
        header {
            text-align: center;
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        h1 {
            font-size: 2.2rem;
            background: linear-gradient(90deg, #00d4ff, #7b2cbf, #e94560);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }
        .subtitle { color: #888; font-size: 1rem; }
        
        /* Navigation Tabs */
        .tabs {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1.5rem;
            flex-wrap: wrap;
        }
        .tab {
            padding: 0.75rem 1.5rem;
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s;
            color: #aaa;
        }
        .tab:hover { background: rgba(255,255,255,0.1); color: #fff; }
        .tab.active {
            background: linear-gradient(135deg, rgba(0,212,255,0.3), rgba(123,44,191,0.3));
            border-color: #00d4ff;
            color: #fff;
        }
        
        /* Panels */
        .panel { display: none; }
        .panel.active { display: block; }
        
        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 0.75rem;
            margin-bottom: 1.5rem;
        }
        .stat-card {
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 1rem;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
            transition: all 0.3s;
        }
        .stat-card:hover {
            transform: translateY(-3px);
            background: rgba(255,255,255,0.1);
            border-color: #00d4ff;
        }
        .stat-card h3 { font-size: 1.8rem; color: #00d4ff; }
        .stat-card p { color: #888; font-size: 0.85rem; margin-top: 0.25rem; }
        
        /* Query Editor */
        .editor-container {
            background: rgba(0,0,0,0.3);
            border-radius: 15px;
            padding: 1rem;
            margin-bottom: 1rem;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .editor-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.75rem;
            flex-wrap: wrap;
            gap: 0.5rem;
        }
        .editor-title { color: #00d4ff; font-weight: 600; }
        .CodeMirror {
            height: 280px;
            border-radius: 10px;
            font-size: 14px;
        }
        
        /* Buttons */
        .btn {
            padding: 0.6rem 1.2rem;
            border-radius: 8px;
            border: none;
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
        }
        .btn-primary {
            background: linear-gradient(90deg, #00d4ff, #7b2cbf);
            color: #fff;
        }
        .btn-primary:hover { transform: scale(1.05); filter: brightness(1.1); }
        .btn-secondary {
            background: rgba(255,255,255,0.1);
            color: #fff;
            border: 1px solid rgba(255,255,255,0.2);
        }
        .btn-secondary:hover { background: rgba(255,255,255,0.2); }
        
        /* Predefined Queries */
        .queries-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 0.75rem;
            margin-bottom: 1rem;
        }
        .query-card {
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 1rem;
            cursor: pointer;
            transition: all 0.3s;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .query-card:hover {
            background: rgba(255,255,255,0.1);
            border-color: #7b2cbf;
            transform: translateY(-2px);
        }
        .query-card h4 { color: #00d4ff; margin-bottom: 0.4rem; font-size: 0.95rem; }
        .query-card p { color: #888; font-size: 0.8rem; }
        
        /* Results */
        .results-container {
            background: rgba(0,0,0,0.3);
            border-radius: 15px;
            padding: 1rem;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .results-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.75rem;
            flex-wrap: wrap;
            gap: 0.5rem;
        }
        .results-title { color: #e94560; font-weight: 600; }
        .results-meta { color: #888; font-size: 0.85rem; }
        
        /* Table */
        .results-table-wrapper {
            overflow-x: auto;
            max-height: 400px;
            overflow-y: auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85rem;
        }
        th {
            background: rgba(0,212,255,0.2);
            color: #00d4ff;
            padding: 0.75rem;
            text-align: left;
            position: sticky;
            top: 0;
            border-bottom: 2px solid #00d4ff;
        }
        td {
            padding: 0.6rem 0.75rem;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            color: #ccc;
            max-width: 300px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        tr:hover td { background: rgba(255,255,255,0.05); }
        
        /* Endpoint Info */
        .endpoint-box {
            background: rgba(0,212,255,0.1);
            border: 1px solid #00d4ff;
            border-radius: 12px;
            padding: 1.25rem;
            margin-bottom: 1.5rem;
        }
        .endpoint-box h3 { color: #00d4ff; margin-bottom: 0.75rem; }
        .endpoint-url {
            font-family: monospace;
            background: rgba(0,0,0,0.3);
            padding: 0.75rem 1rem;
            border-radius: 8px;
            margin: 0.5rem 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 0.5rem;
        }
        .endpoint-url code { color: #7b2cbf; word-break: break-all; }
        
        /* Loading */
        .loading {
            text-align: center;
            padding: 2rem;
            color: #888;
        }
        .loading::after {
            content: '';
            animation: dots 1.5s infinite;
        }
        @keyframes dots {
            0%, 20% { content: '.'; }
            40% { content: '..'; }
            60%, 100% { content: '...'; }
        }
        
        /* Error */
        .error {
            background: rgba(233,69,96,0.2);
            border: 1px solid #e94560;
            border-radius: 10px;
            padding: 1rem;
            color: #e94560;
        }
        
        /* JSON View */
        .json-view {
            background: rgba(0,0,0,0.5);
            border-radius: 10px;
            padding: 1rem;
            max-height: 400px;
            overflow: auto;
            font-family: monospace;
            font-size: 0.85rem;
            white-space: pre-wrap;
            color: #aaa;
        }
        
        /* Graph Visualization */
        #graphContainer {
            height: 500px;
            background: rgba(0,0,0,0.3);
            border-radius: 15px;
            border: 1px solid rgba(255,255,255,0.1);
            margin-bottom: 1rem;
        }
        .viz-controls {
            display: flex;
            gap: 0.75rem;
            margin-bottom: 1rem;
            flex-wrap: wrap;
            align-items: center;
        }
        .viz-controls select, .viz-controls input {
            padding: 0.6rem 1rem;
            border-radius: 8px;
            border: 1px solid rgba(255,255,255,0.2);
            background: rgba(255,255,255,0.1);
            color: #fff;
            font-size: 0.9rem;
        }
        .viz-controls select option { background: #1a1a3e; }
        .viz-controls input::placeholder { color: #888; }
        .legend {
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            padding: 1rem;
            background: rgba(0,0,0,0.2);
            border-radius: 10px;
        }
        .legend-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.85rem;
            color: #aaa;
        }
        .legend-color {
            width: 16px;
            height: 16px;
            border-radius: 50%;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            h1 { font-size: 1.5rem; }
            .container { padding: 1rem; }
            .CodeMirror { height: 200px; }
            #graphContainer { height: 350px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🧬 PKG2020 Knowledge Graph Explorer</h1>
            <p class="subtitle">SPARQL Endpoint & Interactive Query Interface</p>
        </header>
        
        <!-- Navigation -->
        <div class="tabs">
            <div class="tab active" onclick="showPanel('dashboard')">📊 Dashboard</div>
            <div class="tab" onclick="showPanel('visualization')">🕸️ Graph Viz</div>
            <div class="tab" onclick="showPanel('sparql')">🔍 SPARQL Query</div>
            <div class="tab" onclick="showPanel('queries')">📝 Competency Queries</div>
            <div class="tab" onclick="showPanel('endpoint')">🔗 API Endpoint</div>
        </div>
        
        <!-- Dashboard Panel -->
        <div id="dashboard" class="panel active">
            <div class="stats-grid" id="statsGrid">
                <div class="stat-card"><p class="loading">Loading stats</p></div>
            </div>
            
            <div class="results-container">
                <div class="results-header">
                    <span class="results-title">📈 Quick Overview</span>
                </div>
                <div id="overviewContent">
                    <p class="loading">Loading knowledge graph</p>
                </div>
            </div>
        </div>
        
        <!-- Graph Visualization Panel -->
        <div id="visualization" class="panel">
            <div class="viz-controls">
                <select id="vizType" onchange="changeVizType()">
                    <option value="overview">🏗️ Schema Overview</option>
                    <option value="authors">👤 Authors Network</option>
                    <option value="articles">📄 Articles & BioEntities</option>
                    <option value="organizations">🏢 Organizations</option>
                    <option value="explore">🔍 Explore Entity</option>
                </select>
                <input type="text" id="exploreEntity" placeholder="Enter entity ID to explore..." style="display:none;flex:1;min-width:200px;">
                <button class="btn btn-primary" onclick="loadVisualization()">🔄 Load Graph</button>
                <button class="btn btn-secondary" onclick="fitGraph()">⊞ Fit View</button>
                <button class="btn btn-secondary" onclick="togglePhysics()">⚡ Physics</button>
            </div>
            
            <div id="graphContainer"></div>
            
            <div class="legend" id="graphLegend">
                <div class="legend-item"><span class="legend-color" style="background:#e94560"></span> Author</div>
                <div class="legend-item"><span class="legend-color" style="background:#00d4ff"></span> Article</div>
                <div class="legend-item"><span class="legend-color" style="background:#7b2cbf"></span> Organization</div>
                <div class="legend-item"><span class="legend-color" style="background:#f39c12"></span> Affiliation</div>
                <div class="legend-item"><span class="legend-color" style="background:#2ecc71"></span> BioEntity</div>
                <div class="legend-item"><span class="legend-color" style="background:#9b59b6"></span> Education</div>
                <div class="legend-item"><span class="legend-color" style="background:#3498db"></span> Employment</div>
                <div class="legend-item"><span class="legend-color" style="background:#1abc9c"></span> NIHProject</div>
            </div>
            
            <div class="results-container" style="margin-top:1rem;">
                <div class="results-header">
                    <span class="results-title">ℹ️ Graph Info</span>
                    <span id="graphInfo" class="results-meta"></span>
                </div>
                <p style="color:#888;padding:0.5rem 0;">Click on nodes to see details. Drag to move, scroll to zoom. Double-click a node to explore its connections.</p>
            </div>
        </div>
        
        <!-- SPARQL Query Panel -->
        <div id="sparql" class="panel">
            <div class="editor-container">
                <div class="editor-header">
                    <span class="editor-title">📝 SPARQL Query Editor</span>
                    <div>
                        <button class="btn btn-secondary" onclick="clearEditor()">Clear</button>
                        <button class="btn btn-secondary" onclick="loadSampleQuery()">Sample</button>
                        <button class="btn btn-primary" onclick="executeQuery()">▶️ Execute</button>
                    </div>
                </div>
                <textarea id="queryEditor"></textarea>
            </div>
            
            <div class="results-container">
                <div class="results-header">
                    <span class="results-title">📊 Results</span>
                    <span class="results-meta" id="resultsMeta"></span>
                </div>
                <div id="queryResults">
                    <p style="color:#888;text-align:center;padding:2rem;">Write a query and click Execute</p>
                </div>
            </div>
        </div>
        
        <!-- Competency Queries Panel -->
        <div id="queries" class="panel">
            <h3 style="color:#00d4ff;margin-bottom:1rem;">🎯 Predefined Competency Queries</h3>
            <div class="queries-grid" id="queriesGrid">
                <div class="query-card"><p class="loading">Loading queries</p></div>
            </div>
            
            <div class="results-container">
                <div class="results-header">
                    <span class="results-title" id="queryTitle">📊 Query Results</span>
                    <button class="btn btn-secondary" onclick="viewQueryCode()" id="viewCodeBtn" style="display:none;">View SPARQL</button>
                </div>
                <div id="competencyResults">
                    <p style="color:#888;text-align:center;padding:2rem;">Select a query from above to run</p>
                </div>
            </div>
        </div>
        
        <!-- API Endpoint Panel -->
        <div id="endpoint" class="panel">
            <div class="endpoint-box">
                <h3>🔗 SPARQL Endpoint URL</h3>
                <div class="endpoint-url">
                    <code id="endpointUrl"></code>
                    <button class="btn btn-secondary" onclick="copyEndpoint()">📋 Copy</button>
                </div>
                <p style="color:#888;margin-top:0.5rem;">Use this endpoint with any SPARQL client (Yasgui, GraphDB, etc.)</p>
            </div>
            
            <div class="results-container" style="margin-bottom:1rem;">
                <h4 style="color:#00d4ff;margin-bottom:0.75rem;">📡 HTTP Methods</h4>
                <p style="color:#aaa;margin-bottom:0.5rem;"><strong>GET:</strong> <code>/sparql?query=YOUR_QUERY</code></p>
                <p style="color:#aaa;"><strong>POST:</strong> Body with <code>query</code> parameter or <code>Content-Type: application/sparql-query</code></p>
            </div>
            
            <div class="results-container" style="margin-bottom:1rem;">
                <h4 style="color:#00d4ff;margin-bottom:0.75rem;">📚 Available Namespaces</h4>
                <div class="json-view">PREFIX pkg: &lt;http://example.org/pkg2020/ontology.owl#&gt;
PREFIX owl: &lt;http://www.w3.org/2002/07/owl#&gt;
PREFIX rdfs: &lt;http://www.w3.org/2000/01/rdf-schema#&gt;
PREFIX rdf: &lt;http://www.w3.org/1999/02/22-rdf-syntax-ns#&gt;</div>
            </div>
            
            <div class="results-container">
                <h4 style="color:#00d4ff;margin-bottom:0.75rem;">🧪 API Endpoints</h4>
                <table>
                    <tr><th>Endpoint</th><th>Description</th></tr>
                    <tr><td><code>/sparql</code></td><td>Main SPARQL endpoint</td></tr>
                    <tr><td><code>/api/stats</code></td><td>Graph statistics</td></tr>
                    <tr><td><code>/api/queries</code></td><td>List competency queries</td></tr>
                    <tr><td><code>/api/query/{key}</code></td><td>Run competency query</td></tr>
                    <tr><td><code>/api/search?type=Author&q=term</code></td><td>Search entities</td></tr>
                </table>
            </div>
        </div>
    </div>
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/codemirror.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/mode/sparql/sparql.min.js"></script>
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <script>
        let editor;
        let currentQueryKey = null;
        let network = null;
        let physicsEnabled = true;
        
        // Initialize CodeMirror
        document.addEventListener('DOMContentLoaded', () => {
            editor = CodeMirror.fromTextArea(document.getElementById('queryEditor'), {
                mode: 'sparql',
                theme: 'dracula',
                lineNumbers: true,
                matchBrackets: true,
                autoCloseBrackets: true,
                tabSize: 2
            });
            
            // Set default query
            editor.setValue(`PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>

SELECT ?author ?lastName ?foreName
WHERE {
    ?author a pkg:Author .
    ?author pkg:lastName ?lastName .
    OPTIONAL { ?author pkg:foreName ?foreName }
}
LIMIT 20`);
            
            // Set endpoint URL
            document.getElementById('endpointUrl').textContent = window.location.origin + '/sparql';
            
            // Load data
            loadStats();
            loadCompetencyQueries();
        });
        
        async function loadStats() {
            try {
                const res = await fetch('/api/stats');
                const data = await res.json();
                
                const counts = data.class_counts || {};
                let html = '';
                
                const order = ['Author', 'Article', 'Organization', 'Affiliation', 'Employment', 'Education', 'BioEntity', 'NIHProject', 'Institution'];
                order.forEach(key => {
                    if (counts[key]) {
                        html += `<div class="stat-card"><h3>${counts[key].toLocaleString()}</h3><p>${key}s</p></div>`;
                    }
                });
                
                // Add any remaining
                Object.entries(counts).forEach(([key, val]) => {
                    if (!order.includes(key)) {
                        html += `<div class="stat-card"><h3>${val.toLocaleString()}</h3><p>${key}</p></div>`;
                    }
                });
                
                if (html) {
                    document.getElementById('statsGrid').innerHTML = html;
                }
                
                document.getElementById('overviewContent').innerHTML = `
                    <p style="color:#aaa;">
                        ✅ Knowledge Graph loaded with <strong style="color:#00d4ff;">${data.total_triples?.toLocaleString() || 'N/A'}</strong> triples<br><br>
                        The graph contains data about authors, articles, organizations, affiliations, 
                        employment history, education, biological entities, and NIH projects.<br><br>
                        Use the <strong>SPARQL Query</strong> tab to write custom queries, or try the 
                        <strong>Competency Queries</strong> for predefined analysis.
                    </p>
                `;
            } catch (err) {
                document.getElementById('statsGrid').innerHTML = `<div class="error">Error loading stats: ${err.message}</div>`;
            }
        }
        
        async function loadCompetencyQueries() {
            try {
                const res = await fetch('/api/queries');
                const data = await res.json();
                
                let html = '';
                Object.entries(data).forEach(([key, info]) => {
                    html += `
                        <div class="query-card" onclick="runCompetencyQuery('${key}')">
                            <h4>${info.title}</h4>
                            <p>${info.description}</p>
                        </div>
                    `;
                });
                
                document.getElementById('queriesGrid').innerHTML = html;
            } catch (err) {
                document.getElementById('queriesGrid').innerHTML = `<div class="error">Error: ${err.message}</div>`;
            }
        }
        
        async function runCompetencyQuery(key) {
            currentQueryKey = key;
            document.getElementById('competencyResults').innerHTML = '<p class="loading">Running query</p>';
            document.getElementById('viewCodeBtn').style.display = 'inline-flex';
            
            try {
                const res = await fetch(`/api/query/${key}`);
                const data = await res.json();
                
                document.getElementById('queryTitle').textContent = '📊 ' + (data.title || 'Results');
                displayResults(data, 'competencyResults');
            } catch (err) {
                document.getElementById('competencyResults').innerHTML = `<div class="error">Error: ${err.message}</div>`;
            }
        }
        
        async function viewQueryCode() {
            if (!currentQueryKey) return;
            
            try {
                const res = await fetch(`/api/query-code/${currentQueryKey}`);
                const data = await res.json();
                
                // Switch to SPARQL tab and set query
                showPanel('sparql');
                document.querySelectorAll('.tab')[1].classList.add('active');
                document.querySelectorAll('.tab')[2].classList.remove('active');
                editor.setValue(data.query);
            } catch (err) {
                alert('Error loading query: ' + err.message);
            }
        }
        
        async function executeQuery() {
            const query = editor.getValue();
            if (!query.trim()) {
                alert('Please enter a query');
                return;
            }
            
            document.getElementById('queryResults').innerHTML = '<p class="loading">Executing query</p>';
            document.getElementById('resultsMeta').textContent = '';
            
            try {
                const res = await fetch('/sparql', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: 'query=' + encodeURIComponent(query)
                });
                const data = await res.json();
                
                displayResults(data, 'queryResults');
            } catch (err) {
                document.getElementById('queryResults').innerHTML = `<div class="error">Error: ${err.message}</div>`;
            }
        }
        
        function displayResults(data, containerId) {
            const container = document.getElementById(containerId);
            
            if (data.error) {
                container.innerHTML = `<div class="error">${data.message}</div>`;
                return;
            }
            
            const results = data.results?.bindings || [];
            const vars = data.head?.vars || [];
            
            if (containerId === 'queryResults') {
                document.getElementById('resultsMeta').textContent = `${results.length} results`;
            }
            
            if (results.length === 0) {
                container.innerHTML = '<p style="color:#888;text-align:center;padding:2rem;">No results found</p>';
                return;
            }
            
            let html = '<div class="results-table-wrapper"><table><thead><tr>';
            vars.forEach(v => html += `<th>${v}</th>`);
            html += '</tr></thead><tbody>';
            
            results.forEach(row => {
                html += '<tr>';
                vars.forEach(v => {
                    const val = row[v] || '-';
                    html += `<td title="${val}">${val}</td>`;
                });
                html += '</tr>';
            });
            
            html += '</tbody></table></div>';
            container.innerHTML = html;
        }
        
        function clearEditor() {
            editor.setValue('PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>\\n\\nSELECT \\nWHERE {\\n    \\n}\\nLIMIT 100');
        }
        
        function loadSampleQuery() {
            editor.setValue(`PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>

# Sample: Find prolific authors with their article counts
SELECT ?author ?lastName ?foreName (COUNT(?article) AS ?articleCount)
WHERE {
    ?author a pkg:Author .
    ?author pkg:lastName ?lastName .
    OPTIONAL { ?author pkg:foreName ?foreName }
    ?article pkg:writtenBy ?author .
}
GROUP BY ?author ?lastName ?foreName
ORDER BY DESC(?articleCount)
LIMIT 25`);
        }
        
        function copyEndpoint() {
            navigator.clipboard.writeText(window.location.origin + '/sparql');
            alert('Endpoint URL copied to clipboard!');
        }
        
        // ============ GRAPH VISUALIZATION ============
        function changeVizType() {
            const vizType = document.getElementById('vizType').value;
            const exploreInput = document.getElementById('exploreEntity');
            exploreInput.style.display = vizType === 'explore' ? 'block' : 'none';
        }
        
        async function loadVisualization() {
            const vizType = document.getElementById('vizType').value;
            const container = document.getElementById('graphContainer');
            container.innerHTML = '<p class="loading" style="padding:2rem;text-align:center;">Loading graph</p>';
            
            let url = '/api/graph/overview';
            
            if (vizType === 'overview') {
                url = '/api/graph/overview';
            } else if (vizType === 'authors') {
                url = '/api/graph/sample?type=Author&limit=30';
            } else if (vizType === 'articles') {
                url = '/api/graph/sample?type=Article&limit=30';
            } else if (vizType === 'organizations') {
                url = '/api/graph/sample?type=Organization&limit=30';
            } else if (vizType === 'explore') {
                const entity = document.getElementById('exploreEntity').value;
                if (!entity) {
                    alert('Please enter an entity ID to explore');
                    return;
                }
                url = `/api/graph/explore?entity=${encodeURIComponent(entity)}`;
            }
            
            try {
                const res = await fetch(url);
                const data = await res.json();
                renderGraph(data);
            } catch (err) {
                container.innerHTML = `<div class="error" style="margin:2rem;">Error: ${err.message}</div>`;
            }
        }
        
        function renderGraph(data) {
            const container = document.getElementById('graphContainer');
            container.innerHTML = '';
            
            const nodes = new vis.DataSet(data.nodes || []);
            const edges = new vis.DataSet(data.edges || []);
            
            document.getElementById('graphInfo').textContent = `${data.nodes?.length || 0} nodes, ${data.edges?.length || 0} edges`;
            
            const options = {
                nodes: {
                    shape: 'dot',
                    size: 20,
                    font: { color: '#fff', size: 12 },
                    borderWidth: 2,
                    shadow: true
                },
                edges: {
                    color: { color: '#555', hover: '#00d4ff' },
                    font: { color: '#888', size: 10, align: 'middle' },
                    smooth: { type: 'continuous' },
                    width: 1.5
                },
                physics: {
                    enabled: physicsEnabled,
                    solver: 'forceAtlas2Based',
                    forceAtlas2Based: {
                        gravitationalConstant: -50,
                        centralGravity: 0.01,
                        springLength: 150,
                        springConstant: 0.08
                    },
                    stabilization: { iterations: 100 }
                },
                interaction: {
                    hover: true,
                    tooltipDelay: 200,
                    zoomView: true,
                    dragView: true
                }
            };
            
            network = new vis.Network(container, { nodes, edges }, options);
            
            // Double-click to explore node
            network.on('doubleClick', function(params) {
                if (params.nodes.length > 0) {
                    const nodeId = params.nodes[0];
                    document.getElementById('vizType').value = 'explore';
                    document.getElementById('exploreEntity').style.display = 'block';
                    document.getElementById('exploreEntity').value = nodeId;
                    loadVisualization();
                }
            });
            
            // Click to show info
            network.on('click', function(params) {
                if (params.nodes.length > 0) {
                    const nodeId = params.nodes[0];
                    const node = nodes.get(nodeId);
                    document.getElementById('graphInfo').textContent = `Selected: ${node.title || node.label} (${node.group || 'Entity'})`;
                }
            });
        }
        
        function fitGraph() {
            if (network) network.fit();
        }
        
        function togglePhysics() {
            physicsEnabled = !physicsEnabled;
            if (network) {
                network.setOptions({ physics: { enabled: physicsEnabled } });
            }
        }
        
        // Auto-load overview when switching to visualization tab
        function showPanel(panelId) {
            document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.getElementById(panelId).classList.add('active');
            event.target.classList.add('active');
            
            if (panelId === 'visualization' && !network) {
                loadVisualization();
            }
        }
    </script>
</body>
</html>
"""

# ============================================================
# MAIN ROUTES
# ============================================================

@app.route('/')
def index():
    return HTML_TEMPLATE

@app.route('/health')
def health():
    return jsonify({"status": "ok", "service": "PKG2020 Knowledge Graph"})

# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='PKG2020 Knowledge Graph Web Server')
    parser.add_argument('--port', type=int, default=5000, help='Port to run on')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--preload', action='store_true', help='Preload graph before starting server')
    args = parser.parse_args()
    
    print("=" * 65)
    print("  PKG2020 Knowledge Graph - SPARQL Endpoint Server")
    print("=" * 65)
    print()
    print(f"  🌐 Web Interface:  http://localhost:{args.port}")
    print(f"  🔗 SPARQL Endpoint: http://localhost:{args.port}/sparql")
    print(f"  📊 API Stats:       http://localhost:{args.port}/api/stats")
    print()
    print("  Available Endpoints:")
    print("    GET/POST /sparql         - SPARQL query endpoint")
    print("    GET      /api/stats      - Graph statistics")
    print("    GET      /api/queries    - List competency queries")
    print("    GET      /api/query/{id} - Run competency query")
    print()
    
    if args.preload:
        print("  ⏳ Preloading knowledge graph...")
        load_graph()
        print()
    else:
        print("  💡 Graph will load on first query (may take a few minutes)")
        print()
    
    print("=" * 65)
    print("  Press Ctrl+C to stop the server")
    print("=" * 65)
    print()
    
    app.run(host=args.host, port=args.port, debug=False, threaded=True)
