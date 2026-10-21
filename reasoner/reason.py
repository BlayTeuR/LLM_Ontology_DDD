"""Raisonnement HermiT sur un artefact TTL (metamodele + donnees)."""
import argparse
import os
import sys
import tempfile
import time

from rdflib import Graph, RDF, OWL, BNode, URIRef
from rdflib.collection import Collection
from owlready2 import (
    get_ontology, sync_reasoner_hermit,
    default_world, OwlReadyInconsistentOntologyError,
)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TBOX = os.path.join(ROOT, "metamodel", "ddd-metamodel.ttl")
TBOX_IRI = "https://example.org/ddd-metamodel"

def merge_to_ntriples(tbox_path, abox_path, out_path):
    """Fusionne TBox + ABox en N-Triples et y ajoute l'axiome AllDifferent.

    OWL n'a pas d'hypothese de noms uniques : sans AllDifferent, deux racines
    d'un meme Aggregate seraient jugees identiques au lieu d'etre une erreur.
    Retourne (nombre de triplets, nombre d'individus).
    """
    g = Graph()
    g.parse(tbox_path, format="turtle")
    abox = Graph()
    abox.parse(abox_path, format="turtle")

    # individus = sujets IRI qui ont un rdf:type dans l'ABox (pas dans le TBox)
    individuals = sorted({s for s in abox.subjects(RDF.type, None)
                          if isinstance(s, URIRef)})
    g += abox

    # [] a owl:AllDifferent ; owl:distinctMembers ( ind1 ind2 ... )
    axiom, members = BNode(), BNode()
    g.add((axiom, RDF.type, OWL.AllDifferent))
    Collection(g, members, individuals)
    g.add((axiom, OWL.distinctMembers, members))

    g.serialize(destination=out_path, format="nt", encoding="utf-8")
    return len(g), len(individuals)


def load_ontology(nt_path):
    """Charge le fichier N-Triples dans Owlready2."""
    onto = get_ontology(TBOX_IRI)
    with open(nt_path, "rb") as f:
        onto.load(fileobj=f, format="ntriples")
    return onto


def run_hermit():
    """Retourne (coherent, duree_en_secondes)."""
    t0 = time.perf_counter()
    try:
        sync_reasoner_hermit(debug=0)
    except OwlReadyInconsistentOntologyError:
        return False, time.perf_counter() - t0
    return True, time.perf_counter() - t0


def main():
    ap = argparse.ArgumentParser(description="Verifie la coherence d'un .ttl avec HermiT.")
    ap.add_argument("abox", help="fichier .ttl genere par le convertisseur")
    ap.add_argument("--tbox", default=TBOX, help="metamodele (defaut : ddd-metamodel.ttl)")
    args = ap.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        nt_path = os.path.join(tmp, "merged.nt")
        n_triples, n_individuals = merge_to_ntriples(args.tbox, args.abox, nt_path)
        load_ontology(nt_path)

    print(f"Triplets fusionnes : {n_triples} | individus : {n_individuals}")

    coherent, secs = run_hermit()
    if not coherent:
        print(f"INCOHERENT ({secs:.1f}s) : l'artefact viole le metamodele.")
        sys.exit(1)

    unsat = list(default_world.inconsistent_classes())
    print(f"COHERENT ({secs:.1f}s) | classes insatisfaisables : {len(unsat)}")
    sys.exit(0)


if __name__ == "__main__":
    main()