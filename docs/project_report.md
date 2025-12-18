# PKG2020 Knowledge Graph Project Report

## 1. Introduction to the Domain

The PKG2020S4 (PubMed Knowledge Graph) dataset represents bibliometric and researcher metadata from PubMed publications. This domain encompasses:

- **Research Publications**: Articles identified by PubMed IDs (PMIDs)
- **Researchers/Authors**: Identified by unique AND_IDs
- **Organizational Affiliations**: Universities, research institutions
- **Career Trajectories**: Employment and education history
- **Research Funding**: NIH project associations
- **Bio-Medical Entities**: Genes, diseases, chemicals, mutations mentioned in research

## 2. Motivation and Target Application Use Case

### Motivation
- **Research Analytics**: Enable semantic querying of researcher networks
- **Collaboration Discovery**: Find potential research collaborators
- **Funding Analysis**: Track NIH funding patterns across institutions
- **Bio-Medical Research**: Link publications to molecular/disease entities
- **Career Tracking**: Analyze researcher career trajectories

### Target Applications
1. Research collaboration recommendation system
2. Funding opportunity matching
3. Researcher profiling and expertise identification
4. Publication trend analysis
5. Bio-entity research landscape mapping

## 3. Dataset Description

| CSV File | Description | Key Fields |
|----------|-------------|------------|
| OA01_Author_List | Author-article relationships | PMID, AND_ID, LastName, ForeName |
| OA04_Affiliations | Author affiliations | AND_ID, Affiliation, City, Country |
| OA05_Researcher_Employment | Employment history | AND_ID, Organization, StartYear, EndYear |
| OA06_Researcher_Education | Education records | AND_ID, Institution, Degree |
| OA02_Bio_entities_Main | Bio-entities in articles | PMID, Type, Name |
| OA03_Bio_entities_Mutation | Mutations in articles | PMID, MutationType |
| OA07_NIH_Projects | NIH funding | AND_ID, ProjectNumber |

## 4. Ontology Design

### 4.1 Classes (20+ as required)
1. Article, Author, Authorship, PublicationYear
2. Organization, Institution, Affiliation
3. Employment, Education
4. NIHProject
5. BioEntity, Gene, Chemical, Disease, Species, Mutation
6. PublicationStatus (enumeration)
7. ActiveAuthor, AnonymousAuthor, ResearchEntity (defined)
8. ProlificAuthor, SingleAuthorArticle, MultiAuthorArticle (defined)

### 4.2 Special Classes
- **Enumeration**: PublicationStatus = {Published, Preprint, Retracted, InReview}
- **Intersection**: ActiveAuthor = Author ⊓ ∃careerStartYear
- **Union**: ResearchEntity = Author ⊔ Article
- **Complement**: AnonymousAuthor = Author ⊓ ¬ActiveAuthor
- **Cardinality**: Article with writtenBy.min(1)

### 4.3 Properties
- **Functional**: hasPrimaryAuthor, hasStatus, hasPMID
- **Inverse Functional**: hasPMID
- **Object Properties**: 10+ (writtenBy, hasAffiliation, hasEmployment, etc.)
- **Data Properties**: 15+ (lastName, foreName, city, degree, etc.)

## 5. External Linking (5-Star Linked Data)

- Organizations linked to **DBpedia**
- Institutions linked to **Wikidata**
- Federated SPARQL queries enabled

## 6. Tools Used

- **Ontology**: OWLReady2 (Python)
- **Data Processing**: Pandas
- **Reasoning**: HermiT reasoner
- **Visualization**: GraphDB, Protégé
- **SPARQL Endpoint**: GraphDB/Virtuoso

## 7. Validation

- Reasoning performed with HermiT
- Consistency checking passed
- Competency questions validated via SPARQL

## 8. Reflections

Converting non-RDF data to linked data enabled:
- Semantic querying across heterogeneous datasets
- Reasoning over implicit relationships
- Integration with global knowledge bases
- FAIR data principles compliance
