# Knowledge Graphs Project

PKG2020S4 Knowledge Representation and Reasoning (KRR) project using OWL/RDF ontologies.

## Project Structure

```
├── scripts/           # Python scripts
│   ├── ontology_core.py           # Base ontology with 20+ classes
│   ├── ontology_constraints.py    # OWL axioms and constraints
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
│   ├── pkg2020_core.owl
│   ├── pkg2020_constrained.owl
│   ├── pkg2020_final.owl
│   └── pkg2020_linked.owl         # With external links
├── docs/              # Documentation
│   ├── conceptual_model.md        # Ontology diagram
│   ├── project_report.md          # Full report
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

# BONUS: Web Application
python webapp.py
# Open http://localhost:5000
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

## SPARQL Queries
7 competency queries available in `scripts/sparql_queries.py`

## License
MIT
