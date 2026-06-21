# Record Harm Ontology

A formal OWL 2 DL ontology for modeling ontological attacks on informational records.

[![Version](https://img.shields.io/badge/version-2.3-blue.svg)](ontology/record-harm-ontology.ttl)
[![OWL 2 DL](https://img.shields.io/badge/OWL-2%20DL-green.svg)](https://www.w3.org/TR/owl2-overview/)
[![SHACL](https://img.shields.io/badge/SHACL-validated-green.svg)](shapes/record-harm-shapes.ttl)

> **OWL 2 DL note:** `ex:buildsUpon` is asymmetric and irreflexive and is used in `ex:CompositeHarm`'s cardinality-based definition, so it is deliberately **not** declared transitive — a transitive property is "non-simple" in OWL 2 DL and may not be asymmetric/irreflexive or appear in cardinality restrictions. Transitive dependency chains are computed on demand with the SPARQL property path `ex:buildsUpon+` (see [docs/QUERIES.md](docs/QUERIES.md)), not materialized by the reasoner. This keeps the ontology inside OWL 2 DL so a conforming reasoner can run the disjointness and CompositeHarm-membership cross-checks.

## Overview

The Record Harm Ontology provides a rigorous taxonomy of how informational records can be damaged, destroyed, or corrupted. It distinguishes between **prime harms** (ontologically irreducible attacks) and **composite harms** (derived from combinations of primes), while also modeling specific harm events and recurring harm patterns.

### Key Features

- **5 Prime Harms**: Destruction, Fabrication, Alteration, Omission, Denial
- **7 Composite Harms**: Built from formal dependencies on prime harms
- **Event Layer**: Model specific occurrences with dates, perpetrators, and severity
- **Pattern Layer**: Capture empirical co-occurrences of independent harms
- **SHACL Validation**: Comprehensive constraint checking separate from OWL reasoning
- **SKOS Vocabularies**: Controlled terms for aspects, detectability, and reversibility

## Use Cases

- **Digital Forensics**: Evidence integrity analysis and chain of custody tracking
- **Records Management**: Archival science and preservation planning
- **Information Security**: Threat modeling and attack surface analysis
- **Legal/Regulatory**: Compliance with record-keeping requirements
- **Misinformation Analysis**: Tracking disinformation campaigns and propaganda
- **Historical Research**: Documenting record manipulation and censorship

## Repository Structure

```
record-harm-ontology/
├── ontology/
│   └── record-harm-ontology.ttl    # Main OWL 2 DL ontology (v2.3)
├── shapes/
│   └── record-harm-shapes.ttl      # SHACL validation constraints
├── examples/
│   └── example-harm-events.ttl     # Worked HarmEvent / Record / Agent data
├── docs/
│   ├── ARCHITECTURE.md             # Design patterns and rationale
│   └── QUERIES.md                  # Example SPARQL queries
├── scripts/
│   └── validate.py                 # Syntax + SHACL validation + metrics
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
└── README.md
```

## Quick Start

### Loading the Ontology

**Python (rdflib)**:
```python
from rdflib import Graph

g = Graph()
g.parse("ontology/record-harm-ontology.ttl", format="turtle")

# Query for all prime harms
query = """
PREFIX ex: <http://example.org/record-harm-ontology#>
SELECT ?harm ?label WHERE {
    ?harm a ex:PrimeHarm ;
          rdfs:label ?label .
}
"""
for row in g.query(query):
    print(f"{row.harm}: {row.label}")
```

**SPARQL Endpoint**:
```sparql
PREFIX ex: <http://example.org/record-harm-ontology#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

# Find all harms targeting Authenticity
SELECT ?harm ?label ?definition WHERE {
    ?harm ex:targetsAspect ex:Authenticity ;
          rdfs:label ?label ;
          skos:definition ?definition .
}
```

### Validating with SHACL

**Python (pyshacl)**:
```python
from pyshacl import validate

data_graph = "path/to/your/data.ttl"
shacl_graph = "shapes/record-harm-shapes.ttl"
ontology_graph = "ontology/record-harm-ontology.ttl"

conforms, results_graph, results_text = validate(
    data_graph,
    shacl_graph=shacl_graph,
    ont_graph=ontology_graph,
    inference='rdfs',
    abort_on_first=False
)

print(f"Conforms: {conforms}")
print(results_text)
```

## Ontology Architecture

### Type Layer (RecordHarm Taxonomy)

The ontology defines 12 harm types organized into two disjoint classes:

**Prime Harms** (ontologically irreducible):
1. **Destruction** - Complete annihilation of the record
2. **Fabrication** - Creation of false records
3. **Alteration** - Modification of existing genuine records
4. **Omission** - Deliberate exclusion of relevant elements
5. **Denial** - Refusing to acknowledge existence/validity

**Composite Harms** (built from primes via `ex:buildsUpon`):
1. **ForgeryOfProvenance** - Falsifying origin/custody (builds on Fabrication + Alteration)
2. **Fragmentation** - Breaking records into disconnected pieces (builds on Omission)
3. **Suppression** - Preventing access/circulation (builds on Omission)
4. **Obfuscation** - Making records difficult to understand (builds on Suppression)
5. **Decontextualization** - Stripping metadata/context (builds on Omission)
6. **Contamination** - Mixing genuine with fabricated (builds on Fabrication)
7. **Repudiation** - Disavowing authorship/authority (builds on Denial + Fabrication)

### Event Layer (HarmEvent)

Model specific occurrences:
```turtle
ex:exampleDestructionEvent a ex:HarmEvent ;
    ex:ofType ex:Destruction ;
    ex:harms ex:SomeSpecificRecord ;
    dc:date "2026-06-15"^^xsd:date ;
    ex:perpetrator ex:SomeAgent ;
    ex:severity 8 .
```

### Pattern Layer (HarmPattern)

Capture recurring combinations:
```turtle
ex:CoverUpPattern a ex:HarmPattern ;
    rdfs:label "Cover-up" ;
    ex:includesHarm ex:Suppression, ex:Alteration, ex:Denial .
```

## Record Aspects

Every harm targets one or more of six fundamental aspects:

- **Existence** - The record's being or presence
- **Authenticity** - Genuine link to claimed origin/content
- **Integrity** - Wholeness and completeness
- **Accessibility** - Discoverability and comprehension
- **Context** - Provenance and surrounding circumstances
- **Trustworthiness** - Reliability and legitimacy

## Validation Rules (SHACL)

The ontology includes comprehensive SHACL shapes that enforce:

- Prime harms must have zero `buildsUpon` edges
- Composite harms must have at least one `buildsUpon` edge
- Every harm must target at least one aspect
- Every harm must be classified as exactly one of Prime/Composite
- Harm events must reference exactly one harm type
- Severity values must be integers 1-10
- Detectability/reversibility must use controlled vocabulary terms

## Version History

### v2.3 (Current)
- **OWL 2 DL profile fix**: removed `owl:TransitiveProperty` from `ex:buildsUpon`. Transitivity is incompatible with the property also being asymmetric, irreflexive, and used in a cardinality restriction (all forbidden for "non-simple" properties in OWL 2 DL); v2.0–v2.2 were therefore OWL 2 Full despite the DL claim. Transitive closure remains available via the `ex:buildsUpon+` SPARQL path.

### v2.2
- Added HarmEvent class for modeling specific occurrences
- Added HarmPattern class for empirical co-occurrences
- Introduced controlled vocabularies for detectability/reversibility
- Added inverse property `isBuiltUponBy`
- Separated SHACL shapes into companion file
- Added worked examples

### v2.1
- Promoted Denial from CompositeHarm to 5th PrimeHarm
- Added SKOS typing to all harm instances
- Added `rdfs:isDefinedBy` to all harms

### v2.0
- Replaced boolean flags with disjoint OWL classes
- Made `buildsUpon` transitive, asymmetric, irreflexive
- Promoted RecordAspect to proper SKOS vocabulary
- Eliminated duplicate aspect-subclasses

### v1.0
- Initial release with 4 prime harms
- Basic taxonomy structure

## Contributing

This ontology is part of the broader "thought framework" project exploring philosophical approaches to information integrity. Contributions welcome via:

1. Issue reports for conceptual inconsistencies
2. Pull requests for new harm types or patterns
3. Example data demonstrating real-world applications
4. Documentation improvements

## License

MIT License — Copyright (c) 2026 Ron Hinchley. See [LICENSE](LICENSE).

## Citation

If you use this ontology in academic work, please cite:

```bibtex
@misc{recordharmontology2026,
  title={Record Harm Ontology: A Formal Model of Ontological Attacks on Information},
  author={Hinchley, Ron},
  year={2026},
  version={2.3},
  url={https://github.com/commuted/record-harm-ontology}
}
```

## Contact

- **Project**: Part of the thought framework collection
- **Repository**: https://github.com/commuted/record-harm-ontology
- **Issues**: https://github.com/commuted/record-harm-ontology/issues

## Related Work

- **Unified Record Thesis** - Philosophical foundation for comprehensive record-keeping
- **AI Ethics Framework** - Single-party reconciliation through escalation analysis
- **Thought Escalation Plugin** - Conflict analysis and permanent front mapping

## Technical Requirements

- **RDF Library**: rdflib (Python), Apache Jena (Java), or similar
- **SHACL Validator**: pyshacl, Apache Jena SHACL, or TopBraid
- **OWL Reasoner** (optional): HermiT, Pellet, or ELK for DL inference
- **SPARQL Endpoint** (optional): Fuseki, Virtuoso, or GraphDB

## Acknowledgments

Conceptual modeling by Grok; ontology engineering and SHACL validation by Claude (Anthropic); philosophical framework development through extended dialogue in the thought framework project.
