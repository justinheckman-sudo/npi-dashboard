#!/usr/bin/env python3
"""
generate.py — NPI Dashboard generator
Usage: python scripts/generate.py
Reads data/programs.yaml, validates schema, renders templates/index.html.j2, writes index.html.
"""
import sys
import json
import yaml
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
YAML_PATH = REPO_ROOT / "data" / "programs.yaml"
TEMPLATE_DIR = REPO_ROOT / "templates"
TEMPLATE_FILE = "index.html.j2"
OUTPUT_PATH = REPO_ROOT / "index.html"
VALIDATOR_PATH = REPO_ROOT / "validate_programs.py"


def validate(yaml_path: Path) -> bool:
    """Run validate_programs.py as subprocess. Returns True if valid, prints error and exits on failure."""
    result = subprocess.run(
        [sys.executable, str(VALIDATOR_PATH), str(yaml_path)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        output = result.stdout.strip() or result.stderr.strip()
        print(output)
        print("Aborting — index.html not written.")
        sys.exit(1)
    return True


def map_program(p: dict) -> dict:
    """Map programs.yaml schema (snake_case) → JS PROGRAMS object fields (camelCase)."""
    # exit_criteria: comma-delimited string → list
    ec_raw = (p.get("next_gate") or {}).get("exit_criteria", "[NEED UPDATE]") or "[NEED UPDATE]"
    if ec_raw and ec_raw != "[NEED UPDATE]":
        criteria = [c.strip() for c in ec_raw.split(",") if c.strip()]
    else:
        criteria = ["[NEED UPDATE]"]

    return {
        "id": p["id"],
        "name": p["name"],
        "subtitle": "",
        "phase": p["phase"],
        "status": "watch",
        "lastGate": {
            "label": (p.get("last_milestone") or {}).get("name", "[NEED UPDATE]"),
            "date":  (p.get("last_milestone") or {}).get("date", "[NEED UPDATE]"),
        },
        "nextGate": {
            "label":    (p.get("next_gate") or {}).get("name", "[NEED UPDATE]"),
            "date":     (p.get("next_gate") or {}).get("date", "[NEED UPDATE]"),
            "criteria": criteria,
        },
        "risks": [
            {"label": r["name"], "owner": r.get("owner", "[NEED UPDATE]")}
            for r in (p.get("risks") or [])
        ],
        "decisions": [
            {
                "label": d["name"],
                "owner": d.get("owner", "[NEED UPDATE]"),
                "date":  d.get("deadline", "TBD"),
            }
            for d in (p.get("decisions") or [])
        ],
    }


def main():
    import argparse
    from jinja2 import Environment, FileSystemLoader

    parser = argparse.ArgumentParser(description="NPI Dashboard generator")
    parser.add_argument("--yaml", type=Path, default=YAML_PATH,
                        help="Path to programs.yaml (default: data/programs.yaml)")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH,
                        help="Output path for index.html (default: index.html at repo root)")
    args = parser.parse_args()

    yaml_path = args.yaml
    output_path = args.output

    # Step 1: Validate
    validate(yaml_path)

    # Step 2: Load YAML
    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    programs = data["programs"]
    n_programs = len(programs)

    # Step 3: Map fields
    js_programs = [map_program(p) for p in programs]
    programs_json = json.dumps(js_programs, indent=2)

    # Step 4: Render template
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template(TEMPLATE_FILE)
    output = template.render(programs_json=programs_json)

    # Step 5: Write output
    output_path.write_text(output, encoding="utf-8")
    n_lines = output.count("\n") + 1

    print(f"Validation passed ({n_programs} programs)")
    print(f"Generated index.html ({n_lines} lines)")


if __name__ == "__main__":
    main()
