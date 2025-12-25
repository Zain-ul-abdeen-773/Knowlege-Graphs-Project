"""
PKG2020 Hand-Annotated Individuals - Manual A-Box for Testing
PURPOSE: Creates 10+ manually annotated individuals to test defined classes and reasoner classification (simulates Protégé annotation).
HOW: Loads T-Box, creates sample individuals (Article_HAND_001, Author_HAND_001, Gene_HAND_BRCA1, etc.) with explicit property assertions.
KEY TEST: Author_HAND_001 has careerStartYear → classified as ActiveAuthor; Author_HAND_002 lacks it → classified as AnonymousAuthor.
INDIVIDUALS: 2 Articles, 3 Authors, 1 Organization (Harvard→DBpedia), 1 Institution (MIT→Wikidata), Gene, Disease, NIHProject.
OUTPUT: Saves pkg2020_hand_annotated.owl and pkg2020_hand_annotated_reasoned.owl (after running HermiT reasoner).
"""
from owlready2 import *

# Load the T-Box only ontology
onto = get_ontology("../owl/pkg2020_tbox_only.owl").load()

print("="*60)
print("CREATING HAND-ANNOTATED INDIVIDUALS")
print("="*60)

with onto:
    # ========== 1. ARTICLE INDIVIDUALS ==========
    
    # Article 1: Single-author article about cancer research
    article1 = onto.Article("Article_HAND_001")
    article1.hasPMID = "12345678"  # Functional property - direct assignment
    article1.publicationYear = 2023  # Functional
    article1.hasStatus = onto.Published  # Functional
    print("✅ Created: Article_HAND_001 (Cancer Research Paper)")
    
    # Article 2: Multi-author article about gene therapy
    article2 = onto.Article("Article_HAND_002")
    article2.hasPMID = "87654321"
    article2.publicationYear = 2024
    article2.hasStatus = onto.Preprint
    print("✅ Created: Article_HAND_002 (Gene Therapy Paper)")
    
    # ========== 2. AUTHOR INDIVIDUALS ==========
    
    # Author 1: Prolific active author (has career info)
    author1 = onto.Author("Author_HAND_001")
    author1.lastName = ["Smith"]
    author1.foreName = ["John"]
    author1.initials = ["JS"]
    author1.careerStartYear = [2010]  # Makes them an ActiveAuthor
    print("✅ Created: Author_HAND_001 (John Smith - Active Author)")
    
    # Author 2: Anonymous author (no career info) 
    author2 = onto.Author("Author_HAND_002")
    author2.lastName = ["Doe"]
    author2.foreName = ["Jane"]
    author2.initials = ["JD"]
    # No careerStartYear - should be classified as AnonymousAuthor
    print("✅ Created: Author_HAND_002 (Jane Doe - Anonymous Author)")
    
    # Author 3: Another active author for collaboration
    author3 = onto.Author("Author_HAND_003")
    author3.lastName = ["Williams"]
    author3.foreName = ["Robert"]
    author3.initials = ["RW"]
    author3.careerStartYear = [2015]
    print("✅ Created: Author_HAND_003 (Robert Williams - Active Author)")
    
    # ========== 3. LINK ARTICLES TO AUTHORS ==========
    
    # Article 1 written by Author 1 only (SingleAuthorArticle)
    article1.writtenBy = [author1]
    article1.hasPrimaryAuthor = author1  # Functional
    
    # Article 2 written by multiple authors (MultiAuthorArticle)
    article2.writtenBy = [author1, author2, author3]
    article2.hasPrimaryAuthor = author1  # Functional
    
    # ========== 4. ORGANIZATION INDIVIDUAL ==========
    
    org1 = onto.Organization("Org_HAND_Harvard")
    org1.dbpediaLink = ["http://dbpedia.org/resource/Harvard_University"]
    print("✅ Created: Org_HAND_Harvard (Harvard University)")
    
    # ========== 5. INSTITUTION INDIVIDUAL ==========
    
    inst1 = onto.Institution("Inst_HAND_MIT")
    inst1.wikidataLink = ["https://www.wikidata.org/wiki/Q49108"]
    print("✅ Created: Inst_HAND_MIT (MIT)")
    
    # ========== 6. AFFILIATION INDIVIDUAL ==========
    
    aff1 = onto.Affiliation("Aff_HAND_001")
    aff1.city = ["Boston"]
    aff1.state = ["Massachusetts"] 
    aff1.country = ["USA"]
    aff1.affiliatedWith = [org1]
    print("✅ Created: Aff_HAND_001 (Boston, MA affiliation)")
    
    # Link author to affiliation
    author1.hasAffiliation = [aff1]
    
    # ========== 7. EMPLOYMENT INDIVIDUAL ==========
    
    emp1 = onto.Employment("Emp_HAND_001")
    emp1.startYear = [2015]
    emp1.endYear = [2020]
    emp1.jobTitle = ["Research Scientist"]
    emp1.employedAt = [org1]
    print("✅ Created: Emp_HAND_001 (Research Scientist at Harvard)")
    
    # Link author to employment
    author1.hasEmployment = [emp1]
    
    # ========== 8. EDUCATION INDIVIDUAL ==========
    
    edu1 = onto.Education("Edu_HAND_001")
    edu1.degree = ["PhD"]
    edu1.startYear = [2008]
    edu1.endYear = [2014]
    edu1.educatedAt = [inst1]
    print("✅ Created: Edu_HAND_001 (PhD at MIT)")
    
    # Link author to education
    author1.hasEducation = [edu1]
    
    # ========== 9. BIOENTITY INDIVIDUALS ==========
    
    # Gene
    gene1 = onto.Gene("Gene_HAND_BRCA1")
    gene1.entityName = ["BRCA1"]
    gene1.entityType = ["Gene"]
    print("✅ Created: Gene_HAND_BRCA1 (BRCA1 gene)")
    
    # Disease
    disease1 = onto.Disease("Disease_HAND_Cancer")
    disease1.entityName = ["Breast Cancer"]
    disease1.entityType = ["Disease"]
    print("✅ Created: Disease_HAND_Cancer (Breast Cancer)")
    
    # Link article to bio-entities
    article1.mentionsBioEntity = [gene1, disease1]
    
    # ========== 10. NIH PROJECT INDIVIDUAL ==========
    
    nih1 = onto.NIHProject("NIH_HAND_001")
    nih1.projectNumber = ["R01-CA12345"]
    nih1.piName = ["John Smith"]
    print("✅ Created: NIH_HAND_001 (Cancer Research Grant)")
    
    # Link author to NIH project
    author1.hasProject = [nih1]

# ========== SAVE THE ONTOLOGY WITH HAND-ANNOTATED INDIVIDUALS ==========

onto.save(file="../owl/pkg2020_hand_annotated.owl", format="rdfxml")
print("\n" + "="*60)
print("✅ SAVED: pkg2020_hand_annotated.owl")
print("="*60)

# ========== RUN REASONING ==========

print("\n🧠 RUNNING REASONER FOR CLASSIFICATION...")
print("-"*40)

try:
    with onto:
        sync_reasoner(infer_property_values=True)
    print("✅ Reasoning completed successfully!")
    print("✅ Ontology is CONSISTENT")
    
    # Check classifications
    print("\n📊 INFERRED CLASSIFICATIONS:")
    print("-"*40)
    
    # Check ActiveAuthor
    active_authors = list(onto.ActiveAuthor.instances())
    print(f"ActiveAuthor: {len(active_authors)} instance(s)")
    for a in active_authors:
        print(f"  - {a.name}")
    
    # Check AnonymousAuthor
    anon_authors = list(onto.AnonymousAuthor.instances())
    print(f"AnonymousAuthor: {len(anon_authors)} instance(s)")
    for a in anon_authors:
        print(f"  - {a.name}")
    
    # Check SingleAuthorArticle
    single_articles = list(onto.SingleAuthorArticle.instances())
    print(f"SingleAuthorArticle: {len(single_articles)} instance(s)")
    
    # Check MultiAuthorArticle  
    multi_articles = list(onto.MultiAuthorArticle.instances())
    print(f"MultiAuthorArticle: {len(multi_articles)} instance(s)")
    
    # Check FundedAuthor
    funded = list(onto.FundedAuthor.instances())
    print(f"FundedAuthor: {len(funded)} instance(s)")

except Exception as e:
    print(f"⚠️ Reasoner note: {e}")

# Save after reasoning
onto.save(file="../owl/pkg2020_hand_annotated_reasoned.owl", format="rdfxml")
print("\n✅ SAVED: pkg2020_hand_annotated_reasoned.owl (with inferred classifications)")

# ========== SUMMARY ==========

print("\n📋 HAND-ANNOTATED INDIVIDUALS SUMMARY:")
print("-"*40)
print("""
1. Article_HAND_001 - Single-author cancer research paper
2. Article_HAND_002 - Multi-author gene therapy preprint
3. Author_HAND_001 - John Smith (Active Author with career info)
4. Author_HAND_002 - Jane Doe (Anonymous Author, no career info)
5. Author_HAND_003 - Robert Williams (Active Author)
6. Org_HAND_Harvard - Harvard University (linked to DBpedia)
7. Inst_HAND_MIT - MIT (linked to Wikidata)
8. Aff_HAND_001 - Boston affiliation
9. Gene_HAND_BRCA1 - BRCA1 gene entity
10. Disease_HAND_Cancer - Breast Cancer disease entity

Additional supporting individuals:
- Emp_HAND_001 - Employment record
- Edu_HAND_001 - Education record  
- NIH_HAND_001 - NIH project

These individuals demonstrate:
- ActiveAuthor classification (Author 1, 3 have careerStartYear)
- AnonymousAuthor classification (Author 2 has no careerStartYear)
- SingleAuthorArticle (Article 1)
- MultiAuthorArticle (Article 2)
- FundedAuthor (Author 1 has NIH project)
- External linking (DBpedia, Wikidata)
""")

print("\n💡 NEXT STEPS:")
print("1. Open pkg2020_hand_annotated.owl in Protégé")
print("2. Run the reasoner (Reasoner → Start Reasoner)")
print("3. Verify classifications in the 'Inferred' view")
print("4. Take screenshots for the project report")
