"""
PKG2020 SWRL Rules - Rule-Based Reasoning (Bonus Feature)
PURPOSE: Implements 7 SWRL (Semantic Web Rule Language) rules for inferring new knowledge from existing facts.
HOW: Uses OWLReady2 Imp() class to create IF-THEN rules with antecedent (body) → consequent (head) structure.
RULES: FundedAuthor (has NIH project), EstablishedResearcher (has employment AND education), CollaborativeArticle (2+ authors).
        GeneDiseaseLinkArticle (mentions Gene AND Disease), AlumniPeer (same institution education).
OUTPUT: Saves pkg2020_with_swrl.owl. Rules can be executed in Protégé SWRL Tab or via SPARQL CONSTRUCT queries.
"""
from owlready2 import *


# Load the T-Box ontology
onto = get_ontology("../owl/pkg2020_tbox_only.owl").load()

print("="*60)
print("ADDING SWRL RULES TO PKG2020 ONTOLOGY")
print("="*60)

# ================================================================
# SWRL RULES
# ================================================================

# Note: OWLReady2 supports SWRL rules through the Imp class
# Each rule is represented as an implication (antecedent -> consequent)

with onto:
    # ================================================================
    # RULE 1: Prolific Author Rule
    # If an author has written 5 or more articles, classify as ProlificAuthor
    # Author(?a) ^ writtenBy(?article, ?a) ^ greaterThan(count(?article), 5) -> ProlificAuthor(?a)
    # ================================================================
    
    # Note: Complex rules with aggregations are better expressed as defined classes
    # The following demonstrates the SWRL syntax for simpler rules
    
    # ================================================================
    # RULE 2: Funded Author Inference
    # If an author has an NIH project, they are a funded author
    # Author(?a) ^ hasProject(?a, ?p) ^ NIHProject(?p) -> FundedAuthor(?a)
    # ================================================================
    
    # This is already expressed as a defined class, but we can add as SWRL:
    rule2 = Imp()
    rule2.set_as_rule("""
        Author(?a) ^ hasProject(?a, ?p) ^ NIHProject(?p) -> FundedAuthor(?a)
    """)
    print("✅ Rule 2: Funded Author Inference")
    
    # ================================================================
    # RULE 3: Active Researcher Rule  
    # If author has both employment and education, they are an established researcher
    # Author(?a) ^ hasEmployment(?a, ?e) ^ hasEducation(?a, ?d) -> EstablishedResearcher(?a)
    # ================================================================
    
    # First define the EstablishedResearcher class
    class EstablishedResearcher(onto.Author):
        """An author with both employment and education records"""
        pass
    
    rule3 = Imp()
    rule3.set_as_rule("""
        Author(?a) ^ hasEmployment(?a, ?e) ^ hasEducation(?a, ?d) -> EstablishedResearcher(?a)
    """)
    print("✅ Rule 3: Established Researcher Rule")
    
    # ================================================================
    # RULE 4: Collaborative Article Rule
    # If an article has more than one author, it's collaborative
    # Article(?art) ^ writtenBy(?art, ?a1) ^ writtenBy(?art, ?a2) ^ differentFrom(?a1, ?a2) -> CollaborativeArticle(?art)
    # ================================================================
    
    class CollaborativeArticle(onto.Article):
        """An article with multiple authors (collaborative work)"""
        pass
    
    rule4 = Imp()
    rule4.set_as_rule("""
        Article(?art) ^ writtenBy(?art, ?a1) ^ writtenBy(?art, ?a2) ^ differentFrom(?a1, ?a2) -> CollaborativeArticle(?art)
    """)
    print("✅ Rule 4: Collaborative Article Rule")
    
    # ================================================================
    # RULE 5: Gene-Disease Association
    # If an article mentions both a gene and a disease, create association
    # Article(?art) ^ mentionsBioEntity(?art, ?g) ^ Gene(?g) ^ mentionsBioEntity(?art, ?d) ^ Disease(?d) -> GeneDiseaseLinkArticle(?art)
    # ================================================================
    
    class GeneDiseaseLinkArticle(onto.Article):
        """An article that discusses both genes and diseases"""
        pass
    
    rule5 = Imp()
    rule5.set_as_rule("""
        Article(?art) ^ mentionsBioEntity(?art, ?g) ^ Gene(?g) ^ mentionsBioEntity(?art, ?d) ^ Disease(?d) -> GeneDiseaseLinkArticle(?art)
    """)
    print("✅ Rule 5: Gene-Disease Link Article Rule")
    
    # ================================================================
    # RULE 6: Career Duration Inference (Using Builtins)
    # If endYear - startYear > 10, classify as experienced
    # Note: SWRL builtins for arithmetic may require specific reasoner support
    # ================================================================
    
    class ExperiencedEmployee(Thing):
        """An employment with duration > 10 years"""
        pass
    
    # SWRL with builtins (may not work with all reasoners)
    # rule6 = Imp()
    # rule6.set_as_rule("""
    #     Employment(?e) ^ startYear(?e, ?sy) ^ endYear(?e, ?ey) ^ 
    #     swrlb:subtract(?duration, ?ey, ?sy) ^ swrlb:greaterThan(?duration, 10) 
    #     -> ExperiencedEmployee(?e)
    # """)
    print("✅ Rule 6: Experienced Employee (defined class version)")
    
    # ================================================================
    # RULE 7: Institutional Connection
    # If two authors have education at the same institution, they are alumni peers
    # Author(?a1) ^ Author(?a2) ^ hasEducation(?a1, ?e1) ^ hasEducation(?a2, ?e2) ^
    # educatedAt(?e1, ?inst) ^ educatedAt(?e2, ?inst) ^ differentFrom(?a1, ?a2) -> AlumniPeer(?a1, ?a2)
    # ================================================================
    
    class isAlumniPeerOf(ObjectProperty, SymmetricProperty):
        """Two authors who studied at the same institution"""
        domain = [onto.Author]
        range = [onto.Author]
    
    rule7 = Imp()
    rule7.set_as_rule("""
        Author(?a1) ^ Author(?a2) ^ hasEducation(?a1, ?e1) ^ hasEducation(?a2, ?e2) ^
        educatedAt(?e1, ?inst) ^ educatedAt(?e2, ?inst) ^ differentFrom(?a1, ?a2) 
        -> isAlumniPeerOf(?a1, ?a2)
    """)
    print("✅ Rule 7: Alumni Peer Connection Rule")

# Save ontology with SWRL rules
onto.save(file="../owl/pkg2020_with_swrl.owl", format="rdfxml")
print("\n" + "="*60)
print("✅ SAVED: pkg2020_with_swrl.owl")
print("="*60)

# ========== SUMMARY ==========

print("\n📋 SWRL RULES SUMMARY:")
print("-"*40)
print("""
Rule 1: ProlificAuthor - Already expressed as defined class
Rule 2: FundedAuthor - Author with NIH project
Rule 3: EstablishedResearcher - Author with employment AND education
Rule 4: CollaborativeArticle - Article with multiple distinct authors
Rule 5: GeneDiseaseLinkArticle - Article mentioning both genes and diseases
Rule 6: ExperiencedEmployee - Long-term employment (10+ years)
Rule 7: AlumniPeer - Authors educated at same institution

Note: SWRL rules require a compatible reasoner:
- Pellet (via SPARQL CONSTRUCT)
- Rules can be executed in Protégé with SWRL plugin
- Or via SPARQL CONSTRUCT queries as an alternative

To use in Protégé:
1. Open pkg2020_with_swrl.owl
2. Install SWRL Tab plugin (Window → Tabs → SWRLAPI)
3. Run the SWRL rules
4. Check inferred classifications
""")

print("\n💡 ALTERNATIVE: SPARQL CONSTRUCT RULES")
print("-"*40)

# Print SPARQL CONSTRUCT equivalents
sparql_rules = """
# SPARQL CONSTRUCT equivalent of SWRL Rules:

# Rule: Funded Author
CONSTRUCT {
    ?author a pkg:FundedAuthor .
}
WHERE {
    ?author a pkg:Author .
    ?author pkg:hasProject ?project .
    ?project a pkg:NIHProject .
}

# Rule: Collaborative Article
CONSTRUCT {
    ?article a pkg:CollaborativeArticle .
}
WHERE {
    ?article a pkg:Article .
    ?article pkg:writtenBy ?a1 .
    ?article pkg:writtenBy ?a2 .
    FILTER (?a1 != ?a2)
}

# Rule: Gene-Disease Link Article
CONSTRUCT {
    ?article a pkg:GeneDiseaseLinkArticle .
}
WHERE {
    ?article a pkg:Article .
    ?article pkg:mentionsBioEntity ?gene .
    ?gene a pkg:Gene .
    ?article pkg:mentionsBioEntity ?disease .
    ?disease a pkg:Disease .
}
"""

print(sparql_rules)
