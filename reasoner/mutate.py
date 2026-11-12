"""Negative tests: inject errors into a valid .ttl and check what HermiT and SHACL answer.

HermiT (open world) detects contradictions; SHACL (closed world) detects missing or
malformed information. Each case states the expected answer of each validator.
"""
import os
import subprocess
import sys

from rdflib import Graph, Literal, Namespace, RDF, URIRef

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SOURCE = os.path.join(ROOT, "examples", "insurance", "insurance.ttl")
OUT_DIR = os.path.join(HERE, "mutations")
REASON = os.path.join(HERE, "reason.py")
SHACL = os.path.join(HERE, "validate_shacl.py")

D = Namespace("https://example.org/ddd-metamodel#")

def first(g, cls):
    """First subject of type cls (sorted for a reproducible result)."""
    return sorted(g.subjects(RDF.type, cls))[0]


def entity_is_also_value_object(g):
    g.add((first(g, D.Entity), RDF.type, D.ValueObject))


def bounded_context_is_also_aggregate(g):
    g.add((first(g, D.BoundedContext), RDF.type, D.Aggregate))


def aggregate_with_two_roots(g):
    roots = sorted(g.subjects(RDF.type, D.RootEntity))
    aggregate = next(g.subjects(D.containsEntity, roots[0]))
    other = next(r for r in roots if (aggregate, D.containsEntity, r) not in g)
    g.add((aggregate, D.containsEntity, other))


def aggregate_without_root(g):
    root = first(g, D.RootEntity)
    g.remove((root, RDF.type, D.RootEntity))
    g.add((root, RDF.type, D.Entity))


def bounded_context_with_invalid_type(g):
    bc = first(g, D.BoundedContext)
    g.remove((bc, D.bcType, None))
    g.add((bc, D.bcType, Literal("WHATEVER")))


def aggregate_without_name(g):
    g.remove((first(g, D.Aggregate), D.name, None))


def attribute_with_unknown_reference(g):
    attribute = sorted(g.subjects(D.refersTo, None))[0]
    g.remove((attribute, D.refersTo, None))
    g.add((attribute, D.refersTo, URIRef("https://example.org/kg/insurance/bc/Nowhere/Ghost")))


def team_with_aggregate(g):
    g.add((first(g, D.Team), D.hasAggregate, first(g, D.Aggregate)))


def aggregate_owned_by_context(g):
    aggregate = first(g, D.Aggregate)
    g.remove((aggregate, D.ownedBy, None))
    g.add((aggregate, D.ownedBy, first(g, D.BoundedContext)))


def aggregate_as_upstream(g):
    relationship = sorted(g.subjects(D.upstream, None))[0]
    g.add((relationship, D.upstream, first(g, D.Aggregate)))


def relationship_without_upstream(g):
    g.remove((sorted(g.subjects(D.upstream, None))[0], D.upstream, None))

# (file name, description, mutation function, expected HermiT code, expected SHACL code)
CASES = [
    ("00_baseline", "no mutation (control)", None, 0, 0),
    ("01_entity_valueobject", "an Entity is also a ValueObject", entity_is_also_value_object, 1, 0),
    ("02_bc_aggregate", "a BoundedContext is also an Aggregate", bounded_context_is_also_aggregate, 1, 1),
    ("03_two_roots", "an Aggregate contains two RootEntity", aggregate_with_two_roots, 1, 1),
    ("04_no_root", "an Aggregate has no RootEntity", aggregate_without_root, 0, 1),
    ("05_bad_bctype", "a BoundedContext has an invalid bcType", bounded_context_with_invalid_type, 0, 1),
    ("06_no_name", "an Aggregate has no name", aggregate_without_name, 0, 1),
    ("07_unknown_ref", "an Attribute refers to an unknown term", attribute_with_unknown_reference, 0, 1),
    ("08_team_aggregate", "a Team has an Aggregate", team_with_aggregate, 1, 0),
    ("09_owner_not_team", "an Aggregate is owned by a BoundedContext", aggregate_owned_by_context, 1, 1),
    ("10_aggregate_upstream", "an Aggregate is the upstream of a relationship", aggregate_as_upstream, 1, 1),
    ("11_no_upstream", "a relationship has no upstream context", relationship_without_upstream, 0, 1),
]

HERMIT_VERDICT = {0: "COHERENT", 1: "INCOHERENT"}
SHACL_VERDICT = {0: "CONFORMS", 1: "NON-CONFORMING"}


def run(script, path):
    return subprocess.run([sys.executable, script, path], capture_output=True, text=True)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    failures = 0
    for name, description, mutate, want_hermit, want_shacl in CASES:
        g = Graph()
        g.parse(SOURCE, format="turtle")
        if mutate:
            mutate(g)
        path = os.path.join(OUT_DIR, name + ".ttl")
        g.serialize(destination=path, format="turtle")

        hermit, shacl = run(REASON, path), run(SHACL, path)
        ok = (hermit.returncode, shacl.returncode) == (want_hermit, want_shacl)
        failures += not ok
        print(f"[{'OK' if ok else 'MISMATCH'}] {name:22} "
              f"HermiT={HERMIT_VERDICT.get(hermit.returncode, 'ERROR'):10} "
              f"SHACL={SHACL_VERDICT.get(shacl.returncode, 'ERROR'):15} {description}")
        for result in (hermit, shacl):
            if result.returncode not in (0, 1):
                print(result.stderr)
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
