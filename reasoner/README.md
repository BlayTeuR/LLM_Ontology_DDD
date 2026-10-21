# Reasoner (HermiT)

Checks that an artifact (`.ttl` produced by the CML converter) is logically consistent with the DDD metamodel (`metamodel/ddd-metamodel.ttl`). HermiT is the OWL reasoner embedded in [Owlready2](https://owlready2.readthedocs.io).

## Requirements

- Java (same as for `cm`), Python 3.x
- `pip install rdflib owlready2`

## Usage

Run from the repository root:

```
python reasoner/reason.py cml_to_ttl/output_cml/ttl/insurance.ttl
python reasoner/mutate.py
```

`reason.py` exits with `0` (COHERENT) or `1` (INCOHERENT). `--tbox <file>` overrides the metamodel.

`mutate.py` is the negative test: it copies `insurance.ttl`, injects one faulty triple per case, runs `reason.py` on each copy and compares with the expected result. The copies are written to `reasoner/mutations/` (regenerated at each run).

| Case | Injected error | Detected by |
|---|---|---|
| `00_baseline` | none (control) | expected COHERENT |
| `01_entity_valueobject` | an Entity is also a ValueObject | disjoint classes |
| `02_bc_aggregate` | a BoundedContext is also an Aggregate | disjoint classes |
| `03_two_roots` | an Aggregate contains two RootEntity | `Aggregate ⊑ ≤1 containsEntity.RootEntity` |

## How it works

1. The metamodel (TBox) and the artifact (ABox) are merged with rdflib into a temporary N-Triples file (Owlready2 cannot read Turtle).
2. An `owl:AllDifferent` axiom over all individuals of the artifact is added to that file. OWL does not assume that distinct names are distinct things: without it, two roots in one Aggregate would be merged into one instead of being reported.
3. The file is loaded in Owlready2 and `sync_reasoner_hermit()` is run.

## Scope and limits

- HermiT checks typing, disjointness and upper bounds. It does not check lower bounds ("at least one root"): OWL works under the open-world assumption, those rules belong to SHACL (`metamodel/shapes.ttl`, not wired yet).
- One file at a time. An inconsistency that only appears when two artifacts are combined is not detected yet.
- The result does not gate the Neo4j loading: the two commands are run separately.
