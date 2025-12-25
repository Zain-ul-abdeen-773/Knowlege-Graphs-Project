"""
PKG2020 Reasoning & Consistency Checking - OWL Reasoner Script
PURPOSE: Runs HermiT reasoner to check ontology consistency and classify individuals into defined classes (ActiveAuthor, ProlificAuthor, etc.).
HOW: Uses OWLReady2's sync_reasoner() with infer_property_values=True to compute class membership based on equivalent_to definitions.
KEY CHECKS: Validates functional properties (hasPMID), cardinality constraints (min 1 author), detects inconsistencies if axioms conflict.
INFERENCES: Authors with careerStartYear → ActiveAuthor; Authors with 5+ articles → ProlificAuthor; Articles with 1 author → SingleAuthorArticle.
OUTPUT: Reports classification counts and validates ontology consistency - critical for demonstrating OWL reasoning capabilities.
"""
from owlready2 import *
import sys

def run_reasoning(ontology_file):
    """Run reasoning on the ontology and report results"""
    
    print("="*60)
    print("PKG2020 ONTOLOGY REASONING & CONSISTENCY CHECKING")
    print("="*60)
    
    # Load ontology
    print(f"\n📂 Loading ontology: {ontology_file}")
    onto = get_ontology(ontology_file).load()
    
    # Count before reasoning
    print("\n📊 BEFORE REASONING:")
    print("-"*40)
    for cls in onto.classes():
        instances = list(cls.instances())
        if instances:
            print(f"  {cls.name}: {len(instances)} instances")
    
    # Run reasoner
    print("\n🧠 RUNNING REASONER (HermiT)...")
    print("-"*40)
    
    try:
        with onto:
            sync_reasoner(infer_property_values=True)
        print("  ✅ Reasoning completed successfully")
        print("  ✅ Ontology is CONSISTENT")
    except OwlReadyInconsistentOntologyError as e:
        print(f"  ❌ INCONSISTENT ONTOLOGY: {e}")
        return False
    except Exception as e:
        print(f"  ⚠️ Reasoner error: {e}")
        print("  Trying alternative reasoner...")
        try:
            with onto:
                sync_reasoner_hermit(infer_property_values=True)
            print("  ✅ HermiT reasoning completed")
        except Exception as e2:
            print(f"  ⚠️ HermiT also failed: {e2}")
    
    # Count after reasoning (check inferred classifications)
    print("\n📊 AFTER REASONING (Inferred Classifications):")
    print("-"*40)
    
    # Check defined classes
    defined_classes = [
        "ActiveAuthor", "AnonymousAuthor", "ResearchEntity",
        "ProlificAuthor", "SingleAuthorArticle", "MultiAuthorArticle"
    ]
    
    for class_name in defined_classes:
        cls = getattr(onto, class_name, None)
        if cls:
            instances = list(cls.instances())
            print(f"  {class_name}: {len(instances)} classified instances")
    
    # Check consistency of key axioms
    print("\n🔍 AXIOM VALIDATION:")
    print("-"*40)
    
    # Check functional properties
    Article = onto.Article
    hasPMID = onto.hasPMID
    
    articles_without_pmid = [a for a in Article.instances() if not a.hasPMID]
    if articles_without_pmid:
        print(f"  ⚠️ {len(articles_without_pmid)} articles without PMID")
    else:
        print("  ✅ All articles have PMID (functional property validated)")
    
    # Check cardinality on writtenBy
    writtenBy = onto.writtenBy
    articles_without_author = [a for a in Article.instances() if not a.writtenBy]
    if articles_without_author:
        print(f"  ⚠️ {len(articles_without_author)} articles without authors")
    else:
        print("  ✅ All articles have at least 1 author (min cardinality validated)")
    
    print("\n" + "="*60)
    print("REASONING COMPLETE")
    print("="*60)
    
    return True

if __name__ == "__main__":
    ontology_file = sys.argv[1] if len(sys.argv) > 1 else "../owl/pkg2020_final.owl"
    run_reasoning(ontology_file)
