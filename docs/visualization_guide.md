# Visualization and SPARQL Endpoint Setup Guide

## 1. Protégé Visualization

### Setup
1. Download Protégé from https://protege.stanford.edu/
2. Open `owl/pkg2020_constrained.owl` or `owl/pkg2020_final.owl`

### Visualize Ontology
1. Go to **Window → Tabs → OntoGraf**
2. Select classes to visualize
3. Export as image for report

### Run Reasoner in Protégé
1. Go to **Reasoner → HermiT** (or Pellet)
2. Click **Start Reasoner**
3. Check for consistency (yellow icon = consistent)
4. View inferred hierarchy in **Class Hierarchy (inferred)** tab

---

## 2. GraphDB Setup (SPARQL Endpoint)

### Install GraphDB
1. Download from https://graphdb.ontotext.com/
2. Install and start GraphDB
3. Access at http://localhost:7200

### Create Repository
1. Click **Setup → Repositories → Create new repository**
2. Name: `pkg2020`
3. Ruleset: OWL2-RL (for reasoning)
4. Click **Create**

### Import Ontology
1. Select repository `pkg2020`
2. Go to **Import → RDF → Upload files**
3. Upload `owl/pkg2020_final.owl`
4. Click **Import**

### SPARQL Endpoint
- Endpoint URL: `http://localhost:7200/repositories/pkg2020`
- Go to **SPARQL** tab to run queries

---

## 3. Sample SPARQL Queries for GraphDB

### Query 1: Authors with Multiple Affiliations
```sparql
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
LIMIT 20
```

### Query 2: Articles Mentioning Genes
```sparql
PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>

SELECT ?article ?gene ?geneName
WHERE {
    ?article a pkg:Article .
    ?article pkg:mentionsBioEntity ?gene .
    ?gene a pkg:Gene .
    OPTIONAL { ?gene pkg:entityName ?geneName }
}
LIMIT 50
```

### Query 3: Author Collaboration Network
```sparql
PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>

SELECT ?author1 ?author2 (COUNT(?article) AS ?collaborations)
WHERE {
    ?article a pkg:Article .
    ?article pkg:writtenBy ?author1 .
    ?article pkg:writtenBy ?author2 .
    FILTER (?author1 < ?author2)
}
GROUP BY ?author1 ?author2
ORDER BY DESC(?collaborations)
LIMIT 50
```

### Query 4: Federated Query to DBpedia
```sparql
PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
PREFIX dbo: <http://dbpedia.org/ontology/>

SELECT ?org ?dbpediaLink ?abstract
WHERE {
    ?org a pkg:Organization .
    ?org pkg:dbpediaLink ?dbpediaLink .
    
    SERVICE <http://dbpedia.org/sparql> {
        OPTIONAL { ?dbpediaLink dbo:abstract ?abstract }
        FILTER (lang(?abstract) = 'en')
    }
}
LIMIT 10
```

---

## 4. VOWL Visualization

### WebVOWL
1. Go to http://vowl.visualdataweb.org/webvowl.html
2. Upload `owl/pkg2020_constrained.owl`
3. Explore visual ontology representation
4. Take screenshots for report

---

## 5. Python Visualization

Run the visualization script:
```bash
cd scripts
python visualize_graph.py
```

This generates network graphs of author collaborations.
