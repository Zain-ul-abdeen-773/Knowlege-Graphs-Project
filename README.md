# Knowledge Graphs Project

PKG2020S4 Knowledge Representation and Reasoning (KRR) project using OWL/RDF ontologies.

## Project Structure

```
├── scripts/           # Python scripts
│   ├── ontology_core.py           # Base ontology with 20+ classes
│   ├── ontology_constraints.py    # OWL axioms and constraints
│   ├── create_tbox_ontology.py    # T-Box only ontology (NEW)
│   ├── create_hand_annotated_individuals.py  # 10+ hand-annotated (NEW)
│   ├── create_swrl_rules.py       # SWRL rules (NEW)
│   ├── populate_authors_articles.py
│   ├── populate_affiliations.py
│   ├── populate_employment.py
│   ├── populate_education.py
│   ├── populate_bioentities.py
│   ├── populate_nih_projects.py
│   ├── validate_ontology.py
│   ├── reasoning.py               # HermiT reasoner
│   ├── link_external_data.py      # DBpedia/Wikidata linking
│   ├── sparql_queries.py          # SPARQL competency queries
│   └── webapp.py                  # BONUS: Web application
├── owl/               # Generated OWL ontology files
│   ├── pkg2020_tbox_only.owl      # T-Box without individuals (NEW)
│   ├── pkg2020_hand_annotated.owl # Hand-annotated individuals (NEW)
│   ├── pkg2020_with_swrl.owl      # T-Box with SWRL rules (NEW)
│   ├── pkg2020_core.owl
│   ├── pkg2020_constrained.owl
│   ├── pkg2020_final.owl
│   ├── pkg2020_final.ttl          # For GraphDB
│   └── pkg2020_linked.owl         # With external links
├── docs/              # Documentation
│   ├── conceptual_model.md        # Ontology diagram
│   ├── project_report.tex         # Full LaTeX report
│   └── visualization_guide.md     # GraphDB/Protégé guide
└── data/              # CSV data files (not included)
```

## Requirements

```bash
pip install -r requirements.txt
```

## Quick Start

```bash
# Run the pipeline
cd scripts
python ontology_core.py
python ontology_constraints.py
python populate_authors_articles.py
python populate_affiliations.py
python populate_employment.py
python populate_education.py
python populate_bioentities.py
python populate_nih_projects.py

# Reasoning & Validation
python reasoning.py
python link_external_data.py

# Web Application with SPARQL Endpoint
python webapp_sparql.py
# Open http://localhost:5000
```

## 🌐 SPARQL Endpoint

The project uses **GraphDB Sandbox** as the live SPARQL endpoint:

### Live Endpoint
```
https://x1327f4041a654297998.sandbox.graphwise.ai/repositories/KRR-Project
```

**Statistics:**
- 2.1M+ triples
- 23 classes
- Full biomedical knowledge graph

### Local Web Application
```bash
cd scripts
python webapp.py
# Open http://localhost:5000
```

### Features
- Live SPARQL query execution against GraphDB
- Interactive graph visualization
- 12 competency queries
- D3.js force-directed graph explorer

### Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/sparql` | GET/POST | Main SPARQL endpoint |
| `/api/stats` | GET | Graph statistics |
| `/api/queries` | GET | List competency queries |
| `/api/query/{key}` | GET | Run predefined query |
| `/api/search?type=Author&q=term` | GET | Search entities |

### Example Query
```bash
curl -X POST http://localhost:5000/sparql \
  -d "query=PREFIX pkg: <http://example.org/pkg2020/ontology.owl#> SELECT ?author WHERE { ?author a pkg:Author } LIMIT 10"
```

### Docker Deployment
```bash
# Start Fuseki triplestore and webapp
docker-compose up -d

# Load data into Fuseki
python scripts/load_to_fuseki.py
```

## Ontology Features

### Classes (20+)
- Core: Article, Author, Authorship, PublicationYear
- Organizational: Organization, Institution, Affiliation
- Career: Employment, Education, NIHProject
- Bio-Medical: BioEntity, Gene, Chemical, Disease, Mutation
- Enumeration: PublicationStatus
- Defined: ActiveAuthor, AnonymousAuthor, ProlificAuthor

### Axioms
- ✅ Enumeration class (PublicationStatus)
- ✅ Cardinality restrictions
- ✅ Intersection class (ActiveAuthor)
- ✅ Union class (ResearchEntity)
- ✅ Complement class (AnonymousAuthor)
- ✅ Functional properties
- ✅ Inverse functional properties

## External Linking (5-Star Linked Data)
- Organizations → DBpedia
- Institutions → Wikidata

## SPARQL Competency Queries
15 competency queries available in `scripts/sparql_queries.py`:
- Authors with multiple institutions
- Prolific authors by article count
- Author collaboration networks
- Articles mentioning genes/diseases
- Mutation-disease correlations
- Bio-entity distribution
- Top organizations by affiliations
- Geographic distribution of affiliations
- Education by institution
- Employment timeline
- Authors with doctoral degrees
- NIH-funded authors
- Principal investigators
