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
│  (CoverUpPattern, MiscontextualizationPattern)          │
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
│  - PrimeHarm (6 types)                                  │
│  - CompositeHarm (6 types)                              │
│  - buildsUpon dependencies                              │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                   Record Layer                           │
│  Record structure (v3.1):                               │
│  - hasElement / elementOf  (mereology)                  │
│  - bearer / bears          (where it resides)           │
│  inside-agent = 1 individual bearer                     │
│  inside-community = many, or 1 collective bearer        │
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

### 2a. Primality Test (what qualifies as a PrimeHarm)

A candidate prime must pass **both** tests:

1. **Irreducibility** — no other harm in the taxonomy reduces it. Checked by
   argument, against the harms' own definitions, not by intuition.
2. **Aspect necessity** — it is the only route to some aspect of the record it
   attacks, i.e. removing it would leave an aspect reachable only through
   composites.

Test 2 is the one that is easy to skip and the one that catches real errors.
Every composite bottoms out in primes via `ex:buildsUpon`, so an aspect
reachable *only* through composites means one of those composites is rooted in
a prime that does not actually attack that aspect — the composite was attached
somewhere plausible-looking for want of a correct parent. That is exactly the
v3.0 defect: `ex:Accessibility` had no prime, and `ex:Suppression` carried a
`buildsUpon ex:Omission` edge that contradicted both definitions (Omission
excludes elements from a record; a suppressed record is complete and
unmodified, and only its channel to an observer is cut).

`scripts/validate.py::check_aspect_coverage` enforces test 2 in CI. Test 1
cannot be automated.

**Corollary on `ex:buildsUpon` semantics**: an edge asserts a *necessary*
presupposition, not a frequent co-occurrence. Harms that merely travel together
belong in `ex:HarmPattern` — which is why the false-context variant of
decontextualization became `ex:MiscontextualizationPattern` rather than a
Fabrication edge on `ex:Decontextualization`, and why `ex:Contamination` keeps a
Fabrication edge alone despite corpus-poisoning often involving alteration too.
One known tension remains: `ex:Repudiation buildsUpon ex:Fabrication`, where a
bare disavowal fabricates nothing. See the note on that instance.

### 3. Dependency Chain (closure computed, not asserted)

**Pattern**: Composite harms transitively depend on all primes beneath them — but the transitive *closure* is computed on demand, not materialized by the reasoner.

**Implementation**:
```sparql
# ex:buildsUpon is intentionally NOT owl:TransitiveProperty (see note below).
# Walk the chain with a property path instead:
SELECT ?prime WHERE { ex:Obfuscation ex:buildsUpon+ ?prime }
```

**Rationale**: a composite that builds on another composite rests on every
prime beneath it, and `ex:buildsUpon+` derives that at query time rather than
having the reasoner materialize it.

**As of v3.0 the dependency graph is flat** — maximum chain depth 1, every
composite depending only on primes. The v2.3 illustration of this pattern
(`Obfuscation → Suppression → Omission`) was the *defect*: that two-hop chain
existed only because `ex:Suppression` had been mis-rooted in `ex:Omission`, and
promoting Suppression to a prime removed the only multi-hop path in the
taxonomy. So `ex:buildsUpon+` currently returns exactly what `ex:buildsUpon`
does. Keep writing the `+` form anyway: it stays correct if a composite-on-composite
dependency is ever added, and the queries in `docs/QUERIES.md` do not change
when it is.

**Why not `owl:TransitiveProperty`?** A transitive property is "non-simple" in OWL 2 DL, and OWL 2 DL forbids non-simple properties from being declared asymmetric or irreflexive, or from being used in cardinality restrictions. `ex:buildsUpon` is all three (asymmetric, irreflexive, and the basis of `ex:CompositeHarm`'s cardinality definition), so declaring it transitive would push the ontology into OWL 2 Full and a conforming DL reasoner would refuse the CompositeHarm definition. Keeping it simple preserves both the cycle guards and reasoner-derivable classification. *(Fixed in v2.3; v2.0–v2.2 had this defect.)*

### 3a. Record Location is a Record Property, Not a Harm Dimension (v3.1)

**Pattern**: where a record lives — inside an agent, inside a community — is
stated on the `ex:Record`, never by adding harm types or aspects.

**Implementation**:
```turtle
ex:WitnessMemory  a ex:Record ; ex:bearer ex:SomeAgent .        # inside-agent
ex:ParishRegister a ex:Record ; ex:bearer ex:SomeCollective ;   # inside-community
                    ex:hasElement ex:SomeSpecificRecord .
```

**Rationale**: the question was whether the agent/community distinction needed
its own harms. It does not — every case lands on an existing prime:

| case | harm |
|---|---|
| forgetting | Destruction |
| confabulated memory | Fabrication |
| self-deception | Denial |
| repression | Suppression |
| testimony kept out of a register | Omission *from that register* |

That last row is the agent→community boundary, and it works because a register
is itself an `ex:Record` whose elements are records (`ex:hasElement`), so
non-admission is exclusion of an element. The six primes are untouched.

**Why mereology was owed regardless**: `ex:Record` was a terminal node through
v3.0 — object of `ex:harms`, subject of nothing. Three harm definitions already
quantified over record structure in prose (`Omission` over "elements",
`Fragmentation` over "pieces", `Suppression` over the channel to "an observer"),
and v3.0's Omission definition went further, asserting that elements include
relations and adjacent metadata. The vocabulary could not express any of it.

**Newly derivable**: self-directed harm, where a `HarmEvent`'s `ex:perpetrator`
is also the `ex:bearer` of the record harmed. No new class or property — it
falls out of the two existing ones meeting.

**Not solved here** (both recorded in the ontology so they are choices, not
oversights): `detectability`/`reversibility` are calibrated to community-borne
records and mislead for inside-agent ones; pure non-creation — witnessing and
recording nothing — stays outside the ontology.

### 4. Controlled Vocabularies (SKOS)

**Pattern**: Use SKOS ConceptSchemes for enumerated values

**Implementation**:
- `RecordAspectScheme`: 6 aspects
- `DetectabilityScheme`: 3 levels
- `ReversibilityScheme`: 3 levels

**Rationale**: Prevents string chaos ("Easy" vs "easy" vs "kinda hard"); enables reliable querying

**Scope note — no Confidentiality aspect**: unauthorized disclosure is not a
RecordHarm in this ontology, so the aspect scheme does *not* map one-to-one
onto STRIDE or the CIA triad (Information Disclosure has no counterpart). A
leaked record is undamaged as a record — it exists, and is authentic, complete,
accessible, contextualized and trustworthy. The injury runs to its subject or
custodian, which is a different ontology.

### 5. Dual Validation Strategy

**Pattern**: OWL axioms + SHACL shapes

**Implementation**:
- OWL: Open-world reasoning (what CAN be inferred)
- SHACL: Closed-world validation (what MUST be present)

**Rationale**: OWL alone can't enforce "every CompositeHarm must have buildsUpon" in closed-world sense; SHACL fills this gap

**[v3.1] SHACL runs in two passes, inference on and off.** The ontology
declares `rdfs:domain`/`rdfs:range` on its properties, so under RDFS entailment
those axioms *manufacture* the typing that the type-asserting shapes exist to
check — `ex:BuildsUponEndpointTypeShape` cannot fail on an untyped node when
inference is on, because `ex:buildsUpon`'s domain types it first; the node is
then reported by the aspect and classification shapes with misleading messages.
Verified empirically in both directions. Versions through v3.0 ran the
inference-on pass only, which is why a shape documented as catching untyped
nodes had never been able to.

Division of labour: `shapes/record-harm-shapes.ttl` constrains **data a
consumer authors** (their records, nesting, bearers, events), while
`scripts/validate.py` holds invariants about the **ontology's own shape** (OWL 2
DL simple-property rules, aspect coverage). A consumer validating their own
graph needs the first and not the second.

## Property Design

### Object Properties

| Property | Domain | Range | Characteristics |
|----------|--------|-------|-----------------|
| `harms` | RecordHarm ∪ HarmEvent | Record | - |
| `hasElement` | Record | Record | Asymmetric, Irreflexive (not transitive — Pattern 3) |
| `elementOf` | Record | Record | Inverse of hasElement |
| `bearer` | Record | owl:Thing | Multi-valued, uncapped |
| `bears` | owl:Thing | Record | Inverse of bearer |
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
# ex:ForgeryOfProvenance ex:buildsUpon+ ?x  ->  Fabrication, Alteration
```
With the v3.0 graph being flat (see Pattern 3), this returns the direct edges;
the property path is what keeps it correct if depth is ever added.

### SHACL Validation

Closed-world checks:

1. **Cardinality**: Exactly one ofType per HarmEvent
2. **Range**: Severity must be 1-10
3. **Membership**: Detectability must be from controlled vocabulary
4. **Consistency**: Every RecordHarm is exactly one of Prime/Composite

### Structural Checks (neither OWL nor SHACL)

`scripts/validate.py` additionally enforces what the two languages cannot
express:

1. **OWL 2 DL simple-property rules** — regression guard for the v2.3 fix.
   Note this guard covers `ex:hasElement` automatically: declaring it
   transitive, which is the obvious thing to want for a part-whole property,
   would be caught as a conflict with its asymmetry and irreflexivity.
2. **Aspect coverage** — every `RecordAspectScheme` concept is targeted by at
   least one `PrimeHarm` (Pattern 2a; regression guard for the v3.0 fix)

Record nesting cycles are checked in the shapes file instead
(`ex:RecordAcyclicShape`, a SPARQL-based constraint), since nesting is consumer
data rather than ontology shape. `ex:hasElement`'s asymmetry and irreflexivity
only cover one- and two-step cycles, and only under a DL reasoner.

SHACL could only express the second as one hand-written shape per aspect
concept, maintained by the same person who would have forgotten the prime.

## Extension Points

### Adding New Harm Types

1. **Determine classification**: Prime or Composite? Apply both primality
   tests in Pattern 2a — irreducibility *and* aspect necessity
2. **If Prime**: Add as direct instance of `ex:PrimeHarm`
3. **If Composite**: Add `ex:buildsUpon` edges to dependencies
4. **Add aspects**: Use `ex:targetsAspect` to link to aspects
5. **Add soft properties**: Set detectability/reversibility
6. **Update SHACL**: Add any new constraints

### Adding a Record Location or Bearer Kind

Do **not** add a harm type or an aspect for it. Location is a property of the
record (Pattern 3a): state it with `ex:bearer`, and if the
individual/collective distinction needs to be machine-readable, type the agent
with `foaf:Group` or `prov:Organization` rather than adding a class here — the
same rule that kept `ex:Agent` from being called `ex:Actor`.

### Adding New Aspects

1. Add to `RecordAspectScheme` as `skos:Concept`
2. Update documentation
3. Review existing harms for applicability
4. Confirm at least one `PrimeHarm` targets it — an aspect only composites can
   attack means a prime is missing (Pattern 2a). `scripts/validate.py` fails
   until this holds.

### Adding New Properties

1. Define in ontology with clear domain/range
2. Add SHACL shape if constraints needed
3. Seed existing instances with values
4. Document in this file

## Performance Considerations

### Query Optimization

- **Use property paths sparingly**: `buildsUpon+` can be expensive (currently
  cheap — the graph is flat, so the path resolves in one hop)
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

### What counts as breaking here

Added because v3.0 was first drafted as a minor bump and should not have been.
For an ontology the breaking changes are not only removals:

| change | breaking? | why |
|---|---|---|
| Moving a harm between `PrimeHarm` and `CompositeHarm` | **Yes** | The two are `owl:disjointWith`, so a consumer asserting the old class gets an inconsistent graph — the equivalent of changing a type signature |
| Removing a `buildsUpon` edge | **Yes** | `PrimeHarmShape`/`CompositeHarmShape` change which data validates, and `buildsUpon+` closures change silently |
| Narrowing a `skos:definition` | **Yes, silently** | Data classified under the dropped sense is now mis-typed with no error anywhere |
| Adding a harm, aspect, property, or shape | No | Nothing previously valid becomes invalid |
| *Widening* a definition or an `rdfs:comment` | No | More things qualify; nothing stops qualifying |
| Seeded `detectability`/`reversibility` value corrections | Judgement | Illustrative values by design (see their notes); treat as breaking if a consumer keys decisions off them |

A major release owes consumers a migration table in `CHANGELOG.md`, not just a
list of what changed.

## Testing Strategy

1. **Syntax validation**: RDF parsing
2. **SHACL validation**: Constraint checking
3. **Reasoning tests**: Expected inferences
4. **Query tests**: SPARQL result verification
5. **Example validation**: Real-world data conformance

See `scripts/validate.py` for automated checks.
