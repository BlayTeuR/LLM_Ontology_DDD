"""Negative tests: inject errors into a valid .ttl and check that HermiT detects them."""
import os
import subprocess
import sys

from rdflib import Graph, Namespace, RDF

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SOURCE = os.path.join(ROOT, "examples", "insurance", "insurance.ttl")
OUT_DIR = os.path.join(HERE, "mutations")
REASON = os.path.join(HERE, "reason.py")

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

# (file name, description, mutation function, expected exit code)
CASES = [
    ("00_baseline", "no mutation (control)", None, 0),
    ("01_entity_valueobject", "an Entity is also a ValueObject", entity_is_also_value_object, 1),
    ("02_bc_aggregate", "a BoundedContext is also an Aggregate", bounded_context_is_also_aggregate, 1),
    ("03_two_roots", "an Aggregate contains two RootEntity", aggregate_with_two_roots, 1),
]

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    failures = 0
    for name, description, mutate, expected in CASES:
        g = Graph()
        g.parse(SOURCE, format="turtle")
        if mutate:
            mutate(g)
        path = os.path.join(OUT_DIR, name + ".ttl")
        g.serialize(destination=path, format="turtle")

        result = subprocess.run([sys.executable, REASON, path],
                                capture_output=True, text=True)
        ok = result.returncode == expected
        failures += not ok
        verdict = {0: "COHERENT", 1: "INCOHERENT"}.get(result.returncode, "ERROR")
        print(f"[{'OK' if ok else 'MISMATCH'}] {name:24} {verdict:11} {description}")
        if result.returncode not in (0, 1):
            print(result.stderr)
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()