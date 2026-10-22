"""CML -> JSON -> TTL in a single command.

    python cml_to_ttl/src/main_cml_to_ttl.py examples/insurance/insurance.cml     (from the repository root)

    cml_to_ttl/output_cml/json/insurance.json   (step 1: official parser, cml_to_json.py)
    cml_to_ttl/output_cml/ttl/insurance.ttl     (step 2: OWL metamodel, cml2ttl.py)

The output folder can be changed with --out. The export-json.ftl template is read
from cml_to_ttl/cm-probe/, outside src/. No validation here: logical consistency
is checked afterwards with reasoner/reason.py (HermiT).
"""
import argparse
import json
import os
import sys

from cml2ttl import BuildError, build, print_report
from cml_to_json import ExportError, export_json

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TEMPLATE = os.path.join(ROOT, "cm-probe", "export-json.ftl")
DEFAULT_OUT = os.path.join(ROOT, "output_cml")


def main():
    ap = argparse.ArgumentParser(description="Convert a .cml file to .json, then to .ttl.")
    ap.add_argument("cml", help=".cml file to convert")
    ap.add_argument("--out", default=DEFAULT_OUT, help=f"output folder (default: {DEFAULT_OUT})")
    a = ap.parse_args()

    stem = os.path.splitext(os.path.basename(a.cml))[0]
    json_path = os.path.join(a.out, "json", stem + ".json")
    ttl_path = os.path.join(a.out, "ttl", stem + ".ttl")

    try:
        print(f"[1/2] {a.cml} -> {json_path}")
        export_json(a.cml, json_path, TEMPLATE)
        print(f"[2/2] {json_path} -> {ttl_path}")
        with open(json_path, encoding="utf-8") as f:
            g, rep = build(json.load(f))
    except (ExportError, BuildError) as e:
        print("ERROR:", e, file=sys.stderr)
        return 1
    except (KeyError, ValueError) as e:
        print(f"ERROR: unexpected JSON ({e!r}). Check that the template is export-json.ftl.",
              file=sys.stderr)
        return 1

    os.makedirs(os.path.dirname(ttl_path), exist_ok=True)
    g.serialize(ttl_path, format="turtle")
    print_report(g, rep, ttl_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
