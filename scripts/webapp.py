"""
PKG2020 Knowledge Graph - Web Application Demo (BONUS)
Flask-based application with SPARQL queries
"""
from flask import Flask, render_template, request, jsonify
from owlready2 import *
import os

app = Flask(__name__)

# Load ontology
ONTOLOGY_PATH = "../owl/pkg2020_final.owl"

def get_ontology_stats():
    """Get statistics about the ontology"""
    onto = get_ontology(ONTOLOGY_PATH).load()
    
    stats = {
        "classes": len(list(onto.classes())),
        "object_properties": len(list(onto.object_properties())),
        "data_properties": len(list(onto.data_properties())),
        "individuals": {}
    }
    
    # Count individuals per class
    for cls in onto.classes():
        instances = list(cls.instances())
        if instances:
            stats["individuals"][cls.name] = len(instances)
    
    return stats

def search_authors(query):
    """Search authors by name"""
    onto = get_ontology(ONTOLOGY_PATH).load()
    Author = onto.Author
    
    results = []
    for author in Author.instances():
        name = f"{author.foreName[0] if author.foreName else ''} {author.lastName[0] if author.lastName else ''}"
        if query.lower() in name.lower() or query.lower() in author.name.lower():
            results.append({
                "id": author.name,
                "name": name.strip(),
                "affiliations": len(list(author.hasAffiliation)) if hasattr(author, 'hasAffiliation') else 0
            })
        if len(results) >= 20:
            break
    
    return results

def search_articles(query):
    """Search articles by PMID"""
    onto = get_ontology(ONTOLOGY_PATH).load()
    Article = onto.Article
    
    results = []
    for article in Article.instances():
        pmid = article.hasPMID[0] if article.hasPMID else ""
        if query in pmid or query in article.name:
            results.append({
                "id": article.name,
                "pmid": pmid,
                "authors": len(list(article.writtenBy)) if hasattr(article, 'writtenBy') else 0
            })
        if len(results) >= 20:
            break
    
    return results

def get_author_details(author_id):
    """Get detailed information about an author"""
    onto = get_ontology(ONTOLOGY_PATH).load()
    author = onto[author_id]
    
    if not author:
        return None
    
    details = {
        "id": author_id,
        "name": f"{author.foreName[0] if author.foreName else ''} {author.lastName[0] if author.lastName else ''}".strip(),
        "initials": author.initials[0] if author.initials else "",
        "articles": [],
        "affiliations": [],
        "employment": [],
        "education": []
    }
    
    # Get articles
    if hasattr(author, 'writtenBy'):
        for article in onto.Article.instances():
            if author in article.writtenBy:
                details["articles"].append({
                    "id": article.name,
                    "pmid": article.hasPMID[0] if article.hasPMID else ""
                })
    
    # Get affiliations
    if hasattr(author, 'hasAffiliation'):
        for aff in author.hasAffiliation:
            aff_info = {"id": aff.name}
            if hasattr(aff, 'city') and aff.city:
                aff_info["city"] = aff.city[0]
            if hasattr(aff, 'country') and aff.country:
                aff_info["country"] = aff.country[0]
            details["affiliations"].append(aff_info)
    
    return details

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PKG2020 Knowledge Graph Explorer</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            color: #fff;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
        h1 {
            text-align: center;
            margin-bottom: 2rem;
            font-size: 2.5rem;
            background: linear-gradient(90deg, #e94560, #f39c12);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }
        .stat-card {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 1.5rem;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.2);
        }
        .stat-card h3 { font-size: 2rem; color: #e94560; }
        .stat-card p { color: #aaa; margin-top: 0.5rem; }
        .search-box {
            display: flex;
            gap: 1rem;
            margin-bottom: 2rem;
        }
        input, select, button {
            padding: 1rem;
            border-radius: 10px;
            border: none;
            font-size: 1rem;
        }
        input {
            flex: 1;
            background: rgba(255,255,255,0.1);
            color: #fff;
        }
        input::placeholder { color: #888; }
        button {
            background: linear-gradient(90deg, #e94560, #f39c12);
            color: #fff;
            cursor: pointer;
            transition: transform 0.2s;
        }
        button:hover { transform: scale(1.05); }
        .results {
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 1.5rem;
        }
        .result-item {
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 0.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .result-item:hover { background: rgba(255,255,255,0.15); }
        .badge {
            background: #e94560;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.85rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧬 PKG2020 Knowledge Graph Explorer</h1>
        
        <div class="stats-grid" id="stats">
            <div class="stat-card"><h3>-</h3><p>Classes</p></div>
            <div class="stat-card"><h3>-</h3><p>Authors</p></div>
            <div class="stat-card"><h3>-</h3><p>Articles</p></div>
            <div class="stat-card"><h3>-</h3><p>Organizations</p></div>
        </div>
        
        <div class="search-box">
            <select id="searchType">
                <option value="authors">Search Authors</option>
                <option value="articles">Search Articles (PMID)</option>
            </select>
            <input type="text" id="searchQuery" placeholder="Enter search query...">
            <button onclick="search()">🔍 Search</button>
        </div>
        
        <div class="results" id="results">
            <p style="text-align:center;color:#888;">Enter a search query above</p>
        </div>
    </div>
    
    <script>
        async function loadStats() {
            const res = await fetch('/api/stats');
            const data = await res.json();
            document.getElementById('stats').innerHTML = `
                <div class="stat-card"><h3>${data.classes}</h3><p>Classes</p></div>
                <div class="stat-card"><h3>${data.individuals.Author || 0}</h3><p>Authors</p></div>
                <div class="stat-card"><h3>${data.individuals.Article || 0}</h3><p>Articles</p></div>
                <div class="stat-card"><h3>${data.individuals.Organization || 0}</h3><p>Organizations</p></div>
            `;
        }
        
        async function search() {
            const type = document.getElementById('searchType').value;
            const query = document.getElementById('searchQuery').value;
            if (!query) return;
            
            const res = await fetch(`/api/search/${type}?q=${encodeURIComponent(query)}`);
            const data = await res.json();
            
            if (data.length === 0) {
                document.getElementById('results').innerHTML = '<p style="text-align:center;color:#888;">No results found</p>';
                return;
            }
            
            let html = '';
            data.forEach(item => {
                if (type === 'authors') {
                    html += `<div class="result-item">
                        <div><strong>${item.name}</strong><br><small>${item.id}</small></div>
                        <span class="badge">${item.affiliations} affiliations</span>
                    </div>`;
                } else {
                    html += `<div class="result-item">
                        <div><strong>PMID: ${item.pmid}</strong><br><small>${item.id}</small></div>
                        <span class="badge">${item.authors} authors</span>
                    </div>`;
                }
            });
            document.getElementById('results').innerHTML = html;
        }
        
        loadStats();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return HTML_TEMPLATE

@app.route('/api/stats')
def api_stats():
    return jsonify(get_ontology_stats())

@app.route('/api/search/authors')
def api_search_authors():
    query = request.args.get('q', '')
    return jsonify(search_authors(query))

@app.route('/api/search/articles')
def api_search_articles():
    query = request.args.get('q', '')
    return jsonify(search_articles(query))

@app.route('/api/author/<author_id>')
def api_author_details(author_id):
    details = get_author_details(author_id)
    if details:
        return jsonify(details)
    return jsonify({"error": "Author not found"}), 404

if __name__ == '__main__':
    print("="*60)
    print("PKG2020 Knowledge Graph Explorer")
    print("="*60)
    print("\nStarting web application...")
    print("Open http://localhost:5000 in your browser")
    print("\nPress Ctrl+C to stop\n")
    app.run(debug=True, port=5000)
