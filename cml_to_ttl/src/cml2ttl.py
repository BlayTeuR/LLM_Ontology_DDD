"""CML -> OWL artifact (Turtle), from the JSON exported by the official parser.

    cm generate -i insurance.cml -g generic -t cm-probe/export-json.ftl -o output_cml/json -f insurance.json
    python src/cml2ttl.py output_cml/json/insurance.json -o insurance.ttl

Conversion only: just rdflib and iri.py are needed. The --validate option (SHACL, then HermiT)
is not available: validate_artifact.py does not exist. Logical consistency is checked
with reasoner/reason.py.

Requires Java.

The JSON is the only input; IRIs come from iri.mint; nothing is guessed.
Anything that cannot be converted is REPORTED (warnings), never silently dropped;
whatever makes the artifact inconsistent is an ERROR.
No line number: the generator does not expose them (ddd:sourceLine absent).
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
ROOT = os.path.dirname(HERE)       # project root (parent of src/)
SUBDOMAIN = {"CORE_DOMAIN": D.CoreDomain, "SUPPORTING_DOMAIN": D.SupportingSubdomain,
             "GENERIC_SUBDOMAIN": D.GenericSubdomain}
ROLE = {"OHS": D.OpenHostService, "PL": D.PublishedLanguage,
        "ACL": D.AnticorruptionLayer, "CF": D.Conformist}
UNSET = {"", "UNDEFINED"}      # cm's default value when nothing is written
# kind (JSON) -> (class, property linking the aggregate to the term)
TERM = {"value_object": (D.ValueObject, D.containsValueObject),
        "domain_event": (D.DomainEvent, D.containsDomainEvent)}
META = os.path.join(os.path.dirname(ROOT), "metamodel") 


class BuildError(Exception):
    pass


def build(j):
    g = Graph()
    g.bind("ddd", D)
    src, seen = os.path.basename(j["file"].replace("\\", "/")), {}
    rep = {"counts": Counter(), "warnings": []}
    terms, aggs = {}, {}          # (bc, agg, object) -> IRI ; (bc, agg) -> IRI
    refs = []                     # references to resolve once all terms are created
    bc_names = {b["name"] for b in j["bounded_contexts"]}

    def node(uri, cls, name):
        if uri in seen:
            raise BuildError(f"'{name}' and '{seen[uri]}' produce the same IRI: {uri}")
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
        rep["warnings"].append(f"{len(j['imports'])} import(s) NOT followed (export each file "
                               f"separately): {', '.join(j['imports'])}")

    for d in j["domains"]:
        du = node(iri.mint("domain", d["name"]), D.Domain, d["name"])
        for s in d["subdomains"]:
            if s["type"] not in SUBDOMAIN:
                rep["warnings"].append(f"subdomain {s['name']}: unknown type '{s['type']}' -> Subdomain")
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
                    rep["warnings"].append(f"{bn}/{a['name']}: owner '{a['owner']}' is not a BoundedContext of this file")
                g.add((au, D.ownedBy, URIRef(iri.mint("bc", a["owner"]))))
            for x in a["responsibilities"]:
                g.add((au, D.responsibility, Literal(x)))
            for o in a["objects"]:
                if o["kind"] == "other":
                    rep["warnings"].append(f"{bn}/{a['name']}/{o['name']}: Enum, Trait, DTO or other "
                                           f"object with no V0 equivalent -> ignored")
                    continue
                if o["kind"] == "entity":
                    if o["root"] is None:
                        raise BuildError(f"{bn}/{a['name']}/{o['name']}: aggregateRoot property missing")
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
        else:                                              # unknown owner: by name, if unambiguous
            tu = by_name[m["target"]][0] if len(by_name[m["target"]]) == 1 else None
        if tu is None:
            rep["warnings"].append(f"{where}: target '{m['target']}' unresolved (Enum/DTO ignored, "
                                   f"or ambiguous name) -> no ddd:refersTo")
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
                    raise BuildError(f"relationship {up} -> {down}: unknown role '{abbr}' (expected: {sorted(ROLE)})")
                g.add((u, prop, node(str(u) + "/" + abbr, ROLE[abbr], None)))
        for ag in r["exposes_aggregates"]:
            if (up, ag) in aggs:
                g.add((u, D.exposesAggregate, aggs[(up, ag)]))
            else:
                rep["warnings"].append(f"relationship {up} -> {down}: exposedAggregates '{ag}' "
                                       f"is not an aggregate of {up}")
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
    """Summary printed after writing: size, nodes per class, warnings."""
    print(f"{path}: {len(g)} triples  (base IRI: {iri.BASE})")
    print("  nodes:", ", ".join(f"{k}={v}" for k, v in sorted(rep["counts"].items())))
    for w in rep["warnings"]:
        print("  WARNING:", w)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--validate", action="store_true", help="also validate the artifact (SHACL, then HermiT)")
    ap.add_argument("--no-hermit", action="store_true", help="with --validate: skip HermiT (no Java)")
    a = ap.parse_args()
    try:
        g, rep = build(json.load(open(a.json, encoding="utf-8")))
    except (BuildError, KeyError, ValueError) as e:
        print("ERROR:", f"missing or invalid field in the JSON: {e}" if isinstance(e, KeyError) else e,
              file=sys.stderr)
        return 1
    g.serialize(a.out, format="turtle")
    print_report(g, rep, a.out)
    if not a.validate:
        return 0
    import validate_artifact as va          # loaded only when requested
    findings = va.validate(va.load(os.path.join(META, "ddd-metamodel.ttl")),
                           va.load(os.path.join(META, "shapes.ttl")), g,
                           hermit=not a.no_hermit)
    if findings:
        print(f"INVALID ({findings[0]['stage']}):")
        for f in findings:
            print("  -", va.format_finding(f))
        return 1
    print("VALID: vocabulary and SHACL" + ("" if a.no_hermit else " and HermiT") + " pass.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
