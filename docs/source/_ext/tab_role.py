from docutils import nodes
from docutils.parsers.rst import roles


def tab_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
    # Support syntax: :tab:`Label <ref:target>`
    if "<ref:" in text and ">" in text:
        label, ref = text.split("<ref:", 1)
        ref = ref.rstrip(">")
        label = label.strip()
        node = nodes.reference(rawtext, label, refuri=ref, classes=["tab"])
    elif "<" in text and ">" in text:
        label, uri = text.split("<", 1)
        uri = uri.rstrip(">")
        label = label.strip()
        node = nodes.reference(rawtext, label, refuri=uri, classes=["tab"])
    else:
        node = nodes.inline(rawtext, text, classes=["tab"])
    return [node], []


def setup(app):
    roles.register_local_role("tab", tab_role)
