# TERM PROJECT REPORT
## Knowledge Representation and Reasoning (KRR)
### PKG2020 Knowledge Graph Project

---

**Group Members:**

| Name | Registration No. |
|------|------------------|
| Zain Ul Abdeen | 2023773 |
| Omer Khan | 2023578 |
| Muhammad Umar | 2023535 |

**Instructor:** Dr. Khurram Jadoon  
**Semester:** Fall 2025

---

## 1. Introduction

### Domain Description
The PKG2020S4 (PubMed Knowledge Graph) dataset represents comprehensive bibliometric and researcher metadata from PubMed publications. This domain encompasses research publications (articles identified by PMIDs), researchers/authors (identified by unique AND_IDs), organizational affiliations, career trajectories (employment and education history), NIH project funding associations, and bio-medical entities such as genes, diseases, chemicals, and mutations mentioned in research articles.

### Motivation
This domain was selected to address the fragmented nature of biomedical research data. Traditional CSV-based datasets lack semantic connectivity, making it difficult to discover research collaborations, track researcher career paths, or link publications to molecular and disease entities. Converting this data to linked data enables:
- Semantic querying across heterogeneous data sources
- Discovery of potential research collaborators
- Tracking of NIH funding patterns across institutions
- Linking publications to molecular and disease entities
- Achieving FAIR principles (Findable, Accessible, Interoperable, Reusable)

### Data Description
The dataset consists of 7 CSV files:
- **OA01_Author_List.csv**: Author-article relationships (~2.5 MB)
- **OA04_Affiliations.csv**: Author organizational affiliations (~11.8 MB)
- **OA05_Researcher_Employment.csv**: Employment history (~6.5 MB)
- **OA06_Researcher_Education.csv**: Education records (~6.2 MB)
- **OA02_Bio_entities_Main.csv**: Bio-entities in articles (~2.3 MB)
- **OA03_Bio_entities_Mutation.csv**: Mutations in articles (~2.5 MB)
- **OA07_NIH_Projects.csv**: NIH funding information (~3.3 MB)

### Problem Addressed
The knowledge graph aims to solve the problem of disconnected research data by creating a unified semantic model that enables:
- Finding authors who work across multiple institutions
- Identifying prolific researchers and their collaboration networks
- Linking biomedical research to specific genes, diseases, and mutations
- Tracking researcher career timelines and NIH funding history

---

## 2. Conceptual Model & Competency Questions

### Competency Questions
Our ontology and knowledge graph are designed to answer the following key questions:

1. **CQ1:** Which authors have worked in multiple institutions?
2. **CQ2:** Who are the most prolific authors by article count?
3. **CQ3:** Which articles mention both genes/mutations and diseases?
4. **CQ4:** Which organizations have the most affiliated authors?
5. **CQ5:** Which authors have NIH project funding and who are the principal investigators?

### Conceptual Model

```
                    ┌─────────────┐
                    │  BioEntity  │
                    │ (Gene,      │
                    │  Disease,   │
                    │  Mutation)  │
                    └──────▲──────┘
                           │ mentionsBioEntity
    ┌──────────────┐      │        ┌─────────────┐         ┌──────────────┐
    │  NIHProject  │      │        │   Author    │         │ Organization │
    │ projectNumber│◄─────┼────────│  lastName   │────────►│              │
    │    piName    │      │        │  foreName   │         └──────────────┘
    └──────────────┘      │        └──────┬──────┘                 ▲
           ▲              │               │                        │
           │ hasProject   │               │ hasAffiliation         │ affiliatedWith
           │              │               ▼                        │
           │        ┌─────┴──────┐   ┌─────────────┐         ┌─────┴──────┐
           │        │  Article   │   │ Affiliation │         │Institution │
           └────────│   hasPMID  │   │ city,state  │         └────────────┘
                    │   year     │   │  country    │
                    └────────────┘   └─────────────┘
                          │                                        ▲
                          │ writtenBy                              │ educatedAt
                          ▼                                        │
                    ┌─────────────┐                         ┌──────┴──────┐
                    │ Authorship  │   ┌─────────────┐       │  Education  │
                    │ authorOrder │   │ Employment  │◄──────│   degree    │
                    └─────────────┘   │ startYear   │       │  startYear  │
                                      │  endYear    │       └─────────────┘
                                      └─────────────┘
```

**Key Classes:** Article, Author, Authorship, Organization, Institution, Affiliation, Employment, Education, NIHProject, BioEntity (with subclasses: Gene, Chemical, Disease, Species, Mutation), PublicationStatus (enumeration), PublicationYear

**Key Relationships:** writtenBy, hasAffiliation, affiliatedWith, hasEmployment, employedAt, hasEducation, educatedAt, hasProject, mentionsBioEntity

---

## 3. Ontology Design

### Summary of Classes and Properties
- **23 Classes**: Including Core (Article, Author), Organizational (Organization, Institution, Affiliation), Career (Employment, Education), Bio-Medical (Gene, Disease, Mutation, Chemical, Species), and Defined Classes (ActiveAuthor, AnonymousAuthor, ProlificAuthor)
- **14 Object Properties**: writtenBy, hasAuthorship, refersToAuthor, hasPrimaryAuthor, hasStatus, hasAffiliation, affiliatedWith, hasEmployment, employedAt, hasEducation, educatedAt, hasProject, mentionsBioEntity, sameAs
- **17+ Data Properties**: hasPMID, lastName, foreName, initials, authorOrder, publicationYear, careerStartYear, city, state, country, startYear, endYear, degree, projectNumber, piName, entityName, entityType, dbpediaLink, wikidataLink

### OWL Features Used

| Feature | Implementation |
|---------|----------------|
| **Enumeration Class** | `PublicationStatus = OneOf([Published, Preprint, Retracted, InReview])` |
| **Cardinality Restriction** | `Article ⊑ writtenBy.min(1, Author)`, `Article ⊑ hasPMID.exactly(1, str)` |
| **Range Restriction** | All object/data properties have domain and range defined |
| **Union Class** | `ResearchEntity ≡ Author ⊔ Article` |
| **Intersection Class** | `ActiveAuthor ≡ Author ⊓ ∃careerStartYear.int` |
| **Complement Class** | `AnonymousAuthor ≡ Author ⊓ ¬ActiveAuthor` |
| **Functional Property** | `hasPrimaryAuthor`, `hasStatus`, `hasPMID`, `publicationYear` |
| **Inverse-Functional Property** | `hasPMID` (uniquely identifies articles) |

### Reasoning Results
- **Consistency Check:** Ontology verified as consistent
- **Inferred Classes:** ActiveAuthor, AnonymousAuthor, ProlificAuthor, SingleAuthorArticle, MultiAuthorArticle instances correctly classified by HermiT reasoner

---

## 4. RDF Conversion & Publishing

### Mapping Method
- **Tool Used:** Python OWLReady2 library for OWL ontology creation and manipulation
- **Approach:** Sequential pipeline scripts that load CSV data and create OWL individuals with proper property assertions
- **Pipeline:** `ontology_core.py` → `ontology_constraints.py` → `populate_*.py` scripts → `convert_to_ttl.py`

### URI Pattern
```
Base URI: http://example.org/pkg2020/ontology.owl#
Structure:
  - Articles: pkg:Article_{PMID}
  - Authors: pkg:Author_{AND_ID}
  - Affiliations: pkg:Affiliation_{index}
  - Organizations: pkg:Organization_{hash}
  - BioEntities: pkg:{Type}_{name_hash}
```

### Storage and Publishing
- **Local Storage:** OWL/RDF-XML files in `/owl/` directory
- **TTL Format:** `pkg2020_final.ttl` for triple store compatibility
- **Published To:** GraphDB Sandbox

### SPARQL Endpoint URL
```
https://x1327f4041a654297998.sandbox.graphwise.ai/repositories/KRR-Project
```
- **Statistics:** 2.1M+ triples, 23 classes, full biomedical knowledge graph
- **Deployed Web Application:** https://krr-685beba13d3f.herokuapp.com

---

## 5. SPARQL Queries & Interlinking

### SPARQL Queries (Answering Competency Questions)

**CQ1: Authors with Multiple Institutions**
```sparql
PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>

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
LIMIT 100
```

**CQ2: Most Prolific Authors**
```sparql
PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>

SELECT ?author ?lastName (COUNT(?article) AS ?articleCount)
WHERE {
    ?author a pkg:Author .
    ?author pkg:lastName ?lastName .
    ?article pkg:writtenBy ?author .
}
GROUP BY ?author ?lastName
ORDER BY DESC(?articleCount)
LIMIT 50
```

**CQ3: Mutation-Disease Correlation**
```sparql
PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>

SELECT ?article ?pmid ?mutation ?disease
WHERE {
    ?article a pkg:Article .
    ?article pkg:hasPMID ?pmid .
    ?article pkg:mentionsBioEntity ?m .
    ?m a pkg:Mutation .
    ?m pkg:entityName ?mutation .
    ?article pkg:mentionsBioEntity ?d .
    ?d a pkg:Disease .
    ?d pkg:entityName ?disease .
}
LIMIT 100
```

**Federated Query (DBpedia Integration)**
```sparql
PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
PREFIX dbo: <http://dbpedia.org/ontology/>

SELECT ?org ?dbpediaLink ?abstract
WHERE {
    ?org a pkg:Organization .
    ?org pkg:dbpediaLink ?dbpediaLink .
    
    SERVICE <https://dbpedia.org/sparql> {
        OPTIONAL { ?dbpediaLink dbo:abstract ?abstract }
        FILTER (lang(?abstract) = 'en')
    }
}
LIMIT 10
```

### Linking with External Datasets

| Entity Type | External Source | Linking Method |
|-------------|-----------------|----------------|
| Organizations | DBpedia | `dbpediaLink` property → `http://dbpedia.org/resource/{name}` |
| Institutions | Wikidata | `wikidataLink` property → Wikidata search URL |
| Articles | PubMed | PMID serves as the linking identifier |

---

## 6. Visualization, Results & Reflection

### Visualizations
- **Ontology Visualization:** Generated using GraphDB's visual graph explorer and VOWL
- **Knowledge Graph Visualization:** D3.js force-directed graph in web application
- **Features:** Interactive node exploration, relationship traversal, live SPARQL query results visualization

### Results / Insights
Converting the PKG2020 dataset to Linked Data enabled several new capabilities:

1. **Cross-Domain Queries:** Ability to find authors who collaborate across institutions and their NIH funding status in a single query
2. **Semantic Discovery:** Automated classification of authors (Active, Anonymous, Prolific) through reasoning
3. **Bio-Medical Research Links:** Direct connections between articles, genes, diseases, and mutations enabling correlation discovery
4. **Career Trajectory Analysis:** Unified view of researcher employment, education, and publication history
5. **External Knowledge Integration:** Enrichment with DBpedia organizational information and Wikidata institutional data
6. **FAIR Compliance:** Data now follows Findable, Accessible, Interoperable, and Reusable principles

### GitHub Repository
https://github.com/Zain-ul-abdeen-773/Knowlege-Graphs-Project.git

---

*Report prepared for Knowledge Representation and Reasoning (KRR) Course Project - Fall 2025*
