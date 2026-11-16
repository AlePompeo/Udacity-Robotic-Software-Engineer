"""Whitespace-only XML re-indenter that keeps every tag, attribute and quote exactly as in the source."""
import re

TOK = re.compile(r"<!--.*?-->|<\?.*?\?>|<![^>]*>|<[^>]+>|[^<]+", re.S)


class N:
    def __init__(self, kind, open_="", name="", close=""):
        self.kind, self.open, self.name, self.close = kind, open_, name, close
        self.children, self.text, self.self_closed = [], "", False


def parse(src):
    root = N("root")
    stack = [root]
    for t in TOK.findall(src):
        if t.startswith(("<?", "<!--", "<!")):
            stack[-1].children.append(N("raw", t))
        elif t.startswith("</"):
            n = stack.pop()
            n.close = t.strip()
        elif t.startswith("<"):
            nm = re.match(r"<\s*([^\s/>]+)", t).group(1)
            n = N("el", t.strip(), nm)
            stack[-1].children.append(n)
            if t.rstrip().endswith("/>"):
                n.self_closed = True
            else:
                stack.append(n)
        elif t.strip():
            stack[-1].text += t
    assert len(stack) == 1, "tag non chiusi"
    return root


def emit(root, indent="  "):
    out = []

    def go(n, d):
        pad = indent * d
        if n.kind == "raw":
            out.append(pad + n.open)
        elif n.self_closed:
            out.append(pad + n.open)
        elif not n.children:
            out.append(pad + n.open + n.text.strip() + n.close)
        else:
            out.append(pad + n.open)
            for c in n.children:
                go(c, d + 1)
            out.append(pad + n.close)

    for c in root.children:
        go(c, 0)
    return "\n".join(out) + "\n"


def find(n, name, **attrs):
    for c in n.children:
        if c.kind == "el" and c.name == name and all(f"{k}='{v}'" in c.open or f'{k}="{v}"' in c.open for k, v in attrs.items()):
            return c
    return None
