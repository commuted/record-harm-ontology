#!/usr/bin/env python3
"""
Validation script for Record Harm Ontology

Validates:
1. OWL syntax and consistency
2. SHACL constraint compliance
3. Basic ontology metrics
"""

import sys
from pathlib import Path
from rdflib import Graph
from pyshacl import validate

def load_graph(file_path, format="turtle"):
    """Load an RDF graph from file."""
    g = Graph()
    try:
        g.parse(file_path, format=format)
        return g
    except Exception as e:
        print(f"❌ Error loading {file_path}: {e}")
        sys.exit(1)

def validate_syntax(ontology_path):
    """Validate RDF/Turtle syntax."""
    print("🔍 Validating RDF syntax...")
    g = load_graph(ontology_path)
    print(f"✅ Syntax valid: {len(g)} triples loaded")
    return g

def validate_shacl(data_graph, shacl_graph, ont_graph=None):
    """Validate data against SHACL shapes."""
    print("\n🔍 Validating SHACL constraints...")
    
    conforms, results_graph, results_text = validate(
        data_graph,
        shacl_graph=shacl_graph,
        ont_graph=ont_graph,
        inference='rdfs',
        abort_on_first=False,
        allow_warnings=True
    )
    
    if conforms:
        print("✅ All SHACL constraints satisfied")
    else:
        print("❌ SHACL validation failed:")
        print(results_text)
        return False
    
    return True

def print_metrics(g):
    """Print basic ontology metrics."""
    print("\n📊 Ontology Metrics:")
    
    # Count classes
    classes_query = """
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    SELECT (COUNT(DISTINCT ?class) as ?count) WHERE {
        ?class a owl:Class .
    }
    """
    class_count = list(g.query(classes_query))[0][0]
    print(f"   Classes: {class_count}")
    
    # Count properties
    props_query = """
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    SELECT (COUNT(DISTINCT ?prop) as ?count) WHERE {
        { ?prop a owl:ObjectProperty } UNION
        { ?prop a owl:DatatypeProperty }
    }
    """
    prop_count = list(g.query(props_query))[0][0]
    print(f"   Properties: {prop_count}")
    
    # Count harm instances
    harms_query = """
    PREFIX ex: <http://example.org/record-harm-ontology#>
    SELECT (COUNT(DISTINCT ?harm) as ?count) WHERE {
        ?harm a ex:RecordHarm .
    }
    """
    harm_count = list(g.query(harms_query))[0][0]
    print(f"   Harm Types: {harm_count}")
    
    # Count prime vs composite
    prime_query = """
    PREFIX ex: <http://example.org/record-harm-ontology#>
    SELECT (COUNT(DISTINCT ?harm) as ?count) WHERE {
        ?harm a ex:PrimeHarm .
    }
    """
    prime_count = list(g.query(prime_query))[0][0]
    print(f"   - Prime Harms: {prime_count}")
    
    composite_query = """
    PREFIX ex: <http://example.org/record-harm-ontology#>
    SELECT (COUNT(DISTINCT ?harm) as ?count) WHERE {
        ?harm a ex:CompositeHarm .
    }
    """
    composite_count = list(g.query(composite_query))[0][0]
    print(f"   - Composite Harms: {composite_count}")

def main():
    """Main validation routine."""
    # Determine paths
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    
    ontology_path = repo_root / "ontology" / "record-harm-ontology.ttl"
    shapes_path = repo_root / "shapes" / "record-harm-shapes.ttl"
    
    if not ontology_path.exists():
        print(f"❌ Ontology file not found: {ontology_path}")
        sys.exit(1)
    
    if not shapes_path.exists():
        print(f"❌ SHACL shapes file not found: {shapes_path}")
        sys.exit(1)
    
    print("=" * 60)
    print("Record Harm Ontology Validation")
    print("=" * 60)
    
    # Validate syntax
    ont_graph = validate_syntax(ontology_path)
    
    # Print metrics
    print_metrics(ont_graph)
    
    # Validate SHACL
    shapes_graph = load_graph(shapes_path)
    
    if not validate_shacl(ont_graph, shapes_graph, ont_graph):
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ All validations passed!")
    print("=" * 60)

if __name__ == "__main__":
    main()
