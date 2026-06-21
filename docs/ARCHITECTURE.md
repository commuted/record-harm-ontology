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

### 3. Transitive Dependency Chain

**Pattern**: Composite harms transitively depend on all primes beneath them

**Implementation**:
```turtle
ex:buildsUpon a owl:TransitiveProperty .
```

**Rationale**: If Obfuscation builds on Suppression, and Suppression builds on Omission, then Obfuscation transitively builds on Omission

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
| `buildsUpon` | RecordHarm | RecordHarm | Transitive, Asymmetric, Irreflexive |
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

With a DL reasoner (HermiT, Pellet):

1. **Classification**: Infer CompositeHarm membership from buildsUpon presence
2. **Transitivity**: Compute full dependency chains
3. **Disjointness**: Detect Prime/Composite conflicts
4. **Property chains**: Infer indirect relationships

Example inference:
```sparql
# Asserted: Obfuscation buildsUpon Suppression
# Asserted: Suppression buildsUpon Omission
# Inferred: Obfuscation buildsUpon Omission (transitivity)
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
