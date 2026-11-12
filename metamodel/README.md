# DDD Metamodel

The DDD metamodel used by the project, and its archived versions.

- `ddd-metamodel.ttl`: current version (0.3.0), the DDD metamodel derived from Kapferer's. Read by the reasoner (`reasoner/`); the artifacts produced by the CML to OWL converter (`cml_to_ttl/`) conform to it.
- `ddd-conflict.ttl`: Conflict module (0.1.0), the output layer of the method. It is not part of DDD, so it is kept apart; its terms keep the `ddd:` namespace. `reason.py` and `validate_shacl.py` merge it with the metamodel (`owl:imports` is declarative only).
- `shapes.ttl`, `shapes-conflict.ttl`: SHACL rules (closed world) for the metamodel and for the Conflict module. Checked by `reasoner/validate_shacl.py`.
- `archive/`: previous versions. When a new version starts, the current files are copied here as `ddd-metamodel_vXY.ttl` and `shapes_vXY.ttl` (`v01` = 0.1.0) before the root files are changed.

| Version | File | Changes |
|---|---|---|
| 0.1.0 | `archive/ddd-metamodel_v01.ttl` | First version: Context Map, Bounded Context, Domain / Subdomain, relationships and roles, Aggregate / Entity / RootEntity / ValueObject / DomainEvent, Attribute (with `refersTo`), text properties, Conflict. |
| 0.2.0 | `archive/ddd-metamodel_v02.ttl`, `archive/shapes_v02.ttl` | Adds `ownedBy` (Aggregate to its team), `bcType`, `implementationTechnology`, `contextMapType` and `contextMapState`. |
| 0.3.0 | `ddd-metamodel.ttl` (current) | Breaking: adds `Team` (disjoint from `BoundedContext`; `ownedBy` now points to it; `bcType` loses `TEAM`). Adds `GenericUpstreamDownstreamRelationship` and `RelationshipRole`, and a covering axiom on every abstract class (a direct instance is inferred to be one of the subclasses). Partnership/SharedKernel, Generic/CustomerSupplier and Upstream/Downstream roles are pairwise disjoint. A symmetric relationship has exactly two participants. `Conflict` moves to `ddd-conflict.ttl`. Artifacts generated with 0.2.0 are rejected: regenerate them. |
| 0.4.0 (planned) | | Additive CML coverage: `downstreamRights`, `Operation`, `isKey`, `collectionType`, subdomain vision statement and entities. |

Kapferer allows at most one downstream role per relationship, but CML accepts several (`[D,ACL,CF]` is valid in Context Mapper 6.12.0): the bound is not encoded.
