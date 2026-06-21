#!/usr/bin/env python3
"""
Validation script for Record Harm Ontology

Validates:
1. OWL/Turtle syntax (ontology + examples)
2. OWL 2 DL profile: simple-property rules (regression guard for the
   transitivity-vs-cardinality defect fixed in v2.3)
3. SHACL constraint compliance (ontology self-check + examples)
4. Basic ontology metrics
"""

import sys
from pathlib import Path
from rdflib import Graph
from rdflib.namespace import OWL, RDF, RDFS

try:
    from pyshacl import validate as _shacl_validate
    HAVE_PYSHACL = True
except ImportError:
    HAVE_PYSHACL = False


def _short(uri):
    s = str(uri)
    return s.rsplit("#", 1)[-1] if "#" in s else s.rsplit("/", 1)[-1]


def load_graph(file_path, format="turtle"):
    """Load an RDF graph from file."""
    g = Graph()
    try:
        g.parse(file_path, format=format)
        return g
    except Exception as e:
        print(f"❌ Error loading {file_path}: {e}")
        sys.exit(1)


def validate_syntax(path):
    """Validate RDF/Turtle syntax and return the parsed graph."""
    print(f"🔍 Validating RDF syntax: {path.name} ...")
    g = load_graph(path)
    print(f"✅ Syntax valid: {len(g)} triples loaded")
    return g


# ---------------------------------------------------------------------------
# OWL 2 DL profile check (targeted)
# ---------------------------------------------------------------------------

_CARDINALITY_PREDS = (
    OWL.cardinality, OWL.minCardinality, OWL.maxCardinality,
    OWL.qualifiedCardinality, OWL.minQualifiedCardinality, OWL.maxQualifiedCardinality,
)

_FORBIDDEN_ON_NONSIMPLE = {
    OWL.AsymmetricProperty: "asymmetric",
    OWL.IrreflexiveProperty: "irreflexive",
    OWL.FunctionalProperty: "functional",
    OWL.InverseFunctionalProperty: "inverse-functional",
}


def _non_simple_properties(g):
    """Object properties that are 'non-simple' in OWL 2 DL: those declared
    owl:TransitiveProperty, plus any super-property of a non-simple property
    (non-simplicity propagates up rdfs:subPropertyOf). Property chains also make
    a super-property non-simple; this ontology declares none, and that case is
    not covered here -- see the scope note in check_owl_profile()."""
    non_simple = set(g.subjects(RDF.type, OWL.TransitiveProperty))
    changed = True
    while changed:
        changed = False
        for sub, sup in g.subject_objects(RDFS.subPropertyOf):
            if sub in non_simple and sup not in non_simple:
                non_simple.add(sup)
                changed = True
    return non_simple


def check_owl_profile(g):
    """Targeted OWL 2 DL check: a non-simple property MUST NOT be declared
    asymmetric / irreflexive / (inverse-)functional, used in a cardinality
    restriction, or used in property disjointness. Violating this silently
    pushes the ontology into OWL 2 Full -- exactly the v2.0-v2.2 defect where
    ex:buildsUpon was transitive *and* asymmetric/irreflexive *and* the basis of
    ex:CompositeHarm's cardinality definition.

    This is a focused regression guard, NOT a complete OWL 2 DL profile
    validator (full conformance needs the OWL API or a DL reasoner). It catches
    the realistic DL-Full traps for an ontology of this shape.
    """
    print("\n🔍 Checking OWL 2 DL profile (simple-property rules)...")
    non_simple = _non_simple_properties(g)
    violations = []

    for p in non_simple:
        for rdf_type, name in _FORBIDDEN_ON_NONSIMPLE.items():
            if (p, RDF.type, rdf_type) in g:
                violations.append(f"{_short(p)} is non-simple (transitive) but declared {name}")

    for restr in g.subjects(RDF.type, OWL.Restriction):
        on_prop = g.value(restr, OWL.onProperty)
        if on_prop in non_simple and any((restr, cp, None) in g for cp in _CARDINALITY_PREDS):
            violations.append(f"{_short(on_prop)} is non-simple but used in a cardinality restriction")

    for s, o in g.subject_objects(OWL.propertyDisjointWith):
        for p in (s, o):
            if p in non_simple:
                violations.append(f"{_short(p)} is non-simple but used in owl:propertyDisjointWith")

    if violations:
        print("❌ OWL 2 DL profile violations:")
        for v in sorted(set(violations)):
            print(f"   - {v}")
        return False
    print("✅ No simple-property OWL 2 DL violations detected")
    return True


# ---------------------------------------------------------------------------
# SHACL
# ---------------------------------------------------------------------------

def validate_shacl(label, data_graph, shacl_graph, ont_graph):
    """Validate a data graph against SHACL shapes (ontology supplied for
    inference so sh:class checks resolve harm-type/Record/Agent typing)."""
    print(f"\n🔍 Validating SHACL constraints: {label} ...")
    if not HAVE_PYSHACL:
        print("⚠️  pyshacl not installed -- skipping SHACL (pip install pyshacl)")
        return True
    conforms, _results_graph, results_text = _shacl_validate(
        data_graph,
        shacl_graph=shacl_graph,
        ont_graph=ont_graph,
        inference="rdfs",
        abort_on_first=False,
        allow_warnings=True,
    )
    if conforms:
        print(f"✅ {label}: all SHACL constraints satisfied")
        return True
    print(f"❌ {label}: SHACL validation failed:")
    print(results_text)
    return False


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def print_metrics(g):
    """Print basic ontology metrics."""
    print("\n📊 Ontology Metrics:")
    EX = "http://example.org/record-harm-ontology#"
    OWLNS = "http://www.w3.org/2002/07/owl#"

    def count(where):
        q = (f"PREFIX owl: <{OWLNS}> PREFIX ex: <{EX}> "
             f"SELECT (COUNT(DISTINCT ?x) AS ?n) WHERE {{ {where} }}")
        return list(g.query(q))[0][0]

    metrics = [
        ("Classes", "?x a owl:Class"),
        ("Properties", "{ ?x a owl:ObjectProperty } UNION { ?x a owl:DatatypeProperty }"),
        ("Harm Types", "?x a ex:RecordHarm"),
        ("- Prime Harms", "?x a ex:PrimeHarm"),
        ("- Composite Harms", "?x a ex:CompositeHarm"),
    ]
    for label, where in metrics:
        print(f"   {label}: {count(where)}")


def main():
    """Main validation routine."""
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent

    ontology_path = repo_root / "ontology" / "record-harm-ontology.ttl"
    shapes_path = repo_root / "shapes" / "record-harm-shapes.ttl"
    examples_path = repo_root / "examples" / "example-harm-events.ttl"

    if not ontology_path.exists():
        print(f"❌ Ontology file not found: {ontology_path}")
        sys.exit(1)
    if not shapes_path.exists():
        print(f"❌ SHACL shapes file not found: {shapes_path}")
        sys.exit(1)

    print("=" * 60)
    print("Record Harm Ontology Validation")
    print("=" * 60)

    ont_graph = validate_syntax(ontology_path)
    print_metrics(ont_graph)
    shapes_graph = load_graph(shapes_path)

    ok = True
    ok &= check_owl_profile(ont_graph)
    # Ontology self-check: the worked examples + harm types live in this graph.
    ok &= validate_shacl("ontology", ont_graph, shapes_graph, ont_graph)

    # Examples: validate the standalone data file against the shapes, with the
    # ontology supplied as ont_graph so sh:class (ofType→RecordHarm, harms→Record)
    # resolves across the file boundary.
    if examples_path.exists():
        ex_graph = validate_syntax(examples_path)
        ok &= validate_shacl("examples", ex_graph, shapes_graph, ont_graph)
    else:
        print(f"\n⚠️  Examples file not found, skipping: {examples_path}")

    print("\n" + "=" * 60)
    if ok:
        print("✅ All validations passed!")
        print("=" * 60)
    else:
        print("❌ Validation failed (see above)")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
