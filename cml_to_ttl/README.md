# CML → Turtle (OWL) Converter

Converts a Context Mapper file (`.cml`) into an OWL artifact (`.ttl`) conforming to the DDD metamodel (`ddd-metamodel.ttl`, version 0.2.0). No LLM involved: the conversion is deterministic.

## Requirements

- [Context Mapper CLI](https://contextmapper.org) 6.12.0 (official CML parser, used through
  `cm generate -g generic`). Install it separately and add its `bin/` folder to your `PATH`.
- Java (required by `cm` and HermiT), Python 3.x, Docker (Neo4j).

## Usage

Run everything from the project root (`cml_to_ttl/`):

```
python src/main_cml_to_ttl.py cml_example/insurance.cml
python src/run_cml_examples.py
```

Output: `output_cml/json/insurance.json`, then `output_cml/ttl/insurance.ttl` (same name as the `.cml`). To use a different output folder: `--out <folder>`.

## Files

| File | Role |
|---|---|
| `src/main_cml_to_ttl.py` | Entry point: chains the two steps |
| `src/cml_to_json.py` | Step 1: calls `cm generate` with the template |
| `cm-probe/export-json.ftl` | Freemarker template: copies the CML into JSON, without interpretation |
| `src/cml2ttl.py` | Step 2: JSON → RDF graph (the mapping) |
| `src/iri.py` | Deterministic IRI generation |
| `src/run_cml_examples.py` | Converter test: compares `cml_tests/*.cml` to their `// EXPECT:` header |

The Python scripts import each other, so they must stay together in `src/`. Paths to the metamodel, shapes, template, tests and outputs are resolved from the project root (the parent of `src/`).

Artifact validation (SHACL, HermiT; Java required) is not available yet: `validate_artifact.py`, `check_vocab.py` and `reason.py` do not exist, so `cml2ttl.py --validate` does not work.

## What is converted

| CML | OWL |
|---|---|
| `ContextMap`, `contains` | `ddd:ContextMap`, `showsRelevantContext` |
| `BoundedContext` | `ddd:BoundedContext` + `domainVisionStatement`, `responsibility` |
| `type` of a `BoundedContext` (`FEATURE`, `APPLICATION`, `SYSTEM`, `TEAM`) | `ddd:bcType` (a `TEAM` is exported as a `ddd:BoundedContext` with `bcType "TEAM"`, and is not listed in `showsRelevantContext`) |
| `implementationTechnology` (on a `BoundedContext` or a relationship) | `ddd:implementationTechnology` |
| `type` / `state` of a `ContextMap` | `ddd:contextMapType` (`SYSTEM_LANDSCAPE`, `ORGANIZATIONAL`) / `ddd:contextMapState` (`AS_IS`, `TO_BE`) |
| `Domain`, `Subdomain` (CORE / SUPPORTING / GENERIC) | `ddd:Domain`, `CoreDomain` / `SupportingSubdomain` / `GenericSubdomain` |
| `Aggregate` | `ddd:Aggregate` |
| `owner` of an `Aggregate` | `ddd:ownedBy` (towards the `TEAM` bounded context) |
| `Entity` (`aggregateRoot` or not), `ValueObject`, `DomainEvent` | `RootEntity` / `Entity`, `ValueObject`, `DomainEvent` |
| attribute (`String name`), reference (`- Type name`) | `ddd:Attribute`; a reference additionally carries `ddd:refersTo` pointing to the target term |
| `[U]->[D]` (+ `[S]`/`[C]`) | `UpstreamDownstreamRelationship` (`CustomerSupplierRelationship`) |
| `[P]<->[P]`, `[SK]<->[SK]` | `Partnership`, `SharedKernel` |
| roles `OHS`, `PL`, `ACL`, `CF` | `OpenHostService`, `PublishedLanguage`, `AnticorruptionLayer`, `Conformist` |
| `exposedAggregates` | `ddd:exposesAggregate` |

Not converted (reported, or absent from the JSON): Enum / Trait / DTO (warning), `import` (warning: export each file separately), line numbers, and elements absent from metamodel 0.2.0 (`knowledgeLevel`, `useCases`, `downstreamRights`, operations, etc.).

An invalid `.cml` is rejected before conversion: `cm generate` accepts it silently, so `cml_to_json.py` first runs `cm validate` and stops on any `ERROR`.
