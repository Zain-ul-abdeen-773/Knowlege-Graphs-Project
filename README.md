# Knowledge Graphs Project

PKG2020S4 Knowledge Representation and Reasoning (KRR) project using OWL/RDF ontologies built with OWLReady2.

## Project Structure

```
├── scripts/           # Python scripts for ontology creation and population
│   ├── ontology_core.py           # Base ontology schema
│   ├── ontology_constraints.py    # OWL axioms and constraints
│   ├── populate_authors_articles.py
│   ├── populate_affiliations.py
│   ├── populate_employment.py
│   ├── populate_education.py
│   ├── populate_bioentities.py
│   ├── populate_nih_projects.py
│   ├── validate_ontology.py
│   └── sparql_queries.py          # SPARQL competency queries
├── owl/               # Generated OWL ontology files
│   ├── pkg2020_core.owl
│   ├── pkg2020_constrained.owl
│   └── pkg2020_final.owl          # Final populated ontology
└── data/              # CSV data files (not included - too large)
```

## Requirements

```bash
pip install owlready2 pandas
```

## Usage

Run scripts in order:

```bash
cd scripts
python ontology_core.py
python ontology_constraints.py
python populate_authors_articles.py
python populate_affiliations.py
python populate_employment.py
python populate_education.py
python populate_bioentities.py
python populate_nih_projects.py
python validate_ontology.py
```

## Ontology Classes

- **Article** - Research publications (PMID)
- **Author** - Researchers (AND_ID)
- **Authorship** - Article-Author relationship with order
- **Affiliation** - Author affiliations
- **Organization** - Research organizations
- **Employment** - Author employment history
- **Education** - Author education records
- **Institution** - Educational institutions
- **BioEntity** - Genes, Chemicals, Diseases, Species, Mutations
- **NIHProject** - NIH funding projects

## SPARQL Queries

7 competency queries available in `scripts/sparql_queries.py`:
1. Authors with multiple institutions
2. Articles mentioning specific bio-entities
3. Author collaborations
4. Authors with NIH funding
5. Education by institution
6. Employment timeline
7. Mutation-disease correlations

## Data Sources

PKG2020S4 dataset CSV files (not included):
- OA01_Author_List.csv
- OA02_Bio_entities_Main.csv
- OA03_Bio_entities_Mutation.csv
- OA04_Affiliations.csv
- OA05_Researcher_Employment.csv
- OA06_Researcher_Education.csv
- OA07_NIH_Projects.csv

## License

MIT
