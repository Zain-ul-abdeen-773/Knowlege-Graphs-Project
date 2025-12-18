"""
Linking to External Datasets (DBpedia, WikiData)
Links organizations and institutions to external knowledge bases
"""
import re
from owlready2 import *
from urllib.parse import quote

# Load ontology
onto = get_ontology("../owl/pkg2020_final.owl").load()

# Define linking properties
with onto:
    class sameAs(ObjectProperty):
        """owl:sameAs equivalent for linking to external entities"""
        pass
    
    class seeAlso(ObjectProperty):
        """rdfs:seeAlso for related external resources"""
        pass
    
    class dbpediaLink(DataProperty):
        """Link to DBpedia resource"""
        domain = [Thing]
        range = [str]
    
    class wikidataLink(DataProperty):
        """Link to Wikidata entity"""
        domain = [Thing]
        range = [str]

def generate_dbpedia_uri(name):
    """Generate DBpedia URI from organization name"""
    # Clean and format name for DBpedia
    clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', str(name))
    clean_name = clean_name.strip().replace(' ', '_')
    return f"http://dbpedia.org/resource/{quote(clean_name)}"

def generate_wikidata_search_url(name):
    """Generate Wikidata search URL"""
    clean_name = str(name).strip()
    return f"https://www.wikidata.org/w/index.php?search={quote(clean_name)}"

# Link organizations to external datasets
Organization = onto.Organization
Institution = onto.Institution

print("="*60)
print("LINKING TO EXTERNAL DATASETS")
print("="*60)

linked_count = 0

# Link Organizations
print("\n📌 Linking Organizations to DBpedia:")
for org in list(Organization.instances())[:50]:  # Limit for demo
    org_name = org.name.replace('_', ' ')
    dbpedia_uri = generate_dbpedia_uri(org_name)
    org.dbpediaLink = [dbpedia_uri]
    linked_count += 1
    if linked_count <= 5:
        print(f"  {org.name} → {dbpedia_uri}")

print(f"\n  ... Linked {linked_count} organizations")

# Link Institutions
if Institution:
    print("\n📌 Linking Institutions to Wikidata:")
    inst_count = 0
    for inst in list(Institution.instances())[:50]:
        inst_name = inst.name.replace('_', ' ')
        wikidata_url = generate_wikidata_search_url(inst_name)
        inst.wikidataLink = [wikidata_url]
        inst_count += 1
        if inst_count <= 5:
            print(f"  {inst.name} → Wikidata search")
    print(f"\n  ... Linked {inst_count} institutions")

# Save ontology with links
onto.save(file="../owl/pkg2020_linked.owl", format="rdfxml")
print(f"\n✅ Saved: pkg2020_linked.owl with {linked_count} external links")

# Generate sample SPARQL for federated queries
print("\n" + "="*60)
print("FEDERATED SPARQL QUERY EXAMPLES")
print("="*60)

federated_query = """
# Federated query to get DBpedia information about organizations
PREFIX pkg: <http://example.org/pkg2020/ontology.owl#>
PREFIX dbpedia: <http://dbpedia.org/resource/>
PREFIX dbo: <http://dbpedia.org/ontology/>

SELECT ?org ?orgName ?dbpediaLink ?abstract
WHERE {
    ?org a pkg:Organization .
    ?org pkg:dbpediaLink ?dbpediaLink .
    
    SERVICE <http://dbpedia.org/sparql> {
        ?dbpediaLink dbo:abstract ?abstract .
        FILTER (lang(?abstract) = 'en')
    }
}
LIMIT 10
"""

print(federated_query)
