#! /usr/bin/env python3

# Imports HTML files exported from Evernote.

from lxml import etree, html
from markdownify import markdownify

def parse_meta(meta):
    return meta.get("itemprop"), meta.get("content")

def get_props(note):
    props = {}
    for thing in note:
        if thing.tag == "meta":
            meta = parse_meta(thing)
            props[meta[0]] = meta[1]
    return props
def import_note(path):
    with open(path) as evernote:
        body = html.fromstring(evernote.read()).body
        html_note = body[1]
        #  [print("class: " + cl) for cl in html_note.classes]
        props = get_props(html_note)
        raw_html = etree.tostring(html_note).decode()
        markdown = markdownify(raw_html, )
        print(f"Note {props}\n{markdown}")

if __name__ == "__main__":
    import_note("/Users/david/Documents/EvernoteExport/Blog/Missing and bombing..html")
