import re, sys

TOK = re.compile(r"<!--.*?-->|<\?.*?\?>|<[^>]+>|[^<]+", re.S)

def analyse(path):
    raw = open(path, "rb").read()
    s = raw.decode("utf-8")
    res = dict(lines=0, bad_indent=0, multi_tag=0, tabs=0, trailing_ws=0, blank=0, crlf=b"\r\n" in raw, final_nl=raw.endswith(b"\n"), units=set(), examples=[])
    depth = 0
    for n, line in enumerate(s.splitlines(), 1):
        res["lines"] += 1
        if not line.strip():
            res["blank"] += 1; continue
        if "\t" in line: res["tabs"] += 1
        if line != line.rstrip(): res["trailing_ws"] += 1
        body = line.strip()
        toks = [t for t in TOK.findall(body) if t.strip()]
        tags = [t for t in toks if t.startswith("<") and not t.startswith(("<?", "<!--"))]
        closes_first = body.startswith("</")
        exp_depth = depth - 1 if closes_first else depth
        lead = len(line) - len(line.lstrip(" "))
        res["units"].add(lead)
        if lead != 2 * exp_depth:
            res["bad_indent"] += 1
            if len(res["examples"]) < 3: res["examples"].append(f"riga {n}: rientro {lead}, atteso {2*exp_depth}")
        opens = sum(1 for t in tags if not t.startswith("</") and not t.endswith("/>"))
        closes = sum(1 for t in tags if t.startswith("</"))
        if len(tags) > 2 or (len(tags) == 2 and not (tags[1].startswith("</") and not tags[0].startswith("</"))):
            res["multi_tag"] += 1
        depth += opens - closes
    return res

if __name__ == "__main__":
    for p in sys.argv[1:]:
        r = analyse(p)
        ok = not (r["bad_indent"] or r["multi_tag"] or r["tabs"] or r["trailing_ws"] or r["crlf"] or not r["final_nl"])
        print(f"{'OK  ' if ok else 'PROB'} {p}: righe={r['lines']} rientro errato={r['bad_indent']} piu'tag/riga={r['multi_tag']} tab={r['tabs']} spazi finali={r['trailing_ws']} righe vuote={r['blank']} CRLF={r['crlf']} newline finale={r['final_nl']}")
        for e in r["examples"]: print("        ", e)
