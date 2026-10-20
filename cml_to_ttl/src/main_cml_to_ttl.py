"""CML -> JSON -> TTL en une commande.

    python src/main_cml_to_ttl.py cml_example/insurance.cml     (depuis la racine du projet)

    output_cml/json/insurance.json   (etape 1 : parseur officiel, cml_to_json.py)
    output_cml/ttl/insurance.ttl     (etape 2 : metamodele OWL, cml2ttl.py)

Le dossier de sortie se change avec --out. Le gabarit export-json.ftl est lu
dans cm-probe/ (a la racine du projet, hors de src/). Aucune validation ici
(SHACL/HermiT : option --validate de cml2ttl.py, a part).
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
    ap = argparse.ArgumentParser(description="Convertit un fichier .cml en .json puis en .ttl.")
    ap.add_argument("cml", help="fichier .cml a convertir")
    ap.add_argument("--out", default=DEFAULT_OUT, help=f"dossier de sortie (defaut : {DEFAULT_OUT})")
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
        print("ERREUR :", e, file=sys.stderr)
        return 1
    except (KeyError, ValueError) as e:
        print(f"ERREUR : JSON inattendu ({e!r}). Verifie que le gabarit est export-json.ftl.",
              file=sys.stderr)
        return 1

    os.makedirs(os.path.dirname(ttl_path), exist_ok=True)
    g.serialize(ttl_path, format="turtle")
    print_report(g, rep, ttl_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
