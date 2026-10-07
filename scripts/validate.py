#!/usr/bin/env python3
"""
Validation script for Record Harm Ontology

Validates:
1. OWL/Turtle syntax (ontology + examples)
2. OWL 2 DL profile: simple-property rules (regression guard for the
   transitivity-vs-cardinality defect fixed in v2.3)
3. Aspect coverage: every RecordAspect is reachable from a PrimeHarm
   (regression guard for the Accessibility gap fixed in v3.0)
4. SHACL constraint compliance (ontology self-check + examples)
5. Basic ontology metrics
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
# Aspect coverage
# ---------------------------------------------------------------------------

def check_aspect_coverage(g):
    """Every concept in ex:RecordAspectScheme must be targeted by at least one
    ex:PrimeHarm.

    An aspect that only composite harms attack is a structural smell, not a
    neutral fact: every composite bottoms out in primes via ex:buildsUpon, so
    if some aspect is reachable only through composites, one of those
    composites is hanging off a prime that does not actually attack that
    aspect. That is exactly the v3.0 defect -- ex:Accessibility had no prime,
    and ex:Suppression had been given a `buildsUpon ex:Omission` edge that
    contradicted both definitions purely for want of anywhere else to attach.
    Cheap check, and it is what surfaced the bug, so it stays in CI.

    This is a heuristic about ontology shape, not an OWL or SHACL constraint --
    neither language can express it (SHACL could only check it per-aspect with
    a hand-written shape per concept, which would have to be updated by the
    same person who forgot the prime).
    """
    print("\n🔍 Checking aspect coverage (every aspect reachable from a prime)...")
    EX = "http://example.org/record-harm-ontology#"
    q = f"""PREFIX ex: <{EX}>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        SELECT ?aspect WHERE {{
          ?aspect skos:inScheme ex:RecordAspectScheme .
          FILTER NOT EXISTS {{ ?h a ex:PrimeHarm ; ex:targetsAspect ?aspect }}
        }}"""
    uncovered = [_short(r[0]) for r in g.query(q)]
    if uncovered:
        print("❌ Aspects targeted by no PrimeHarm:")
        for a in sorted(uncovered):
            print(f"   - {a}  (a composite is probably rooted in the wrong prime)")
        return False
    print("✅ Every RecordAspect is targeted by at least one PrimeHarm")
    return True


# ---------------------------------------------------------------------------
# SHACL
# ---------------------------------------------------------------------------

def validate_shacl(label, data_graph, shacl_graph, ont_graph):
    """Validate a data graph against SHACL shapes, in TWO passes.

    [v3.1] Both passes are necessary, and running only the first (as every
    version through v3.0 did) left some shapes nominally green while testing
    nothing:

    - inference="rdfs": RDFS entailment on, so sh:class checks resolve typing
      that follows from subclass axioms. This is how a real consumer loads the
      graph.
    - inference="none": no entailment. Needed because the ontology declares
      rdfs:domain/rdfs:range on its properties, and under RDFS those axioms
      MANUFACTURE the very typing that the type-asserting shapes exist to
      check. ex:BuildsUponEndpointTypeShape says it "catches a node that uses
      buildsUpon but was never given any RecordHarm typing" -- but with RDFS
      on, ex:buildsUpon's domain/range silently types that node as a
      RecordHarm, so the shape cannot fail. Verified: an untyped node using
      ex:buildsUpon passes the rdfs pass and is reported, misleadingly, by the
      aspect and classification shapes instead; it fails the correct shape with
      the correct message only when inference is off. Same applies to
      ex:RecordShape's sh:class on ex:hasElement.

    A violation in either pass fails the run.
    """
    if not HAVE_PYSHACL:
        print(f"\n⚠️  pyshacl not installed -- skipping SHACL for {label} "
              f"(pip install pyshacl)")
        return True

    ok = True
    for inference in ("rdfs", "none"):
        print(f"\n🔍 Validating SHACL constraints: {label} (inference={inference}) ...")
        conforms, _results_graph, results_text = _shacl_validate(
            data_graph,
            shacl_graph=shacl_graph,
            ont_graph=ont_graph,
            inference=inference,
            abort_on_first=False,
            allow_warnings=True,
        )
        if conforms:
            print(f"✅ {label} (inference={inference}): all SHACL constraints satisfied")
        else:
            print(f"❌ {label} (inference={inference}): SHACL validation failed:")
            print(results_text)
            ok = False
    return ok


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
    ok &= check_aspect_coverage(ont_graph)
    # Ontology self-check: the worked examples + harm types live in this graph.
    ok &= validate_shacl("ontology", ont_graph, shapes_graph, ont_graph)

    # Examples: validate them MERGED WITH the ontology, not standalone. The
    # example data references ontology individuals (ofType -> harm types, etc.),
    # and the shapes target ex:RecordHarm; validating the examples alone would
    # target those harm types without their full definitions and report false
    # violations. A real consumer loads both graphs together, so we do too.
    if examples_path.exists():
        ex_graph = validate_syntax(examples_path)
        ok &= validate_shacl("ontology + examples", ont_graph + ex_graph,
                             shapes_graph, ont_graph)
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
