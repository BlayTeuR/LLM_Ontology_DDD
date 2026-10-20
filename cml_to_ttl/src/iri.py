"""Fabrication des IRI d'instances : UNE seule fonction, partagee par les deux routes.

Regles (voir aussi le README de la conversation) :
  - deterministe : memes noms + meme structure => meme IRI, a chaque execution ;
  - independante du fichier, de la ligne, de l'ordre dans le fichier ;
  - construite uniquement avec ce qu'on peut ecrire a l'endroit ou l'element est
    REFERENCE en CML (une BC referencee par son seul nom, un sous-domaine par son
    seul nom) => pas de segment "domaine" dans l'IRI d'un sous-domaine ;
  - imbriquee sous le contexte pour ce qui n'a de sens que dans un contexte
    (agregat, entite, value object, evenement) => les homonymes de deux contextes
    ont des IRI differentes ;
  - le TYPE de relation n'est pas dans l'IRI (changer [U,S] en [P] ne doit pas
    creer un nouveau noeud) ;
  - relation symetrique : noms tries (A<->B == B<->A) ; relation sans nom :
    "<amont>--<aval>".

BASE est LA variable de configuration a changer (ou variable d'environnement
KG_BASE). example.org est reserve (RFC 2606) : valeur de remplacement uniquement.
"""
import os
from urllib.parse import quote

from rdflib import Graph, Namespace, RDF, URIRef

BASE = os.environ.get("KG_BASE", "https://example.org/kg/insurance/")
if not BASE.endswith("/"):
    BASE += "/"

DDD_NS = "https://example.org/ddd-metamodel#"   # idem : a remplacer, une seule fois
D = Namespace(DDD_NS)

KINDS = ("map", "domain", "subdomain", "bc", "rel")

ROLE_ABBR = {
    D.OpenHostService: "OHS",
    D.PublishedLanguage: "PL",
    D.AnticorruptionLayer: "ACL",
    D.Conformist: "CF",
}


def seg(name: str) -> str:
    """Un segment d'IRI : tout caractere hors [A-Za-z0-9_.~-] est encode en %XX."""
    return quote(name, safe="")


def mint(kind: str, *path: str) -> str:
    if kind not in KINDS:
        raise ValueError(f"type d'IRI inconnu : {kind!r} (attendu : {KINDS})")
    if not path or any(not p for p in path):
        raise ValueError(f"segment vide dans {path!r}")
    return BASE + kind + "/" + "/".join(seg(p) for p in path)


def rel_key(name=None, upstream=None, downstream=None, participants=None) -> str:
    if name:
        return name
    if participants:
        return "--".join(sorted(participants))
    return f"{upstream}--{downstream}"


# ----------------------------------------------------------------------------
# Route LLM : le LLM propose des IRI quelconques ; le pipeline les remplace par
# les IRI fabriquees ici, a partir des ddd:name et de la structure. Ainsi le
# LLM ne decide jamais de l'identite d'un noeud.
# ----------------------------------------------------------------------------

_SUBDOMAIN_CLASSES = (D.Subdomain, D.CoreDomain, D.SupportingSubdomain, D.GenericSubdomain)
_REL_CLASSES = (D.Partnership, D.SharedKernel, D.UpstreamDownstreamRelationship,
                D.CustomerSupplierRelationship, D.SymmetricRelationship,
                D.BoundedContextRelationship)


def _subjects(g, classes):
    out = set()
    for c in classes:
        out |= {s for s in g.subjects(RDF.type, c) if isinstance(s, URIRef)}
    return out


def remint(g: Graph):
    """Retourne (graphe_reecrit, mapping ancienne->nouvelle IRI, erreurs).

    Les erreurs sont formulees pour etre renvoyees au LLM (boucle de correction).
    """
    errors, m = [], {}

    def name(n):
        v = g.value(n, D.name)
        if v is None or not str(v).strip():
            errors.append(f"{n} : ddd:name manquant, impossible de calculer son identite")
            return None
        return str(v)

    def assign(node, iri):
        if node in m and str(m[node]) != iri:
            errors.append(f"{node} : deux identites possibles ({m[node]} / {iri})")
        m[node] = URIRef(iri)

    for node in _subjects(g, [D.ContextMap]):
        if (n := name(node)): assign(node, mint("map", n))
    for node in _subjects(g, [D.Domain]):
        if (n := name(node)): assign(node, mint("domain", n))
    for node in _subjects(g, _SUBDOMAIN_CLASSES):
        if (n := name(node)): assign(node, mint("subdomain", n))

    bcs = _subjects(g, [D.BoundedContext])
    for bc in bcs:
        if (bn := name(bc)) is None:
            continue
        assign(bc, mint("bc", bn))
        for agg in g.objects(bc, D.hasAggregate):
            if (an := name(agg)) is None:
                continue
            assign(agg, mint("bc", bn, an))
            for prop in (D.containsEntity, D.containsValueObject, D.containsDomainEvent):
                for child in g.objects(agg, prop):
                    if (cn := name(child)):
                        assign(child, mint("bc", bn, an, cn))
                        for at in g.objects(child, D.hasAttribute):
                            if (atn := name(at)): assign(at, mint("bc", bn, an, cn, atn))

    for node in _subjects(g, [D.Aggregate]):
        if node not in m:
            errors.append(f"{node} : Aggregate rattache a aucun BoundedContext (hasAggregate)")
    for node in _subjects(g, [D.Entity, D.RootEntity, D.ValueObject, D.DomainEvent]):
        if node not in m:
            errors.append(f"{node} : element rattache a aucun Aggregate")

    for rel in _subjects(g, _REL_CLASSES):
        ups, downs = list(g.objects(rel, D.upstream)), list(g.objects(rel, D.downstream))
        parts = list(g.objects(rel, D.hasParticipant))
        own = g.value(rel, D.name)
        try:
            if parts:
                pn = [name(p) for p in parts]
                key = None if None in pn else rel_key(own and str(own), participants=pn)
            else:
                un, dn = name(ups[0]), name(downs[0])
                key = None if None in (un, dn) else rel_key(own and str(own), un, dn)
        except IndexError:
            errors.append(f"{rel} : relation sans amont/aval ni participants")
            continue
        if key is None:
            continue
        assign(rel, mint("rel", key))
        for prop in (D.hasUpstreamRole, D.hasDownstreamRole):
            for role in g.objects(rel, prop):
                abbr = next((ROLE_ABBR[c] for c in ROLE_ABBR if (role, RDF.type, c) in g), None)
                if abbr:
                    assign(role, m[rel] + "/" + abbr)
                else:
                    errors.append(f"{role} : role de type inconnu")

    # collisions : deux noeuds differents -> meme IRI = vrai doublon
    seen = {}
    for old, new in m.items():
        if new in seen and seen[new] != old:
            errors.append(f"doublon : {seen[new]} et {old} auraient la meme identite {new}")
        seen[new] = old

    out = Graph()
    for p, ns in g.namespaces():
        out.bind(p, ns)
    for s, p, o in g:
        out.add((m.get(s, s), p, m.get(o, o) if isinstance(o, URIRef) else o))
    return out, m, errors


if __name__ == "__main__":
    for k, path in [("bc", ("CustomerManagementContext",)),
                    ("bc", ("PolicyManagementContext", "Contract")),
                    ("bc", ("PolicyManagementContext", "Contract", "Contract")),
                    ("rel", (rel_key(upstream="PrintingContext", downstream="CustomerManagementContext"),)),
                    ("rel", (rel_key(participants=["RiskManagementContext", "PolicyManagementContext"]),)),
                    ("bc", ("Contrat é",))]:
        print(mint(k, *path))
