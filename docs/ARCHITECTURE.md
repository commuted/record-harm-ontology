# Record Harm Ontology Architecture

## Overview

The Record Harm Ontology is structured as a multi-layered knowledge graph using OWL 2 DL with SHACL validation. This document explains the architectural decisions and design patterns.

## Layer Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Application Layer                      │
│  (Queries, Reasoning, Validation, Visualization)        │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                   Pattern Layer                          │
│  HarmPattern: Empirical co-occurrences                  │
│  (e.g., CoverUpPattern)                                 │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                   Event Layer (ABox)                     │
│  HarmEvent: Specific occurrences                        │
│  - ofType → harm type                                   │
│  - harms → specific Record                              │
│  - perpetrator, date, severity                          │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                   Type Layer (TBox)                      │
│  RecordHarm taxonomy:                                   │
│  - PrimeHarm (5 types)                                  │
│  - CompositeHarm (7 types)                              │
│  - buildsUpon dependencies                              │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                   Aspect Layer                           │
│  RecordAspectScheme (SKOS vocabulary):                  │
│  Existence, Authenticity, Integrity,                    │
│  Accessibility, Context, Trustworthiness                │
└─────────────────────────────────────────────────────────┘
```

## Design Patterns

### 1. Type/Instance Separation (TBox/ABox)

**Pattern**: Separate harm TYPES from harm EVENTS

**Implementation**:
- `RecordHarm` instances are types (universals)
- `HarmEvent` instances are occurrences (particulars)
- `ex:ofType` links events to types

**Rationale**: Prevents confusion between "what Destruction is" vs "this specific destruction that happened"

### 2. Disjoint Class Hierarchy

**Pattern**: Prime and Composite harms are mutually exclusive

**Implementation**:
```turtle
ex:PrimeHarm owl:disjointWith ex:CompositeHarm .
```

**Rationale**: Reasoner can detect classification errors; a harm cannot be both prime and composite

### 3. Dependency Chain (closure computed, not asserted)

**Pattern**: Composite harms transitively depend on all primes beneath them — but the transitive *closure* is computed on demand, not materialized by the reasoner.

**Implementation**:
```sparql
# ex:buildsUpon is intentionally NOT owl:TransitiveProperty (see note below).
# Walk the chain with a property path instead:
SELECT ?prime WHERE { ex:Obfuscation ex:buildsUpon+ ?prime }
```

**Rationale**: If Obfuscation builds on Suppression and Suppression builds on Omission, then Obfuscation transitively builds on Omission. `ex:buildsUpon+` derives this at query time.

**Why not `owl:TransitiveProperty`?** A transitive property is "non-simple" in OWL 2 DL, and OWL 2 DL forbids non-simple properties from being declared asymmetric or irreflexive, or from being used in cardinality restrictions. `ex:buildsUpon` is all three (asymmetric, irreflexive, and the basis of `ex:CompositeHarm`'s cardinality definition), so declaring it transitive would push the ontology into OWL 2 Full and a conforming DL reasoner would refuse the CompositeHarm definition. Keeping it simple preserves both the cycle guards and reasoner-derivable classification. *(Fixed in v2.3; v2.0–v2.2 had this defect.)*

### 4. Controlled Vocabularies (SKOS)

**Pattern**: Use SKOS ConceptSchemes for enumerated values

**Implementation**:
- `RecordAspectScheme`: 6 aspects
- `DetectabilityScheme`: 3 levels
- `ReversibilityScheme`: 3 levels

**Rationale**: Prevents string chaos ("Easy" vs "easy" vs "kinda hard"); enables reliable querying

### 5. Dual Validation Strategy

**Pattern**: OWL axioms + SHACL shapes

**Implementation**:
- OWL: Open-world reasoning (what CAN be inferred)
- SHACL: Closed-world validation (what MUST be present)

**Rationale**: OWL alone can't enforce "every CompositeHarm must have buildsUpon" in closed-world sense; SHACL fills this gap

## Property Design

### Object Properties

| Property | Domain | Range | Characteristics |
|----------|--------|-------|-----------------|
| `harms` | RecordHarm ∪ HarmEvent | Record | - |
| `ofType` | HarmEvent | RecordHarm | Functional (cardinality 1) |
| `buildsUpon` | RecordHarm | RecordHarm | Asymmetric, Irreflexive (not transitive — see Pattern 3) |
| `isBuiltUponBy` | RecordHarm | RecordHarm | Inverse of buildsUpon |
| `targetsAspect` | RecordHarm | skos:Concept | Multi-valued |
| `includesHarm` | HarmPattern | RecordHarm | Multi-valued (min 2) |
| `perpetrator` | HarmEvent | owl:Thing | Multi-valued |
| `detectability` | RecordHarm | skos:Concept | Single-valued |
| `reversibility` | RecordHarm | skos:Concept | Single-valued |

### Datatype Properties

| Property | Domain | Range | Constraints |
|----------|--------|-------|-------------|
| `severity` | HarmEvent | xsd:integer | 1-10 (SHACL enforced) |

## Reasoning Capabilities

### OWL Reasoning

With a DL reasoner (HermiT, Pellet, ELK):

1. **Classification**: Infer CompositeHarm membership from buildsUpon presence
2. **Disjointness**: Detect Prime/Composite conflicts
3. **Asymmetry/irreflexivity**: Detect a harm that builds upon itself or directly back upon a dependant

These hold only because the ontology stays within OWL 2 DL (see Pattern 3). Transitive dependency chains are **not** a reasoner capability here — `ex:buildsUpon` is not transitive — they are computed with the SPARQL property path:
```sparql
# Asserted: Obfuscation buildsUpon Suppression; Suppression buildsUpon Omission
# Query:    ex:Obfuscation ex:buildsUpon+ ?x  ->  Suppression, Omission
```

### SHACL Validation

Closed-world checks:

1. **Cardinality**: Exactly one ofType per HarmEvent
2. **Range**: Severity must be 1-10
3. **Membership**: Detectability must be from controlled vocabulary
4. **Consistency**: Every RecordHarm is exactly one of Prime/Composite

## Extension Points

### Adding New Harm Types

1. **Determine classification**: Prime or Composite?
2. **If Prime**: Add as direct instance of `ex:PrimeHarm`
3. **If Composite**: Add `ex:buildsUpon` edges to dependencies
4. **Add aspects**: Use `ex:targetsAspect` to link to aspects
5. **Add soft properties**: Set detectability/reversibility
6. **Update SHACL**: Add any new constraints

### Adding New Aspects

1. Add to `RecordAspectScheme` as `skos:Concept`
2. Update documentation
3. Review existing harms for applicability

### Adding New Properties

1. Define in ontology with clear domain/range
2. Add SHACL shape if constraints needed
3. Seed existing instances with values
4. Document in this file

## Performance Considerations

### Query Optimization

- **Use property paths sparingly**: `buildsUpon+` can be expensive
- **Materialize transitive closure**: For large datasets, pre-compute
- **Index aspects**: Common join point for queries

### Reasoning Trade-offs

- **Full DL reasoning**: Expensive but complete
- **RDFS reasoning**: Fast but limited
- **No reasoning**: Fastest but requires explicit assertions

Recommendation: Use RDFS reasoning for most queries, full DL for validation

## Integration Patterns

### With PROV-O

```turtle
ex:HarmEvent rdfs:subClassOf prov:Activity .
ex:Record rdfs:subClassOf prov:Entity .
ex:perpetrator rdfs:subPropertyOf prov:wasAssociatedWith .
```

### With FOAF

```turtle
ex:perpetrator rdfs:range foaf:Agent .
```

### With Dublin Core

Already integrated:
- `dc:created` for record creation dates
- `dc:date` for harm event dates
- `dc:description` for annotations

## Versioning Strategy

- **Ontology version**: In `owl:versionInfo`
- **Backward compatibility**: Maintain for minor versions
- **Breaking changes**: Require major version bump
- **Deprecation**: Use `owl:deprecated true` before removal

## Testing Strategy

1. **Syntax validation**: RDF parsing
2. **SHACL validation**: Constraint checking
3. **Reasoning tests**: Expected inferences
4. **Query tests**: SPARQL result verification
5. **Example validation**: Real-world data conformance

See `scripts/validate.py` for automated checks.
