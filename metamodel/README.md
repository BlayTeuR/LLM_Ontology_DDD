# DDD Metamodel versions

Archived versions of the DDD metamodel. The current version is `cml_to_ttl/ddd-metamodel.ttl`, the one used by the CML to OWL converter. When a new version starts, the previous one is copied here as `ddd-metamodel_vXY.ttl` (`v01` = 0.1.0).

| Version | File | Changes |
|---|---|---|
| 0.1.0 | `ddd-metamodel_v01.ttl` | First version: Context Map, Bounded Context, Domain / Subdomain, relationships and roles, Aggregate / Entity / RootEntity / ValueObject / DomainEvent, Attribute (with `refersTo`), text properties, Conflict. |
| 0.2.0 | `../cml_to_ttl/ddd-metamodel.ttl` (current) | Adds `ownedBy` (Aggregate to its TEAM), `bcType`, `implementationTechnology`, `contextMapType` and `contextMapState`. |
| 0.3.0 (planned) | | Adds `Team` as a class disjoint from `BoundedContext` (breaking: `ownedBy` range changes, `bcType` loses `TEAM`), `downstreamRights`, `Operation`, `isKey`, `collectionType`. |
