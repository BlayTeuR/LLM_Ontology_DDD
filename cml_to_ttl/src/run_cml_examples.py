"""Run main_cml_to_ttl.py on each file in cml_tests/ and compare against the `// EXPECT:` header.

    python src/run_cml_examples.py [folder]        (default: cml_tests/ at the project root)

An `// EXPECT: Class=n ... predicate=n` header counts, in the produced .ttl, the individuals per
class (BoundedContext, Aggregate, Attribute...) and the triples per property (refersTo,
exposesAggregate, responsibility, domainVisionStatement, implementsPartOf). A missing key
is not checked, but any class that is produced and not announced is reported.
`// EXPECT: ERROR <text>`: the conversion must fail and the message must contain <text>.
These counts are written by hand, not computed by the converter.
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
ROOT = os.path.dirname(HERE)
D = iri.D
PREDICATES = {"refersTo", "exposesAggregate", "responsibility", "domainVisionStatement",
              "implementsPartOf", "hasAttribute", "implementationTechnology",
              "ownedBy", "bcType", "contextMapType", "contextMapState"}


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
        return "?", "no // EXPECT: header"
    if exp.startswith("ERROR"):
        want = exp[len("ERROR"):].strip()
        if r.returncode == 0:
            return "MISMATCH", f"expected error ('{want}') but the conversion succeeded"
        return ("OK", f"expected error obtained ('{want}')") if want in msg else \
               ("MISMATCH", f"error different from '{want}':\n{msg}")
    if r.returncode != 0:
        return "MISMATCH", "conversion failed:\n" + msg
    want = {k: int(v) for k, v in (kv.split("=") for kv in exp.split())}
    stem = os.path.splitext(os.path.basename(cml))[0]
    got = counts(os.path.join(out, "ttl", stem + ".ttl"))
    diffs = [f"{k}: expected {v}, got {got.get(k, 0)}" for k, v in want.items() if got.get(k, 0) != v]
    extra = [f"{k}={v} (not announced)" for k, v in got.items()
             if k not in want and v and k not in PREDICATES]
    warns = [l.strip() for l in r.stdout.splitlines() if "WARNING" in l]
    detail = diffs + ([f"classes not announced: {', '.join(extra)}"] if extra else []) + warns
    return ("MISMATCH" if diffs else "OK"), "\n    ".join(detail)


def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "cml_tests")
    out = os.path.join(ROOT, "output_cml", "examples")
    files = sorted(glob.glob(os.path.join(folder, "*.cml")))
    if not files:
        print("no .cml in", folder)
        return 1
    bad = 0
    for f in files:
        status, detail = run_one(f, out)
        bad += status != "OK"
        print(f"{status:8} {os.path.basename(f)}" + (f"\n    {detail}" if detail else ""))
    print(f"\n{len(files) - bad}/{len(files)} passed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
