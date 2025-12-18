"""
PKG2020 Knowledge Graph - Web Application Demo (BONUS)
Flask-based application with comprehensive search across all entity types
"""
from flask import Flask, request, jsonify
from owlready2 import *
import os

app = Flask(__name__)
ONTOLOGY_PATH = "../owl/pkg2020_final.owl"

def get_ontology_stats():
    onto = get_ontology(ONTOLOGY_PATH).load()
    stats = {
        "classes": len(list(onto.classes())),
        "individuals": {}
    }
    for cls in onto.classes():
        instances = list(cls.instances())
        if instances:
            stats["individuals"][cls.name] = len(instances)
    return stats

def search_entity(entity_type, query):
    """Generic search for any entity type"""
    onto = get_ontology(ONTOLOGY_PATH).load()
    
    entity_map = {
        "authors": ("Author", lambda a: {
            "id": a.name,
            "name": f"{a.foreName[0] if a.foreName else ''} {a.lastName[0] if a.lastName else ''}".strip(),
            "extra": f"{len(list(a.hasAffiliation)) if hasattr(a, 'hasAffiliation') else 0} affiliations"
        }),
        "articles": ("Article", lambda a: {
            "id": a.name,
            "name": f"PMID: {a.hasPMID[0] if a.hasPMID else 'N/A'}",
            "extra": f"{len(list(a.writtenBy)) if hasattr(a, 'writtenBy') else 0} authors"
        }),
        "organizations": ("Organization", lambda o: {
            "id": o.name,
            "name": o.name.replace("_", " "),
            "extra": "Organization"
        }),
        "affiliations": ("Affiliation", lambda a: {
            "id": a.name,
            "name": a.name,
            "extra": f"{a.city[0] if hasattr(a,'city') and a.city else ''}, {a.country[0] if hasattr(a,'country') and a.country else ''}"
        }),
        "employment": ("Employment", lambda e: {
            "id": e.name,
            "name": e.name,
            "extra": f"{e.startYear[0] if hasattr(e,'startYear') and e.startYear else '?'} - {e.endYear[0] if hasattr(e,'endYear') and e.endYear else 'Present'}"
        }),
        "education": ("Education", lambda e: {
            "id": e.name,
            "name": e.name,
            "extra": f"{e.degree[0] if hasattr(e,'degree') and e.degree else 'Degree N/A'}"
        }),
        "bioentities": ("BioEntity", lambda b: {
            "id": b.name,
            "name": b.entityName[0] if hasattr(b,'entityName') and b.entityName else b.name,
            "extra": b.entityType[0] if hasattr(b,'entityType') and b.entityType else "BioEntity"
        }),
        "nihprojects": ("NIHProject", lambda p: {
            "id": p.name,
            "name": p.projectNumber[0] if hasattr(p,'projectNumber') and p.projectNumber else p.name,
            "extra": p.piName[0] if hasattr(p,'piName') and p.piName else "PI N/A"
        }),
        "institutions": ("Institution", lambda i: {
            "id": i.name,
            "name": i.name.replace("_", " "),
            "extra": "Institution"
        })
    }
    
    if entity_type not in entity_map:
        return []
    
    class_name, formatter = entity_map[entity_type]
    cls = getattr(onto, class_name, None)
    if not cls:
        return []
    
    results = []
    for entity in cls.instances():
        if query.lower() in entity.name.lower():
            try:
                results.append(formatter(entity))
            except:
                results.append({"id": entity.name, "name": entity.name, "extra": ""})
        if len(results) >= 30:
            break
    return results

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
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 0.75rem;
            margin-bottom: 1.5rem;
        }
        .stat-card {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 1rem;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.2);
            cursor: pointer;
            transition: all 0.3s;
        }
        .stat-card:hover { transform: translateY(-3px); background: rgba(255,255,255,0.15); }
        .stat-card.active { border-color: #e94560; background: rgba(233,69,96,0.2); }
        .stat-card h3 { font-size: 1.5rem; color: #e94560; }
        .stat-card p { color: #aaa; font-size: 0.85rem; }
        .search-box {
            display: flex;
            gap: 1rem;
            margin-bottom: 1.5rem;
        }
        input, select, button {
            padding: 1rem;
            border-radius: 10px;
            border: none;
            font-size: 1rem;
        }
        select { background: rgba(255,255,255,0.15); color: #fff; min-width: 180px; }
        select option { background: #16213e; }
        input { flex: 1; background: rgba(255,255,255,0.1); color: #fff; }
        input::placeholder { color: #888; }
        button {
            background: linear-gradient(90deg, #e94560, #f39c12);
            color: #fff;
            cursor: pointer;
            transition: transform 0.2s;
            padding: 1rem 2rem;
        }
        button:hover { transform: scale(1.05); }
        .results {
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 1.5rem;
            max-height: 500px;
            overflow-y: auto;
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
            font-size: 0.8rem;
            white-space: nowrap;
        }
        .result-name { font-weight: 600; }
        .result-id { font-size: 0.8rem; color: #888; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧬 PKG2020 Knowledge Graph Explorer</h1>
        
        <div class="stats-grid" id="stats"></div>
        
        <div class="search-box">
            <select id="searchType">
                <option value="authors">👤 Authors</option>
                <option value="articles">📄 Articles</option>
                <option value="organizations">🏢 Organizations</option>
                <option value="affiliations">📍 Affiliations</option>
                <option value="employment">💼 Employment</option>
                <option value="education">🎓 Education</option>
                <option value="bioentities">🧬 BioEntities</option>
                <option value="nihprojects">🔬 NIH Projects</option>
                <option value="institutions">🏫 Institutions</option>
            </select>
            <input type="text" id="searchQuery" placeholder="Enter search query... (e.g., Author_, Article_, University)">
            <button onclick="search()">🔍 Search</button>
        </div>
        
        <div class="results" id="results">
            <p style="text-align:center;color:#888;">Select an entity type and enter a search query</p>
        </div>
    </div>
    
    <script>
        async function loadStats() {
            const res = await fetch('/api/stats');
            const data = await res.json();
            const ind = data.individuals;
            document.getElementById('stats').innerHTML = `
                <div class="stat-card" onclick="setSearch('authors')"><h3>${ind.Author || 0}</h3><p>Authors</p></div>
                <div class="stat-card" onclick="setSearch('articles')"><h3>${ind.Article || 0}</h3><p>Articles</p></div>
                <div class="stat-card" onclick="setSearch('organizations')"><h3>${ind.Organization || 0}</h3><p>Organizations</p></div>
                <div class="stat-card" onclick="setSearch('affiliations')"><h3>${ind.Affiliation || 0}</h3><p>Affiliations</p></div>
                <div class="stat-card" onclick="setSearch('employment')"><h3>${ind.Employment || 0}</h3><p>Employment</p></div>
                <div class="stat-card" onclick="setSearch('education')"><h3>${ind.Education || 0}</h3><p>Education</p></div>
                <div class="stat-card" onclick="setSearch('bioentities')"><h3>${ind.BioEntity || 0}</h3><p>BioEntities</p></div>
                <div class="stat-card" onclick="setSearch('nihprojects')"><h3>${ind.NIHProject || 0}</h3><p>NIH Projects</p></div>
            `;
        }
        
        function setSearch(type) {
            document.getElementById('searchType').value = type;
            document.getElementById('searchQuery').value = '';
            document.getElementById('searchQuery').focus();
        }
        
        async function search() {
            const type = document.getElementById('searchType').value;
            const query = document.getElementById('searchQuery').value;
            if (!query) {
                document.getElementById('results').innerHTML = '<p style="text-align:center;color:#888;">Please enter a search query</p>';
                return;
            }
            
            document.getElementById('results').innerHTML = '<p style="text-align:center;color:#888;">Searching...</p>';
            
            const res = await fetch(`/api/search/${type}?q=${encodeURIComponent(query)}`);
            const data = await res.json();
            
            if (data.length === 0) {
                document.getElementById('results').innerHTML = '<p style="text-align:center;color:#888;">No results found</p>';
                return;
            }
            
            let html = '';
            data.forEach(item => {
                html += `<div class="result-item">
                    <div>
                        <div class="result-name">${item.name}</div>
                        <div class="result-id">${item.id}</div>
                    </div>
                    <span class="badge">${item.extra}</span>
                </div>`;
            });
            document.getElementById('results').innerHTML = html;
        }
        
        document.getElementById('searchQuery').addEventListener('keypress', e => {
            if (e.key === 'Enter') search();
        });
        
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

@app.route('/api/search/<entity_type>')
def api_search(entity_type):
    query = request.args.get('q', '')
    return jsonify(search_entity(entity_type, query))

if __name__ == '__main__':
    print("="*60)
    print("PKG2020 Knowledge Graph Explorer")
    print("="*60)
    print("\n📊 Entity Types Available:")
    print("  - Authors, Articles, Organizations")
    print("  - Affiliations, Employment, Education")
    print("  - BioEntities, NIH Projects, Institutions")
    print("\n🌐 Open http://localhost:5000 in your browser")
    print("\nPress Ctrl+C to stop\n")
    app.run(debug=True, port=5000)
