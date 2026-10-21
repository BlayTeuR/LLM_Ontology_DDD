# DDD Metamodel

The DDD metamodel used by the project, and its archived versions.

- `ddd-metamodel.ttl`: current version (0.2.0). Used by the CML to OWL converter (`cml_to_ttl/`) and by the reasoner (`reasoner/`).
- `shapes.ttl`: SHACL rules (closed world) for the same metamodel. Not wired yet.
- `archive/`: previous versions. When a new version starts, the current file is copied here as `ddd-metamodel_vXY.ttl` (`v01` = 0.1.0) before the root file is changed.

| Version | File | Changes |
|---|---|---|
| 0.1.0 | `archive/ddd-metamodel_v01.ttl` | First version: Context Map, Bounded Context, Domain / Subdomain, relationships and roles, Aggregate / Entity / RootEntity / ValueObject / DomainEvent, Attribute (with `refersTo`), text properties, Conflict. |
| 0.2.0 | `ddd-metamodel.ttl` (current) | Adds `ownedBy` (Aggregate to its TEAM), `bcType`, `implementationTechnology`, `contextMapType` and `contextMapState`. |
| 0.3.0 (planned) | | Adds `Team` as a class disjoint from `BoundedContext` (breaking: `ownedBy` range changes, `bcType` loses `TEAM`), `downstreamRights`, `Operation`, `isKey`, `collectionType`. |