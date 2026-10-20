#!/usr/bin/env python3
"""Regenerates tools/sa_mobile_commands.json for scm_asm.py.

Keeps only the commands used by the given sources, taken from the
Sanny Builder library (https://github.com/sannybuilder/library):

    git clone --depth 1 https://github.com/sannybuilder/library.git
    python3 tools/update_commands.py library/sa_mobile/sa_mobile.json mods/*/*.txt
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# CLEO Android reads the result variable of these opcodes BEFORE the inputs
# (checked in libcleo.so: 0DE0 = var, 2 ints; 0DE1 = var, 4 ints;
# 0DD8 = var, 3 ints; ...), unlike the input-then-output order of the
# library description.
OUTPUT_FIRST = {"0DE0", "0DE1", "0DE2", "0DE3", "0DD8"}

# Opcodes added by CLEO Mod for AML 2.0.1.5 (AndroidModLoader/GTA_CLEOMod,
# cleo4opcodes.cpp), missing from the sa_mobile library.
EXTRA = {
    "ADD_TEXT_LABEL": {"id": "0ADF", "in": ["string", "string"], "out": [], "cond": False},
    "ALLOCATE_MEMORY": {"id": "0AC8", "in": ["int"], "out": ["int"], "cond": False},
    "FREE_MEMORY": {"id": "0AC9", "in": ["int"], "out": [], "cond": False},
}


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    with open(argv[0]) as f:
        library = json.load(f)
    all_cmds = {}
    for ext in library["extensions"]:
        for c in ext["commands"]:
            attrs = c.get("attrs", {})
            if attrs.get("is_unsupported") or attrs.get("is_nop"):
                continue
            if c["name"] in all_cmds and ext["name"] == "default":
                continue
            all_cmds[c["name"]] = {
                "id": c["id"],
                "in": [p["type"] for p in c.get("input", [])],
                "out": [p["type"] for p in c.get("output", [])],
                "cond": bool(attrs.get("is_condition")),
            }
            if c["id"] in OUTPUT_FIRST:
                all_cmds[c["name"]]["out_first"] = True
    all_cmds.update(EXTRA)
    used = set()
    for path in argv[1:]:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.split("//")[0].split()
                if line and line[0] == "NOT":
                    line = line[1:]
                if line and re.fullmatch(r"[A-Z0-9_]+", line[0]) and line[0] in all_cmds:
                    used.add(line[0])
    missing = [n for n in ("IF", "GOTO_IF_FALSE") if n not in used]
    used.update(missing)
    data = {
        "source": "sannybuilder/library sa_mobile.json v%s" % library["meta"]["version"],
        "commands": {n: all_cmds[n] for n in sorted(used)},
    }
    out = os.path.join(HERE, "sa_mobile_commands.json")
    with open(out, "w") as f:
        json.dump(data, f, indent=1, sort_keys=True)
        f.write("\n")
    print("%s: %d commands" % (out, len(used)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
