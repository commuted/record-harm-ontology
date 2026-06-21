# Changelog

All notable changes to the Record Harm Ontology will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.3.0] - 2026-06-20

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
