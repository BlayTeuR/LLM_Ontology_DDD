"""Step 1: CML -> JSON, with the official Context Mapper parser (`cm` command).

First validates the CML (`cm validate`, since `cm generate` accepts an invalid CML), then calls
exactly what you would run by hand:
    cm generate -i <file.cml> -g generic -t ./export-json.ftl -o <folder> -f <name>.json
The template is run from its own folder with the ./ prefix (without it, `cm` crashes
with "baseDir is null" on Windows).
"""
import os
import shutil
import subprocess


class ExportError(Exception):
    pass


def _rel(path, start):
    """Path relative to `start` (avoids sending cm an absolute path with accents and spaces)."""
    try:
        return os.path.relpath(path, start)
    except ValueError:                      # different drive on Windows
        return os.path.abspath(path)


def export_json(cml_path, json_path, template, cm="cm"):
    exe = shutil.which(cm)
    if not exe:
        raise ExportError(f"command '{cm}' not found in the PATH (Context Mapper CLI).")
    for label, p in (("CML file", cml_path), ("Freemarker template", template)):
        if not os.path.isfile(p):
            raise ExportError(f"{label} not found: {p}")

    out_dir = os.path.dirname(os.path.abspath(json_path))
    os.makedirs(out_dir, exist_ok=True)
    if os.path.exists(json_path):           # never reuse an old JSON if cm fails
        os.remove(json_path)

    cwd = os.path.dirname(os.path.abspath(template))

    # `cm generate` accepts an invalid CML (code 0, no message): we validate first.
    # `cm validate` also returns 0 on error, so we read its "ERROR" lines.
    v = subprocess.run([exe, "validate", "-i", _rel(cml_path, cwd)], cwd=cwd,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    errors = [l.strip() for l in (v.stdout + v.stderr).splitlines() if l.strip().startswith("ERROR")]
    if errors:
        raise ExportError("Invalid CML (cm validate):\n" + "\n".join(errors))

    cmd = [exe, "generate",
           "-i", _rel(cml_path, cwd),
           "-g", "generic",
           "-t", "./" + os.path.basename(template),
           "-o", _rel(out_dir, cwd),
           "-f", os.path.basename(json_path)]
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if not os.path.isfile(json_path):
        raise ExportError("cm did not produce the JSON.\n" + (r.stdout + r.stderr).strip())
    return json_path
