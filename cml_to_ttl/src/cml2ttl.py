"""CML -> artefact OWL (Turtle), a partir du JSON exporte par le parseur officiel.

    cm generate -i insurance.cml -g generic -t cm-probe/export-json.ftl -o output_cml/json -f insurance.json
    python src/cml2ttl.py output_cml/json/insurance.json -o insurance.ttl

Conversion seule : il ne faut que rdflib et iri.py. La validation (SHACL, HermiT)
est une option : --validate (ajoute --no-hermit pour sauter HermiT, qui exige Java).

Le JSON est la seule entree ; les IRI viennent de iri.mint ; rien n'est devine.
Tout ce qui ne peut pas etre converti est SIGNALE (avertissements), jamais jete
en silence ; ce qui rend l'artefact incoherent est une ERREUR.
Pas de numero de ligne : le generateur ne les expose pas (ddd:sourceLine absent).
"""
import argparse
import json
import os
import sys
from collections import Counter, defaultdict

from rdflib import Graph, Literal, RDF, URIRef

import iri

D = iri.D
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)       # racine du projet (parent de src/)
SUBDOMAIN = {"CORE_DOMAIN": D.CoreDomain, "SUPPORTING_DOMAIN": D.SupportingSubdomain,
             "GENERIC_SUBDOMAIN": D.GenericSubdomain}
ROLE = {"OHS": D.OpenHostService, "PL": D.PublishedLanguage,
        "ACL": D.AnticorruptionLayer, "CF": D.Conformist}
# kind (JSON) -> (classe, propriete qui relie l'agregat au terme)
UNSET = {"", "UNDEFINED"}      # valeur par defaut de cm quand rien n'est ecrit
TERM = {"value_object": (D.ValueObject, D.containsValueObject),
        "domain_event": (D.DomainEvent, D.containsDomainEvent)}


class BuildError(Exception):
    pass


def build(j):
    g = Graph()
    g.bind("ddd", D)
    src, seen = os.path.basename(j["file"].replace("\\", "/")), {}
    rep = {"counts": Counter(), "warnings": []}
    terms, aggs = {}, {}          # (bc, agg, objet) -> IRI ; (bc, agg) -> IRI
    refs = []                     # references a resoudre une fois tous les termes crees
    bc_names = {b["name"] for b in j["bounded_contexts"]}

    def node(uri, cls, name):
        if uri in seen:
            raise BuildError(f"'{name}' et '{seen[uri]}' produisent la meme IRI : {uri}")
        seen[uri] = name
        u = URIRef(uri)
        g.add((u, RDF.type, cls))
        if name:
            g.add((u, D.name, Literal(name)))
        g.add((u, D.sourceFile, Literal(src)))
        g.add((u, D.generatedBy, Literal("cml-converter")))
        rep["counts"][str(cls).split("#")[-1]] += 1
        return u

    if j["imports"]:
        rep["warnings"].append(f"{len(j['imports'])} import(s) NON suivis (exporter chaque fichier "
                               f"separement) : {', '.join(j['imports'])}")

    for d in j["domains"]:
        du = node(iri.mint("domain", d["name"]), D.Domain, d["name"])
        for s in d["subdomains"]:
            if s["type"] not in SUBDOMAIN:
                rep["warnings"].append(f"sous-domaine {s['name']} : type '{s['type']}' inconnu -> Subdomain")
            g.add((du, D.hasSubdomain,
                   node(iri.mint("subdomain", s["name"]), SUBDOMAIN.get(s["type"], D.Subdomain), s["name"])))

    for bc in j["bounded_contexts"]:
        b, bn = node(iri.mint("bc", bc["name"]), D.BoundedContext, bc["name"]), bc["name"]
        if bc["domain_vision_statement"]:
            g.add((b, D.domainVisionStatement, Literal(bc["domain_vision_statement"])))
        if bc["type"] not in UNSET:
            g.add((b, D.bcType, Literal(bc["type"])))
        if bc["implementation_technology"]:
            g.add((b, D.implementationTechnology, Literal(bc["implementation_technology"])))
        for x in bc["responsibilities"]:
            g.add((b, D.responsibility, Literal(x)))
        for s in bc["implements"]:
            g.add((b, D.implementsPartOf, URIRef(iri.mint("subdomain", s))))
        for a in bc["aggregates"]:
            au = aggs[(bn, a["name"])] = node(iri.mint("bc", bn, a["name"]), D.Aggregate, a["name"])
            g.add((b, D.hasAggregate, au))
            if a["owner"]:
                if a["owner"] not in bc_names:
                    rep["warnings"].append(f"{bn}/{a['name']} : owner '{a['owner']}' n'est pas un BoundedContext de ce fichier")
                g.add((au, D.ownedBy, URIRef(iri.mint("bc", a["owner"]))))
            for x in a["responsibilities"]:
                g.add((au, D.responsibility, Literal(x)))
            for o in a["objects"]:
                if o["kind"] == "other":
                    rep["warnings"].append(f"{bn}/{a['name']}/{o['name']} : Enum, Trait, DTO ou autre "
                                           f"objet sans equivalent V0 -> ignore")
                    continue
                if o["kind"] == "entity":
                    if o["root"] is None:
                        raise BuildError(f"{bn}/{a['name']}/{o['name']} : propriete aggregateRoot absente")
                    cls, link = (D.RootEntity if o["root"] else D.Entity), D.containsEntity
                else:
                    cls, link = TERM[o["kind"]]
                ou = terms[(bn, a["name"], o["name"])] = node(
                    iri.mint("bc", bn, a["name"], o["name"]), cls, o["name"])
                g.add((au, link, ou))
                for m in o["attributes"] + o["references"]:
                    mu = node(iri.mint("bc", bn, a["name"], o["name"], m["name"]), D.Attribute, m["name"])
                    g.add((ou, D.hasAttribute, mu))
                    g.add((mu, D.attributeType, Literal(m.get("type") or m["target"])))
                    if "target" in m:
                        refs.append((mu, m, f"{bn}/{a['name']}/{o['name']}.{m['name']}"))

    by_name = defaultdict(list)
    for (_, _, on), ou in terms.items():
        by_name[on].append(ou)
    for mu, m, where in refs:
        if m["target_bc"] and m["target_aggregate"]:
            tu = terms.get((m["target_bc"], m["target_aggregate"], m["target"]))
        else:                                              # proprietaire inconnu : par le nom, si sans ambiguite
            tu = by_name[m["target"]][0] if len(by_name[m["target"]]) == 1 else None
        if tu is None:
            rep["warnings"].append(f"{where} : cible '{m['target']}' non resolue (Enum/DTO ignore, "
                                   f"ou nom ambigu) -> pas de ddd:refersTo")
        else:
            g.add((mu, D.refersTo, tu))

    def relationship(r):
        u = relationship_node(r)
        if r["implementation_technology"]:
            g.add((u, D.implementationTechnology, Literal(r["implementation_technology"])))
        return u

    def relationship_node(r):
        if r["kind"] == "symmetric":
            u = node(iri.mint("rel", iri.rel_key(r["name"], participants=r["participants"])),
                     D.Partnership if r["subtype"] == "Partnership" else D.SharedKernel, r["name"])
            for p in r["participants"]:
                g.add((u, D.hasParticipant, URIRef(iri.mint("bc", p))))
            return u
        up, down = r["upstream"], r["downstream"]
        u = node(iri.mint("rel", iri.rel_key(r["name"], upstream=up, downstream=down)),
                 D.CustomerSupplierRelationship if r["customer_supplier"] else D.UpstreamDownstreamRelationship,
                 r["name"])
        g.add((u, D.upstream, URIRef(iri.mint("bc", up))))
        g.add((u, D.downstream, URIRef(iri.mint("bc", down))))
        for key, prop in (("upstream_roles", D.hasUpstreamRole), ("downstream_roles", D.hasDownstreamRole)):
            for abbr in sorted(r[key]):
                if abbr not in ROLE:
                    raise BuildError(f"relation {up} -> {down} : role '{abbr}' inconnu (attendu : {sorted(ROLE)})")
                g.add((u, prop, node(str(u) + "/" + abbr, ROLE[abbr], None)))
        for ag in r["exposes_aggregates"]:
            if (up, ag) in aggs:
                g.add((u, D.exposesAggregate, aggs[(up, ag)]))
            else:
                rep["warnings"].append(f"relation {up} -> {down} : exposedAggregates '{ag}' "
                                       f"n'est pas un agregat de {up}")
        return u

    for cm in j["context_maps"]:
        mu = node(iri.mint("map", cm["name"]), D.ContextMap, cm["name"])
        if cm["type"] not in UNSET:
            g.add((mu, D.contextMapType, Literal(cm["type"])))
        if cm["state"] not in UNSET:
            g.add((mu, D.contextMapState, Literal(cm["state"])))
        for c in cm["contexts"]:
            g.add((mu, D.showsRelevantContext, URIRef(iri.mint("bc", c))))
        for r in cm["relationships"]:
            g.add((mu, D.showsRelationship, relationship(r)))
    return g, rep


def print_report(g, rep, path):
    """Resume affiche apres ecriture : taille, noeuds par classe, avertissements."""
    print(f"{path} : {len(g)} triplets  (base IRI : {iri.BASE})")
    print("  noeuds :", ", ".join(f"{k}={v}" for k, v in sorted(rep["counts"].items())))
    for w in rep["warnings"]:
        print("  AVERTISSEMENT :", w)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--validate", action="store_true", help="valide aussi l'artefact (SHACL, puis HermiT)")
    ap.add_argument("--no-hermit", action="store_true", help="avec --validate : saute HermiT (pas de Java)")
    a = ap.parse_args()
    try:
        g, rep = build(json.load(open(a.json, encoding="utf-8")))
    except (BuildError, KeyError, ValueError) as e:
        print("ERREUR :", f"champ manquant ou invalide dans le JSON : {e}" if isinstance(e, KeyError) else e,
              file=sys.stderr)
        return 1
    g.serialize(a.out, format="turtle")
    print_report(g, rep, a.out)
    if not a.validate:
        return 0
    import validate_artifact as va          # charge seulement si demande
    findings = va.validate(va.load(f"{ROOT}/ddd-metamodel.ttl"), va.load(f"{ROOT}/shapes.ttl"), g,
                           hermit=not a.no_hermit)
    if findings:
        print(f"INVALIDE ({findings[0]['stage']}) :")
        for f in findings:
            print("  -", va.format_finding(f))
        return 1
    print("VALIDE : vocabulaire et SHACL" + ("" if a.no_hermit else " et HermiT") + " passent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
