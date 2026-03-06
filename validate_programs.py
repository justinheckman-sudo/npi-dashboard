#!/usr/bin/env python3
"""
validate_programs.py — Schema integrity checker for data/programs.yaml
Usage: python validate_programs.py data/programs.yaml
Exits 0 on valid, exits 1 with error list on invalid.
"""
import sys
import yaml

REQUIRED_TOP_KEYS = {
    "id", "name", "phase", "one_pager_url", "last_updated",
    "last_milestone", "next_gate", "milestones", "decisions", "risks"
}
REQUIRED_MILESTONE_KEYS = {"name", "date"}
REQUIRED_GATE_KEYS = {"name", "date", "exit_criteria"}
REQUIRED_DECISION_KEYS = {"name", "owner", "deadline"}
REQUIRED_RISK_KEYS = {"name", "owner"}
FORBIDDEN_KEYS = {"color", "health", "rag", "status", "score", "severity", "confidence"}


def check_program(prog):
    errors = []
    pid = prog.get("id", "?")
    missing = REQUIRED_TOP_KEYS - set(prog.keys())
    if missing:
        errors.append(f"[{pid}] missing required keys: {sorted(missing)}")
    forbidden = FORBIDDEN_KEYS & set(prog.keys())
    if forbidden:
        errors.append(f"[{pid}] forbidden keys found (DATA-02 violation): {sorted(forbidden)}")
    lm = prog.get("last_milestone", {})
    if isinstance(lm, dict):
        missing_lm = REQUIRED_MILESTONE_KEYS - set(lm.keys())
        if missing_lm:
            errors.append(f"[{pid}] last_milestone missing: {sorted(missing_lm)}")
    ng = prog.get("next_gate", {})
    if isinstance(ng, dict):
        missing_ng = REQUIRED_GATE_KEYS - set(ng.keys())
        if missing_ng:
            errors.append(f"[{pid}] next_gate missing: {sorted(missing_ng)}")
    for i, d in enumerate(prog.get("decisions", []) or []):
        missing_d = REQUIRED_DECISION_KEYS - set(d.keys())
        if missing_d:
            errors.append(f"[{pid}] decisions[{i}] missing: {sorted(missing_d)}")
    for i, r in enumerate(prog.get("risks", []) or []):
        missing_r = REQUIRED_RISK_KEYS - set(r.keys())
        if missing_r:
            errors.append(f"[{pid}] risks[{i}] missing: {sorted(missing_r)}")
    return errors


if len(sys.argv) < 2:
    print("Usage: python validate_programs.py <path-to-programs.yaml>")
    sys.exit(1)

with open(sys.argv[1]) as f:
    data = yaml.safe_load(f)

programs = data.get("programs", [])
all_errors = []
for prog in programs:
    all_errors.extend(check_program(prog))

if all_errors:
    print(f"VALIDATION FAILED — {len(all_errors)} error(s):")
    for e in all_errors:
        print(f"  {e}")
    sys.exit(1)
else:
    print(f"OK — {len(programs)} programs validated, schema clean")
