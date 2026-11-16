#!/usr/bin/env python3
"""Check (and optionally fix) name uniqueness in SDF model files.

Rules checked (sdformat 9 / Gazebo 11):
  * link / joint / frame / nested-model names are unique inside a model;
  * collision / visual / sensor / light / projector / audio_* names are unique inside a link
    (a collision and a visual may NOT share the same name);
  * no empty names, no "::" in names.
Usage: sdf_names.py [--fix] file.sdf [...]
"""
import sys, collections
import xml.etree.ElementTree as ET

MODEL_SCOPE = ("link", "joint", "frame", "model")
LINK_SCOPE = ("collision", "visual", "sensor", "light", "projector", "audio_sink", "audio_source", "battery")


def check_scope(parent, tags, fix, where, report):
    seen = collections.Counter()
    for child in parent:
        if child.tag in tags:
            n = child.get("name")
            if not n or "::" in n:
                report.append(f"{where}: nome non valido in <{child.tag}> ({n!r})")
                continue
            seen[n] += 1
    used = set(seen)
    for child in parent:
        if child.tag in tags and child.get("name") and seen[child.get("name")] > 1:
            n = child.get("name")
            if n in seen and seen[n] > 1:
                # keep the first one with this name, rename the others
                first = next(c for c in parent if c.tag in tags and c.get("name") == n)
                if child is first:
                    continue
                new = f"{n}_{child.tag}"
                k = 2
                while new in used:
                    new = f"{n}_{child.tag}{k}"
                    k += 1
                report.append(f"{where}: nome duplicato '{n}' ({child.tag}) -> {'rinominato in ' + new if fix else 'DA CORREGGERE'}")
                if fix:
                    child.set("name", new)
                    used.add(new)
                else:
                    pass


def process(path, fix):
    tree = ET.parse(path)  # also verifies well-formedness
    root = tree.getroot()
    report = []
    for model in root.iter("model"):
        check_scope(model, MODEL_SCOPE, fix, f"{path} model '{model.get('name')}'", report)
        for link in model.findall("link"):
            check_scope(link, LINK_SCOPE, fix, f"{path} link '{link.get('name')}'", report)
    if fix and any("rinominato" in r for r in report):
        ET.indent(tree, space="  ")
        tree.write(path, encoding="unicode", xml_declaration=True)
    return report


if __name__ == "__main__":
    args = sys.argv[1:]
    fix = "--fix" in args
    files = [a for a in args if not a.startswith("--")]
    bad = 0
    for f in files:
        rep = process(f, fix)
        print(f"{'OK  ' if not rep else 'PROB'} {f}")
        for r in rep:
            print("      ", r)
            bad += 1
    sys.exit(1 if (bad and not fix) else 0)
