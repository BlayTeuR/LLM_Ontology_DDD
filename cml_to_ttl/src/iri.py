"""Minting of instance IRIs: ONE single function, shared by both routes.

Rules (see also the README of the conversation):
  - deterministic: same names + same structure => same IRI, on every run;
  - independent of the file, the line, and the order within the file;
  - built only from what can be written where the element is REFERENCED in CML
    (a BC referenced by its name alone, a subdomain by its name alone)
    => no "domain" segment in a subdomain's IRI;
  - nested under the context for whatever only makes sense within a context
    (aggregate, entity, value object, event) => homonyms in two contexts
    get different IRIs;
  - the relationship TYPE is not part of the IRI (changing [U,S] to [P] must not
    create a new node);
  - symmetric relationship: sorted names (A<->B == B<->A); unnamed relationship:
    "<upstream>--<downstream>".

BASE is THE configuration variable to change (or the KG_BASE environment
variable). example.org is reserved (RFC 2606): placeholder value only.
"""
import os
from urllib.parse import quote

from rdflib import Graph, Namespace, RDF, URIRef

BASE = os.environ.get("KG_BASE", "https://example.org/kg/insurance/")
if not BASE.endswith("/"):
    BASE += "/"

DDD_NS = "https://example.org/ddd-metamodel#"   # same: to be replaced, once only
D = Namespace(DDD_NS)

KINDS = ("map", "domain", "subdomain", "bc", "rel")

ROLE_ABBR = {
    D.OpenHostService: "OHS",
    D.PublishedLanguage: "PL",
    D.AnticorruptionLayer: "ACL",
    D.Conformist: "CF",
}


def seg(name: str) -> str:
    """One IRI segment: every character outside [A-Za-z0-9_.~-] is encoded as %XX."""
    return quote(name, safe="")


def mint(kind: str, *path: str) -> str:
    if kind not in KINDS:
        raise ValueError(f"unknown IRI kind: {kind!r} (expected: {KINDS})")
    if not path or any(not p for p in path):
        raise ValueError(f"empty segment in {path!r}")
    return BASE + kind + "/" + "/".join(seg(p) for p in path)


def rel_key(name=None, upstream=None, downstream=None, participants=None) -> str:
    if name:
        return name
    if participants:
        return "--".join(sorted(participants))
    return f"{upstream}--{downstream}"


# ----------------------------------------------------------------------------
# LLM route: the LLM proposes arbitrary IRIs; the pipeline replaces them with
# the IRIs minted here, from the ddd:name values and the structure. Thus the
# LLM never decides the identity of a node.
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
    """Return (rewritten_graph, old->new IRI mapping, errors).

    The errors are worded so they can be sent back to the LLM (correction loop).
    """
    errors, m = [], {}

    def name(n):
        v = g.value(n, D.name)
        if v is None or not str(v).strip():
            errors.append(f"{n}: ddd:name missing, cannot compute its identity")
            return None
        return str(v)

    def assign(node, iri):
        if node in m and str(m[node]) != iri:
            errors.append(f"{node}: two possible identities ({m[node]} / {iri})")
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
            errors.append(f"{node}: Aggregate attached to no BoundedContext (hasAggregate)")
    for node in _subjects(g, [D.Entity, D.RootEntity, D.ValueObject, D.DomainEvent]):
        if node not in m:
            errors.append(f"{node}: element attached to no Aggregate")

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
            errors.append(f"{rel}: relationship with no upstream/downstream nor participants")
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
                    errors.append(f"{role}: role of unknown type")

    # collisions: two different nodes -> same IRI = real duplicate
    seen = {}
    for old, new in m.items():
        if new in seen and seen[new] != old:
            errors.append(f"duplicate: {seen[new]} and {old} would have the same identity {new}")
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
