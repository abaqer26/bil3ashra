#!/usr/bin/env python3
"""يضيف فئات جديدة مدققة لـ bank.js: python3 merge_new.py <fixes.json> <id> [<id>...]
يقرا questions/drafts/new-<id>.json، ويطبّق تصحيحات المدقق (العنوان الأصلي ← الكائن المصحح، أو null للمرفوض)."""
import json, os, sys
J = lambda v: json.dumps(v, ensure_ascii=False)
fixes = json.load(open(sys.argv[1], encoding="utf-8")) if sys.argv[1] != "-" else {}
s = open("bank.js", encoding="utf-8").read()
out = ""; added = 0
for cid in sys.argv[2:]:
    c = json.load(open(f"questions/drafts/new-{cid}.json", encoding="utf-8"))
    lists = []
    for l in c["lists"]:
        if l["t"] in fixes:
            if fixes[l["t"]] is None: print("  rejected:", l["t"][:50]); continue
            l = fixes[l["t"]]; print("  fixed:", l["t"][:50])
        assert len(l["a"]) == 10 and len(l["h"]) == 10 and len(l["x"]) == 3, l["t"]
        assert J(l["t"]) not in s, "duplicate title " + l["t"]
        lists.append(l)
    c["lists"] = lists
    out += '\n  { id:"%s", name:"%s", icon:"", lists:[\n' % (c["id"], c["name"])
    out += "".join("    { t:%s, a:%s, h:%s, x:%s },\n" % (J(l["t"]), J(l["a"]), J(l["h"]), J(l["x"])) for l in lists) + "  ]},"
    json.dump(c, open(f"questions/approved/2026-11-22-new-{cid}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.remove(f"questions/drafts/new-{cid}.json"); added += len(lists)
    print(cid, len(lists))
k = s.rindex("\n];"); s = s[:k] + out + s[k:]
open("bank.js", "w", encoding="utf-8").write(s)
print("added", added, "| total lists", s.count("{ t:"), "| categories", s.count('id:"'))
