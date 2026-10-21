# CML → Turtle (OWL) Converter

Converts a Context Mapper file (`.cml`) into an OWL artifact (`.ttl`) conforming to the DDD metamodel ([`metamodel/ddd-metamodel.ttl`](../metamodel/ddd-metamodel.ttl), version 0.2.0). No LLM involved: the conversion is deterministic.

## Requirements

- [Context Mapper CLI](https://contextmapper.org) 6.12.0 (official CML parser, used through
  `cm generate -g generic`). Install it separately and add its `bin/` folder to your `PATH`.
- Java (required by `cm` and HermiT), Python 3.x, Docker (Neo4j).

## Usage

Run everything from the repository root:

```
python cml_to_ttl/src/main_cml_to_ttl.py examples/insurance/insurance.cml
python cml_to_ttl/src/run_cml_examples.py
```

Output: `cml_to_ttl/output_cml/json/insurance.json`, then `cml_to_ttl/output_cml/ttl/insurance.ttl` (same name as the `.cml`; this folder is generated and not versioned). To use a different output folder: `--out <folder>`. A reference output is versioned in [`examples/insurance/insurance.ttl`](../examples/insurance/insurance.ttl).

## Files

| File | Role |
|---|---|
| `src/main_cml_to_ttl.py` | Entry point: chains the two steps |
| `src/cml_to_json.py` | Step 1: calls `cm generate` with the template |
| `cm-probe/export-json.ftl` | Freemarker template: copies the CML into JSON, without interpretation |
| `src/cml2ttl.py` | Step 2: JSON → RDF graph (the mapping) |
| `src/iri.py` | Deterministic IRI generation |
| `src/run_cml_examples.py` | Converter test: compares `cml_tests/*.cml` to their `// EXPECT:` header |

The Python scripts import each other, so they must stay together in `src/`. Paths to the template, tests and outputs are resolved from `cml_to_ttl/` (the parent of `src/`). The metamodel (`ddd-metamodel.ttl`) and the SHACL shapes (`shapes.ttl`) live in [`../metamodel/`](../metamodel); the converter does not read them during a conversion (only the `--validate` option, not available yet, does).

Consistency checking with HermiT lives in the separate [`reasoner/`](../reasoner) folder (run it on the generated `.ttl`). SHACL validation is not available yet: `validate_artifact.py` and `check_vocab.py` do not exist, so `cml2ttl.py --validate` does not work.

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
