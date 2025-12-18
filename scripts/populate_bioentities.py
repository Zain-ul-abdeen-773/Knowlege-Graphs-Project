import pandas as pd
from owlready2 import *

onto = get_ontology("pkg2020_step6_education_populated.owl").load()

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

# Bio entities files path (external location)
BIO_PATH = r"C:\Users\Zain\Downloads\Compressed\New folder"

# Load caches
Article = onto.Article
BioEntity = onto.BioEntity
Gene = onto.Gene
Chemical = onto.Chemical
Disease = onto.Disease
Species = onto.Species
Mutation = onto.Mutation

article_cache = {a.name: a for a in Article.instances()}
bioentity_cache = {}

print(f"Loaded {len(article_cache)} articles")

# Process OA02_Bio_entities_Main
try:
    df_main = pd.read_csv(f"{BIO_PATH}/OA02_Bio_entities_Main.csv", nrows=10000)
    print("OA02 Columns:", df_main.columns.tolist())
    
    with onto:
        for _, row in df_main.iterrows():
            pmid = str(row["PMID"]) if "PMID" in row else None
            if not pmid:
                continue
                
            article_iri = f"Article_{pmid}"
            if article_iri not in article_cache:
                continue
            
            article = article_cache[article_iri]
            
            # Create appropriate BioEntity subclass based on type
            entity_type = str(row.get("Type", "Unknown"))
            entity_id = str(row.get("id", row.name))
            entity_name = str(row.get("Name", "Unknown"))
            
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
                entity.entityName = [entity_name]
                entity.entityId = [entity_id]
                bioentity_cache[bio_iri] = entity
            
            article.mentionsBioEntity.append(bioentity_cache[bio_iri])
    
    print(f"Processed OA02: {len(df_main)} rows")
except FileNotFoundError:
    print(f"Warning: OA02_Bio_entities_Main.csv not found at {BIO_PATH}")
except Exception as e:
    print(f"Error processing OA02: {e}")

# Process OA03_Bio_entities_Mutation
try:
    df_mutation = pd.read_csv(f"{BIO_PATH}/OA03_Bio_entities_Mutation.csv", nrows=10000)
    print("OA03 Columns:", df_mutation.columns.tolist())
    
    with onto:
        for _, row in df_mutation.iterrows():
            pmid = str(row["PMID"]) if "PMID" in row else None
            if not pmid:
                continue
                
            article_iri = f"Article_{pmid}"
            if article_iri not in article_cache:
                continue
            
            article = article_cache[article_iri]
            
            entity_id = str(row.get("id", row.name))
            mutation_iri = f"Mutation_{entity_id}"
            
            if mutation_iri not in bioentity_cache:
                mutation = Mutation(mutation_iri)
                mutation.entityType = ["Mutation"]
                if "MutationType" in row:
                    mutation.entityName = [str(row["MutationType"])]
                bioentity_cache[mutation_iri] = mutation
            
            article.mentionsBioEntity.append(bioentity_cache[mutation_iri])
    
    print(f"Processed OA03: {len(df_mutation)} rows")
except FileNotFoundError:
    print(f"Warning: OA03_Bio_entities_Mutation.csv not found at {BIO_PATH}")
except Exception as e:
    print(f"Error processing OA03: {e}")

print(f"Total BioEntities created: {len(list(BioEntity.instances()))}")
onto.save(file="pkg2020_step7_bioentities_populated.owl", format="rdfxml")
print("Saved: pkg2020_step7_bioentities_populated.owl")
