"""Etape 1 : CML -> JSON, avec le parseur officiel de Context Mapper (commande `cm`).

Appelle exactement ce que tu lances a la main :
    cm generate -i <fichier.cml> -g generic -t ./export-json-v03.ftl -o <dossier> -f <nom>.json
Le gabarit est lance depuis son propre dossier avec le prefixe ./ (sans lui, `cm` plante
avec « baseDir is null » sous Windows).
"""
import os
import shutil
import subprocess


class ExportError(Exception):
    pass


def _rel(path, start):
    """Chemin relatif a `start` (evite d'envoyer a cm un chemin absolu avec accents et espaces)."""
    try:
        return os.path.relpath(path, start)
    except ValueError:                      # autre disque sous Windows
        return os.path.abspath(path)


def export_json(cml_path, json_path, template, cm="cm"):
    exe = shutil.which(cm)
    if not exe:
        raise ExportError(f"commande '{cm}' introuvable dans le PATH (Context Mapper CLI).")
    for label, p in (("fichier CML", cml_path), ("gabarit Freemarker", template)):
        if not os.path.isfile(p):
            raise ExportError(f"{label} introuvable : {p}")

    out_dir = os.path.dirname(os.path.abspath(json_path))
    os.makedirs(out_dir, exist_ok=True)
    if os.path.exists(json_path):           # jamais reutiliser un ancien JSON si cm echoue
        os.remove(json_path)

    cwd = os.path.dirname(os.path.abspath(template))
    cmd = [exe, "generate",
           "-i", _rel(cml_path, cwd),
           "-g", "generic",
           "-t", "./" + os.path.basename(template),
           "-o", _rel(out_dir, cwd),
           "-f", os.path.basename(json_path)]
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if not os.path.isfile(json_path):
        raise ExportError("cm n'a pas produit le JSON.\n" + (r.stdout + r.stderr).strip())
    return json_path
