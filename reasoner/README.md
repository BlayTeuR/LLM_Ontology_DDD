# Reasoner (HermiT)

Checks that an artifact (`.ttl` produced by the CML converter) is logically consistent with the DDD metamodel (`metamodel/ddd-metamodel.ttl` and its Conflict module `metamodel/ddd-conflict.ttl`). HermiT is the OWL reasoner embedded in [Owlready2](https://owlready2.readthedocs.io).

## Requirements

- Java (same as for `cm`), Python 3.x
- `pip install -r requirements.txt`

## Usage

Run from the repository root:

```
python reasoner/reason.py examples/insurance/insurance.ttl
python reasoner/mutate.py
python reasoner/validate_shacl.py examples/insurance/insurance.ttl
```

`reason.py` exits with `0` (COHERENT) or `1` (INCOHERENT). `--tbox <files>` overrides the metamodel files.
`validate_shacl.py` exits with 0 (CONFORMS) or 1 (NON-CONFORMING) and prints one line per violation. `--tbox <files>` and `--shapes <files>` override the metamodel and the SHACL shapes (by default: `ddd-metamodel.ttl` + `ddd-conflict.ttl`, `shapes.ttl` + `shapes-conflict.ttl`).

`mutate.py` is the negative test: it copies `insurance.ttl`, injects one faulty triple per case, runs `reason.py` and `validate_shacl.py` on each copy and compares both results with the expected ones.

| Case | Injected error | HermiT | SHACL |
|---|---|---|---|
| `00_baseline` | none (control) | COHERENT | CONFORMS |
| `01_entity_valueobject` | an Entity is also a ValueObject | INCOHERENT | CONFORMS |
| `02_bc_aggregate` | a BoundedContext is also an Aggregate | INCOHERENT | NON-CONFORMING |
| `03_two_roots` | an Aggregate contains two RootEntity | INCOHERENT | NON-CONFORMING |
| `04_no_root` | an Aggregate has no RootEntity | COHERENT | NON-CONFORMING |
| `05_bad_bctype` | a BoundedContext has an invalid bcType | COHERENT | NON-CONFORMING |
| `06_no_name` | an Aggregate has no name | COHERENT | NON-CONFORMING |
| `07_unknown_ref` | an Attribute refers to an unknown term | COHERENT | NON-CONFORMING |
| `08_team_aggregate` | a Team has an Aggregate | INCOHERENT | CONFORMS |
| `09_owner_not_team` | an Aggregate is owned by a BoundedContext | INCOHERENT | NON-CONFORMING |
| `10_aggregate_upstream` | an Aggregate is the upstream of a relationship | INCOHERENT | NON-CONFORMING |
| `11_no_upstream` | a relationship has no upstream context | COHERENT | NON-CONFORMING |

## How it works

1. The metamodel files (TBox: core metamodel and Conflict module, merged without following `owl:imports`) and the artifact (ABox) are merged with rdflib into a temporary N-Triples file (Owlready2 cannot read Turtle).
2. An `owl:AllDifferent` axiom over all individuals of the artifact is added to that file. OWL does not assume that distinct names are distinct things: without it, two roots in one Aggregate would be merged into one instead of being reported.
3. The file is loaded in Owlready2 and `sync_reasoner_hermit()` is run.

## Scope and limits

- HermiT checks typing, disjointness and upper bounds. It does not check lower bounds ("at least one root"): OWL works under the open-world assumption, those rules belong to SHACL (`metamodel/shapes.ttl` and `shapes-conflict.ttl`, checked by `validate_shacl.py`).
- One file at a time. An inconsistency that only appears when two artifacts are combined is not detected yet.
- The result does not gate the Neo4j loading: the two commands are run separately.
