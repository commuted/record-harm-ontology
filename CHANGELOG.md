# Changelog

All notable changes to the Record Harm Ontology will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **Relicensed** from MIT to **CC BY 4.0** for the ontology and documentation,
  with the scripts additionally under the **MIT License**. Aligns with the
  epistemic-ontology.net family (CC BY 4.0 is the standard content license for an
  ontology). Attribution: "Record Harm Ontology — epistemic-ontology.net".
  `dc:license` now declared in the ontology header.

## [3.1.0] - 2026-10-06

Record-side structure, prompted by the question of where a record is located —
inside an agent, or inside a community. The answer turned out to need no new
harm type; it needed `ex:Record` to stop being a terminal node.

### Added
- **`ex:hasElement` / `ex:elementOf`** — mereology for records, aligned upward
  to `dcterms:hasPart` / `dcterms:isPartOf` rather than reusing those terms
  directly, so domain/range sit on local properties and a merged graph's other
  uses of `dcterms:hasPart` are not retroactively constrained to Records.
  Asymmetric and irreflexive, deliberately **not** transitive — the v2.3
  precedent exactly: transitivity makes a property non-simple in OWL 2 DL and
  forbids the cycle guards, which matter more here than materialized nesting
  since a record containing itself is the error worth catching. Nesting is
  walked with `ex:hasElement+`.
- **`ex:bearer` / `ex:bears`** — the agent in or by which a record resides.
  Multi-valued, uncapped, range left open on the `ex:perpetrator` precedent.
  The inside-agent / inside-community distinction falls out of this one
  property: one individual bearer is inside-agent (a memory, a belief, a
  private ledger); many bearers, or one collective bearer, is inside-community.
  No class split and no new aspect.
- **Self-directed harm is newly expressible**: a `HarmEvent` whose
  `ex:perpetrator` is also the `ex:bearer` of the record it harms. Repression,
  self-deception and motivated forgetting had no representation in any earlier
  version. Worked example (`ex:exampleRepressionEvent`) and query added.
- **`ex:RecordShape`** (elements of a record must be records; bearer uncapped
  and documented) and **`ex:RecordAcyclicShape`**, a SPARQL-based constraint
  catching a record nested inside itself at any depth — `ex:hasElement`'s
  asymmetry and irreflexivity cover one and two steps only, and only under a
  DL reasoner.
- Worked examples for the inside-agent (`ex:WitnessMemory`) and
  inside-community (`ex:ParishRegister`) cases, deliberately *not* linked to
  each other: admitting the memory to the register would be attestation,
  keeping it out is `ex:Omission` from the register. Plus `ex:SomeCollective`
  as a collective `ex:Agent`.
- Four queries in `docs/QUERIES.md`: bearer counts, self-directed harm, nesting
  via `ex:hasElement+`, and the agent→community boundary (what a register
  leaves out).

### Fixed
- **SHACL validation now runs in two passes, with RDFS inference on and off.**
  The ontology declares `rdfs:domain`/`rdfs:range` on its properties, so under
  RDFS entailment those axioms *manufacture* the very typing that the
  type-asserting shapes exist to check. `ex:BuildsUponEndpointTypeShape` is
  documented as catching "a node that uses buildsUpon but was never given any
  RecordHarm typing" — it could never do so, because `ex:buildsUpon`'s domain
  types the node first; the error surfaced instead through the aspect and
  classification shapes with misleading messages. Verified in both directions:
  an untyped node using `ex:buildsUpon` fails the correct shape with the
  correct message only when inference is off. Versions through v3.0 ran the
  inference-on pass only. The same vacuity would have applied to
  `ex:RecordShape`'s new `sh:class` check.
- **`ex:Record`'s definition widened.** "Any informational artifact" excluded
  memories, beliefs and internal ledgers by the word *artifact*, though the
  harm definitions never did — forgetting is `ex:Destruction`, confabulation
  `ex:Fabrication`, repression `ex:Suppression`, with no change to any of them.

### Changed
- **`ex:Accessibility` documented as observer-RELATIVE**, which v3.0 had
  already implicitly relied on when it promoted `ex:Suppression` to a prime on
  the strength of the record↔observer channel while the ontology contained no
  observer. Corollary now stated: a private memory is not a suppressed record —
  suppression requires access to be severed from a party who would otherwise
  have it, which is a claim about a *change* in the bearer configuration, not
  about the configuration itself.
- `ex:Agent`'s comment notes that it covers collective agents (community,
  institution, court), which is what lets `ex:bearer` carry the
  inside-community case. No `ex:Collective` subclass declared: there is no
  single cross-vocabulary standard name (`foaf:Group`, `prov:Organization`,
  `schema:Organization` all differ), and inventing one would break the naming
  rule that gave `ex:Agent` its name in v2.3.
- `docs/ARCHITECTURE.md`: new Record Layer in the stack diagram, Pattern 3a
  (location is a record property, not a harm dimension), property-table rows,
  and an extension-point rule — do not add a harm or an aspect for a new
  location or bearer kind.

### Documented rather than fixed
Both are recorded in the ontology itself so they stand as choices:
- **`ex:detectability` / `ex:reversibility` are calibrated to community-borne
  records.** `ex:Denial` is `EasilyDetectable` — true of a record in a shared
  register that can be pointed at, false of an agent denying its own memory,
  which no one can audit. `ex:Destruction` is `Irreversible` — right inside an
  agent, where forgetting is total, overstated for a redundantly held community
  record. Expressing this properly needs bearer-relative qualified values;
  `ex:severity` escaped the same problem in v2.2 by living on the event rather
  than the type, which is the likely fix.
- **Pure non-creation stays out of scope.** An agent who witnesses an event and
  forms no record harms no record, because there is no record — non-creation is
  not a thirteenth harm. The community-side case is covered and is easily
  conflated with it: where an agent holds a record and it is kept out of a
  register, that register is itself an `ex:Record`, so non-admission is
  `ex:Omission` from it. Deciding the first would require a notion of the
  record that *ought* to exist, which nothing here supplies. Scope boundary
  noted at `ex:RecordHarm`.

## [3.0.0] - 2026-10-06

**BREAKING.** Major bump because `ex:Suppression` changes class across an
`owl:disjointWith` boundary — for an ontology that is the equivalent of
changing a type signature, and it fails a v2.3 consumer's graph in four
distinct ways. See *Migration* below. (Initially drafted as 2.4.0; corrected
before release, since neither this nor 3.1.0 was ever committed or tagged. The
namespace migration previously earmarked for v3.0 moves to v4.0.)

Prime-set correction following a cross-discipline audit of the taxonomy
(STRIDE, InterPARES diplomatics, spoliation doctrine). The audit's central
complaint — that `ex:Suppression buildsUpon ex:Omission` was wrong — held, and
tracing it turned up a structural cause the audit itself did not identify.

### Fixed
- **`ex:Suppression` promoted from `ex:CompositeHarm` to a sixth `ex:PrimeHarm`,
  and its `buildsUpon ex:Omission` edge removed.** The edge was a category error
  on the ontology's own definitions: `ex:Omission` is the exclusion of elements
  that should be part of the record, while a suppressed record is complete,
  unmodified, and fully itself — what is severed is the channel to an observer.
  Nor does Suppression reduce to `ex:Denial`: a classified file is openly
  acknowledged to exist, so the custodian denies nothing and withholds
  everything. Same move and same reasoning as the v2.1 promotion of `ex:Denial`.
  Taxonomy is now **6 primes / 6 composites** (still 12 harm types).
- **Root cause**: no `ex:PrimeHarm` targeted `ex:Accessibility` at all, so
  Suppression had been hung off Omission for want of anywhere else to attach.
  Since every composite bottoms out in primes, an aspect reachable only through
  composites is a reliable signal that some composite is rooted in a prime that
  does not actually attack it. Now a documented primality test
  (`docs/ARCHITECTURE.md`, Pattern 2a) and a CI check.
- **`ex:Decontextualization` was carrying two harms on one edge.** Its
  definition covered both "stripping a record of its context" and "placing it
  in a false context" while asserting only the `ex:Omission` edge that fits the
  first; stripping omits, false placement fabricates. The false-placement
  clause moved to the new `ex:MiscontextualizationPattern`.
- **`ex:Obfuscation` reversibility** corrected `ex:Reversible` →
  `ex:PartiallyReversible`: re-indexing a buried record is achievable, noise
  already mixed into the channel generally is not separable again.

### Added
- **`ex:MiscontextualizationPattern`** (`ex:HarmPattern`): genuine record
  placed in a false context — `ex:Decontextualization` + `ex:Fabrication`. A
  pattern rather than a composite because neither component presupposes the
  other, and the record itself is untouched throughout.
- **`ex:Omission ex:targetsAspect ex:Context`**, and an explicit statement in
  its definition that a record's *elements* include its internal relations,
  ordering, and adjacent metadata — not substantive content alone. Three things
  were already relying on this silently: `ex:Fragmentation buildsUpon
  ex:Omission` (fragmentation leaves every piece byte-intact and removes only
  the binding), `ex:Decontextualization buildsUpon ex:Omission` (provenance and
  timing are adjacent metadata, not content), and the audit's proposed
  "Spurious Association" prime — asserting a false relation between two genuine
  records — which under this commitment is Fabrication of a relational element
  and needs no new prime.
- **`ex:Obfuscation buildsUpon ex:Alteration`** in addition to `ex:Suppression`;
  definition tightened to distinguish a record's *form* (which obfuscation does
  degrade) from its surface *content* (which it need not touch). The audit's
  alternative of rooting Obfuscation in `ex:Contamination` was declined:
  Contamination is itself composite, so it lengthens the chain, and it would
  wrongly imply obfuscation requires fabricated content.
- **Aspect-coverage check** in `scripts/validate.py`
  (`check_aspect_coverage`): every `RecordAspectScheme` concept must be
  targeted by at least one `ex:PrimeHarm`. Expressible in neither OWL nor
  SHACL, and it is the diagnostic that found this release's defect, so it runs
  in CI. Grouped query form documented in `docs/QUERIES.md`.
- **Scope note on confidentiality** at `ex:RecordAspectScheme`: the absence of
  a Confidentiality aspect is deliberate, so this vocabulary does *not* map
  one-to-one onto STRIDE or the CIA triad. A leaked record is undamaged as a
  record; the injury runs to its subject or custodian.

### Changed
- `ex:buildsUpon`'s intended semantics stated explicitly at `ex:CompositeHarm`:
  an edge asserts a **necessary presupposition**, not a frequent co-occurrence.
  Harms that merely travel together belong in `ex:HarmPattern`. Two consequences
  recorded rather than silently applied:
  - `ex:Contamination` keeps `buildsUpon ex:Fabrication` alone. The audit
    proposed adding `ex:Alteration`, which is right for in-record injection but
    wrong for corpus-level mixing, where no record is altered at all —
    Fabrication is the only dependency both variants require.
  - `ex:Repudiation buildsUpon ex:Denial , ex:Fabrication` is left standing with
    a **known tension** noted on the instance: a bare disavowal presupposes no
    fabrication. Dropping the edge would reverse a deliberate v2.1 decision, so
    it is flagged as an open choice rather than silently changed.
- No SHACL changes required: `ex:PrimeHarmShape` already forbids `buildsUpon` on
  a `PrimeHarm`, so the removed Suppression edge is now enforced, not merely
  asserted.

### Migration from 2.3

| what you have | what to do |
|---|---|
| `ex:Suppression a ex:CompositeHarm` asserted in your graph | **Remove it.** It contradicts `ex:PrimeHarm owl:disjointWith ex:CompositeHarm`, so a DL reasoner reports the graph inconsistent — and you do not need one to find it: plain SHACL fails it on `ex:RecordHarmClassificationShape` (`sh:xone` — exactly one of Prime/Composite) and on `ex:CompositeHarmShape` (a composite with no `buildsUpon`). Verified in both inference modes. |
| `ex:Suppression ex:buildsUpon ex:Omission` carried over from 2.3 | **Remove it.** `ex:PrimeHarmShape` forbids any `buildsUpon` on a prime, so this now fails SHACL validation. |
| Queries selecting `?h a ex:CompositeHarm` | Results change — 6 composites, not 7. Suppression now answers `?h a ex:PrimeHarm`. Re-check any count, grouping or report that assumed seven. |
| `ex:Obfuscation ex:buildsUpon+ ?x` | Returns `Suppression, Alteration` instead of `Suppression, Omission`. The Omission root is gone, and the graph is now flat (depth 1). |
| Events classified under `ex:Decontextualization` for *placing a record in a false context* | **Reclassify** to `ex:MiscontextualizationPattern`. That clause was removed from the definition, so such events are now silently mis-typed rather than loudly wrong. |

Nothing else is removed or renamed; all other 2.3 IRIs keep their meaning.

### Notes on the audit's other claims
- Its STRIDE mapping table is unreliable and was not adopted: `Omission ↔
  Information Leak/Gap` inverts the failure (Information Disclosure is a
  confidentiality breach), and `Destruction ↔ Denial of Service` conflates
  terminal loss with transient unavailability.
- Its agreement with `ex:Repudiation ← Denial + Fabrication` and its reading of
  `ex:Denial` as an attestation-layer prime were accepted; its "missing prime"
  candidate was not needed (see `ex:Omission` above).

## [2.3.0] - 2026-06-20

### Added
- **`ex:Agent` class**: the example data typed perpetrators with an undeclared class.
  Declared it as `ex:Agent` — matching the cross-vocabulary standard (`foaf:Agent`,
  `prov:Agent`, `dcterms:Agent`) rather than the original "Actor". A lightweight class
  for agents; `ex:perpetrator`'s range stays open (`owl:Thing`) for FOAF/PROV-O interop.
  The worked example types `ex:SomeAgent`/`ex:UnknownAgent` as `ex:Agent`.

### Fixed
- **OWL 2 DL profile compliance**: removed `owl:TransitiveProperty` from `ex:buildsUpon`.
  Since v2.0 the property was simultaneously transitive, asymmetric, irreflexive, and
  used in `ex:CompositeHarm`'s cardinality-based `owl:equivalentClass`. OWL 2 DL classifies
  a transitive property as "non-simple" and forbids non-simple properties from being
  asymmetric/irreflexive or used in cardinality restrictions, so v2.0–v2.2 were actually
  OWL 2 Full — a conforming DL reasoner (HermiT/Pellet/ELK) would refuse the CompositeHarm
  definition the design relies on. Dropping transitivity restores OWL 2 DL while preserving
  the cycle guards (asymmetric + irreflexive) and reasoner-derivable CompositeHarm membership.

### Changed
- Transitive dependency chains are now obtained via the SPARQL property path `ex:buildsUpon+`
  (already used in `docs/QUERIES.md`) rather than reasoner materialization. No query results change.
- Updated README and `docs/ARCHITECTURE.md` to document the simple-property rationale.
- `ex:ofType` declared `owl:FunctionalProperty` (DL-safe; matches the "exactly one harm type"
  intent and the `ARCHITECTURE.md` description). SHACL `HarmEventShape` remains the hard
  exactly-one check.
- `docs/QUERIES.md`: relabeled "Compute Dependency Depth" → "Count Underlying Prime Harms"
  (it counts distinct primes in the closure, not path depth).
- `scripts/validate.py`: now validates the examples file against the shapes, adds a targeted
  OWL 2 DL simple-property profile check (regression guard for the transitivity defect), and
  degrades gracefully when `pyshacl` is absent.

### Notes
- The base namespace remains the `example.org` placeholder; migrating to a permanent,
  dereferenceable IRI is tracked as a deliberate v4.0 breaking change (see TODO in the ontology).

## [2.2.0] - 2026-06-20

### Added
- **HarmEvent class**: Model specific occurrences of harm types against actual records
  - `ex:ofType` property links events to harm types
  - `ex:perpetrator` property for actor attribution
  - `ex:severity` property (1-10 scale) for impact assessment
  - Worked example: `exampleDestructionEvent`
- **HarmPattern class**: Capture empirical co-occurrences of independent harms
  - `ex:includesHarm` property (minCardinality 2)
  - Worked example: `CoverUpPattern` (Suppression + Alteration + Denial)
- **Controlled vocabularies** for soft properties:
  - `DetectabilityScheme`: EasilyDetectable, ModeratelyDetectable, DifficultToDetect
  - `ReversibilityScheme`: Reversible, PartiallyReversible, Irreversible
  - All 12 harm instances seeded with detectability/reversibility values
- **Property enhancements**:
  - `ex:isBuiltUponBy` as inverse of `ex:buildsUpon`
  - `ex:detectability` and `ex:reversibility` as object properties (not free strings)
- **SHACL shapes** moved to separate file (`record-harm-shapes.ttl`):
  - `PrimeHarmShape`: Enforces zero `buildsUpon` edges
  - `CompositeHarmShape`: Enforces minCount 1 `buildsUpon`
  - `RecordHarmClassificationShape`: Enforces exactly-one-of Prime/Composite
  - `BuildsUponEndpointTypeShape`: Validates both ends of `buildsUpon`
  - `HarmEventShape`: Validates severity range, ofType cardinality, date format
  - `HarmPatternShape`: Enforces minCount 2 for `includesHarm`
  - `DetectabilityShape`: Validates controlled vocabulary membership

### Changed
- **Domain of `ex:harms`**: Now `owl:unionOf(RecordHarm, HarmEvent)` instead of just RecordHarm
  - Allows both harm types and harm events to use the property
  - Correctly uses `owl:unionOf` (not multiple `rdfs:domain` which would create intersection)
- **Severity placement**: Moved from RecordHarm (type level) to HarmEvent (instance level)
  - Rationale: Severity is property of specific occurrence, not abstract category

### Fixed
- Inline documentation expanded with [v2.2] tags explaining all design decisions
- Comments warn about common OWL pitfalls (e.g., `owl:unionOf` vs multiple domains)

## [2.1.0] - 2026-06-20

### Changed
- **Denial promoted to 5th PrimeHarm** (was CompositeHarm building on Suppression)
  - Rationale: Denial doesn't require hiding (can deny fully accessible record)
  - Makes it ontologically irreducible, distinct from other four primes
  - Cleans up Repudiation (now composite of two primes, not composite of composite)

### Added
- **SKOS typing** for all harm instances:
  - Every harm now typed `skos:Concept` and `skos:inScheme ex:RecordHarmScheme`
  - Enables browsing/export by generic SKOS tooling
  - Parallel to existing `RecordAspectScheme`
- **`rdfs:isDefinedBy`** added to all harm instances
- **Explicit typing fallback**: All composites explicitly typed `ex:CompositeHarm`
  - Not relying solely on `owl:equivalentClass` restriction
  - Ensures tools without DL reasoner still get correct classification

### Fixed
- Comment added at `ex:CompositeHarm` explaining dual typing strategy

## [2.0.0] - 2026-06-20

### Changed
- **Boolean flags replaced with OWL classes**:
  - `ex:isFundamentalRoot` → `ex:PrimeHarm` class membership
  - `ex:isComposite` → `ex:CompositeHarm` class membership
  - Classes are disjoint and reasoner-checkable
- **`ex:buildsUpon` property enhanced**:
  - Declared `owl:TransitiveProperty` (composites transitively build on all primes beneath)
  - Declared `owl:AsymmetricProperty` (prevents A builds on B, B builds on A)
  - Declared `owl:IrreflexiveProperty` (prevents self-dependency)
- **Aspect targeting unified**:
  - Removed duplicate aspect-subclasses (ExistenceHarm, MutationHarm, etc.)
  - `ex:targetsAspect` is now single source of truth
  - Range narrowed to `skos:Concept`
- **RecordAspect promoted to SKOS**:
  - Now proper `skos:ConceptScheme` with concept instances
  - Was bare `owl:Class` with individuals in v1
- **Class-level restriction** for `ex:harms`:
  - Replaced repetitive instance-level assertions
  - Documents type-level relationship

### Removed
- `ex:hasDescription` (replaced by `skos:definition`)
- `ex:composesWith` (declared but never used)
- Aspect-named subclasses (ExistenceHarm, AuthenticityHarm, MutationHarm, etc.)

### Fixed
- `dc:created` now properly typed as `xsd:date`
- MutationHarm inconsistency resolved (had no matching aspect)

## [1.0.0] - 2026-06-20

### Added
- Initial release with core ontology structure
- **4 Prime Harms**: Destruction, Fabrication, Alteration, Omission
- **8 Composite Harms**: ForgeryOfProvenance, Fragmentation, Suppression, Obfuscation, Decontextualization, Contamination, Denial, Repudiation
- **6 Record Aspects**: Existence, Authenticity, Integrity, Accessibility, Context, Trustworthiness
- Basic property structure:
  - `ex:harms` (links harm to record)
  - `ex:targetsAspect` (links harm to aspects)
  - `ex:buildsUpon` (links composite to dependencies)
  - `ex:isFundamentalRoot` (boolean flag)
  - `ex:isComposite` (boolean flag)
- Aspect-named subclasses for harm categorization
- Dublin Core metadata integration

### Known Issues
- Denial incorrectly classified as CompositeHarm (fixed in v2.1)
- MutationHarm class has no matching aspect (fixed in v2.0)
- Boolean flags not reasoner-checkable (fixed in v2.0)

---

## Version Numbering

- **Major version** (X.0.0): Breaking changes to ontology structure
- **Minor version** (0.X.0): New classes, properties, or significant enhancements
- **Patch version** (0.0.X): Bug fixes, documentation, minor clarifications

## Upgrade Notes

### From v2.1 to v2.2
- No breaking changes
- New classes (HarmEvent, HarmPattern) are additive
- Existing harm type instances unchanged
- SHACL shapes now in separate file (update validation scripts)

### From v2.0 to v2.1
- Denial reclassified from CompositeHarm to PrimeHarm
- Update any queries assuming Denial builds upon Suppression
- All harm instances now have SKOS typing (additive, not breaking)

### From v1.0 to v2.0
- **BREAKING**: Aspect-subclasses removed (ExistenceHarm, etc.)
  - Migrate to using `ex:targetsAspect` property instead
- **BREAKING**: Boolean properties removed (isFundamentalRoot, isComposite)
  - Migrate to checking `rdf:type ex:PrimeHarm` or `ex:CompositeHarm`
- `ex:hasDescription` replaced by `skos:definition` (update queries)
- RecordAspect individuals now typed `skos:Concept` (additive)
