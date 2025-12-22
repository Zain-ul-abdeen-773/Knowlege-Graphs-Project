import pandas as pd
import os
from owlready2 import *

# Get script directory for relative paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)

onto = get_ontology(os.path.join(PROJECT_DIR, "owl", "pkg2020_step6_education_populated.owl")).load()

# Define BioEntity classes and properties
with onto:
    class BioEntity(Thing):
        pass

    class Gene(BioEntity):
        pass

    class Chemical(BioEntity):
        pass

    class Disease(BioEntity):
        pass

    class Species(BioEntity):
        pass

    class Mutation(BioEntity):
        pass

    class mentionsBioEntity(ObjectProperty):
        domain = [onto.Article]
        range = [BioEntity]

    class entityType(DataProperty):
        domain = [BioEntity]
        range = [str]

    class entityName(DataProperty):
        domain = [BioEntity]
        range = [str]

    class entityId(DataProperty):
        domain = [BioEntity]
        range = [str]

# Load caches
Article = onto.Article
BioEntity = onto.BioEntity
Gene = onto.Gene
Chemical = onto.Chemical
Disease = onto.Disease
Species = onto.Species
Mutation = onto.Mutation

# Get all existing article IRIs for synthetic mapping
article_list = list(Article.instances())
article_cache = {a.name: a for a in article_list}
bioentity_cache = {}

print(f"Loaded {len(article_cache)} articles for synthetic mapping")

# Process OA02_Bio_entities_Main - synthetically map to existing articles
try:
    df_main = pd.read_csv(os.path.join(PROJECT_DIR, "data", "OA02_Bio_entities_Main.csv"), nrows=50000)
    print("OA02 Columns:", df_main.columns.tolist())
    
    with onto:
        for idx, row in df_main.iterrows():
            if idx % 10000 == 0:
                print(f"Processing OA02 row {idx}...")
            
            # Synthetically map to existing articles using modulo
            article_idx = idx % len(article_list)
            article = article_list[article_idx]
            
            # Create appropriate BioEntity subclass based on type
            entity_type = str(row.get("Type", "Unknown"))
            entity_id = str(row.get("id", row.name))
            entity_name = str(row.get("Mention", row.get("Name", "Unknown")))
            
            bio_iri = f"BioEntity_{entity_id}"
            if bio_iri not in bioentity_cache:
                if entity_type.lower() == "gene":
                    entity = Gene(bio_iri)
                elif entity_type.lower() == "chemical":
                    entity = Chemical(bio_iri)
                elif entity_type.lower() == "disease":
                    entity = Disease(bio_iri)
                elif entity_type.lower() == "species":
                    entity = Species(bio_iri)
                else:
                    entity = BioEntity(bio_iri)
                
                entity.entityType = [entity_type]
                if pd.notna(entity_name):
                    entity.entityName = [str(entity_name)]
                entity.entityId = [entity_id]
                bioentity_cache[bio_iri] = entity
            
            article.mentionsBioEntity.append(bioentity_cache[bio_iri])
    
    print(f"Processed OA02: {len(df_main)} rows")
except FileNotFoundError:
    print(f"Warning: OA02_Bio_entities_Main.csv not found")
except Exception as e:
    print(f"Error processing OA02: {e}")

# Process OA03_Bio_entities_Mutation - synthetically map to existing articles
try:
    df_mutation = pd.read_csv(os.path.join(PROJECT_DIR, "data", "OA03_Bio_entities_Mutation.csv"), nrows=50000)
    print("OA03 Columns:", df_mutation.columns.tolist())
    
    with onto:
        for idx, row in df_mutation.iterrows():
            if idx % 10000 == 0:
                print(f"Processing OA03 row {idx}...")
            
            # Synthetically map to existing articles using modulo
            article_idx = idx % len(article_list)
            article = article_list[article_idx]
            
            entity_id = str(row.get("id", row.name))
            mutation_iri = f"Mutation_{entity_id}"
            
            if mutation_iri not in bioentity_cache:
                mutation = Mutation(mutation_iri)
                mutation.entityType = ["Mutation"]
                if "MutationType" in row and pd.notna(row["MutationType"]):
                    mutation.entityName = [str(row["MutationType"])]
                bioentity_cache[mutation_iri] = mutation
            
            article.mentionsBioEntity.append(bioentity_cache[mutation_iri])
    
    print(f"Processed OA03: {len(df_mutation)} rows")
except FileNotFoundError:
    print(f"Warning: OA03_Bio_entities_Mutation.csv not found")
except Exception as e:
    print(f"Error processing OA03: {e}")

print(f"Total BioEntities created: {len(bioentity_cache)}")
onto.save(file=os.path.join(PROJECT_DIR, "owl", "pkg2020_step7_bioentities_populated.owl"), format="rdfxml")
print("Saved: pkg2020_step7_bioentities_populated.owl")
