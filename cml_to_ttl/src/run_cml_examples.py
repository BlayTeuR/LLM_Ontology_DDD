"""Lance main_cml_to_ttl.py sur chaque fichier de cml_tests/ et compare au en-tete `// EXPECT:`.

    python run_cml_examples.py [dossier]            (defaut : cml_tests/ a cote de ce fichier)

Un en-tete `// EXPECT: Classe=n ... predicat=n` compte, dans le .ttl produit, les individus par
classe (BoundedContext, Aggregate, Attribute...) et les triplets par propriete (refersTo,
exposesAggregate, responsibility, domainVisionStatement, implementsPartOf). Une cle absente
n'est pas verifiee, mais toute classe produite et non annoncee est signalee.
`// EXPECT: ERROR <texte>` : la conversion doit echouer et le message doit contenir <texte>.
Ces comptes sont ecrits a la main, pas calcules par le convertisseur.
"""
import glob
import os
import re
import subprocess
import sys
from collections import Counter

from rdflib import Graph, RDF

import iri

HERE = os.path.dirname(os.path.abspath(__file__))
D = iri.D
PREDICATES = {"refersTo", "exposesAggregate", "responsibility", "domainVisionStatement",
              "implementsPartOf", "hasAttribute", "implementationTechnology"}


def expectation(path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = re.match(r"\s*//\s*EXPECT:\s*(.*)", line)
            if m:
                return m.group(1).strip()
    return None


def counts(ttl):
    g = Graph()
    g.parse(ttl, format="turtle")
    c = Counter()
    for _, _, cls in g.triples((None, RDF.type, None)):
        if str(cls).startswith(str(D)):
            c[str(cls)[len(str(D)):]] += 1
    for p in PREDICATES:
        c[p] = sum(1 for _ in g.triples((None, D[p], None)))
    return c


def run_one(cml, out):
    exp = expectation(cml)
    r = subprocess.run([sys.executable, os.path.join(HERE, "main_cml_to_ttl.py"), cml, "--out", out],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    msg = (r.stdout + r.stderr).strip()
    if exp is None:
        return "?", "pas d'en-tete // EXPECT:"
    if exp.startswith("ERROR"):
        want = exp[len("ERROR"):].strip()
        if r.returncode == 0:
            return "ECART", f"erreur attendue ('{want}') mais la conversion a reussi"
        return ("OK", f"erreur attendue obtenue ('{want}')") if want in msg else \
               ("ECART", f"erreur differente de '{want}' :\n{msg}")
    if r.returncode != 0:
        return "ECART", "conversion en echec :\n" + msg
    want = {k: int(v) for k, v in (kv.split("=") for kv in exp.split())}
    stem = os.path.splitext(os.path.basename(cml))[0]
    got = counts(os.path.join(out, "ttl", stem + ".ttl"))
    diffs = [f"{k}: attendu {v}, obtenu {got.get(k, 0)}" for k, v in want.items() if got.get(k, 0) != v]
    extra = [f"{k}={v} (non annonce)" for k, v in got.items()
             if k not in want and v and k not in PREDICATES]
    warns = [l.strip() for l in r.stdout.splitlines() if "AVERTISSEMENT" in l]
    detail = diffs + ([f"classes non annoncees : {', '.join(extra)}"] if extra else []) + warns
    return ("ECART" if diffs else "OK"), "\n    ".join(detail)


def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "cml_tests")
    out = os.path.join(HERE, "output_cml", "examples")
    files = sorted(glob.glob(os.path.join(folder, "*.cml")))
    if not files:
        print("aucun .cml dans", folder)
        return 1
    bad = 0
    for f in files:
        status, detail = run_one(f, out)
        bad += status != "OK"
        print(f"{status:6} {os.path.basename(f)}" + (f"\n    {detail}" if detail else ""))
    print(f"\n{len(files) - bad}/{len(files)} conformes")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
