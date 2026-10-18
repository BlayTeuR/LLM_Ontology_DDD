# CML → Turtle (OWL) Converter

Converts a Context Mapper file (`.cml`) into an OWL artifact (`.ttl`) conforming to the DDD metamodel (`ddd-metamodel.ttl`, version 0.3.0). No LLM involved: the conversion is deterministic.

## Requirements

- Context Mapper CLI (`cm`) on the `PATH`, Java 17+.
- Python 3 and `rdflib`: `python -m pip install rdflib`.

## Usage

```
python main_cml_to_ttl.py test.cml
```


Output: `output_cml/json/test.json`, then `output_cml/ttl/test.ttl` (same name as the `.cml`). To use a different output folder: `--out <folder>`.

## Files (all in the same folder)

| File | Role |
|---|---|
| `main_cml_to_ttl.py` | Entry point: chains the two steps |
| `cml_to_json.py` | Step 1: calls `cm generate` with the template |
| `export-json-v03.ftl` | Freemarker template: copies the CML into JSON, without interpretation |
| `cml2ttl.py` | Step 2: JSON → RDF graph (the mapping) |
| `iri.py` | Deterministic IRI generation |

To validate the artifact (SHACL, HermiT; Java required), run separately: `python cml2ttl.py output_cml/json/test.json -o x.ttl --validate [--no-hermit]`, with `ddd-metamodel.ttl`, `shapes.ttl`, `validate_artifact.py`, `check_vocab.py` and `reason.py` in the folder.

## What is converted

| CML | OWL |
|---|---|
| `ContextMap`, `contains` | `ddd:ContextMap`, `showsRelevantContext` |
| `BoundedContext` | `ddd:BoundedContext` + `domainVisionStatement`, `responsibility` |
| `Domain`, `Subdomain` (CORE / SUPPORTING / GENERIC) | `ddd:Domain`, `CoreDomain` / `SupportingSubdomain` / `GenericSubdomain` |
| `Aggregate` | `ddd:Aggregate` |
| `Entity` (`aggregateRoot` or not), `ValueObject`, `DomainEvent` | `RootEntity` / `Entity`, `ValueObject`, `DomainEvent` |
| attribute (`String name`), reference (`- Type name`) | `ddd:Attribute`; a reference additionally carries `ddd:refersTo` pointing to the target term |
| `[U]->[D]` (+ `[S]`/`[C]`) | `UpstreamDownstreamRelationship` (`CustomerSupplierRelationship`) |
| `[P]<->[P]`, `[SK]<->[SK]` | `Partnership`, `SharedKernel` |
| roles `OHS`, `PL`, `ACL`, `CF` | `OpenHostService`, `PublishedLanguage`, `AnticorruptionLayer`, `Conformist` |
| `exposedAggregates` | `ddd:exposesAggregate` |

Not converted (reported, or absent from the JSON): `TEAM` contexts, Enum / Trait / DTO (warning), `import` (warning: export each file separately), line numbers, and elements absent from the V0 metamodel (`knowledgeLevel`, `implementationTechnology`, `useCases`, etc.).
