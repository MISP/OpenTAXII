#!/usr/bin/env python3
"""Render the database's Mermaid sources with the MISP book diagram style."""

import argparse
import json
from pathlib import Path
from xml.etree import ElementTree

from playwright.sync_api import sync_playwright

DIAGRAMS = Path(__file__).resolve().parent / "assets" / "diagrams"
SVG_NS = "{http://www.w3.org/2000/svg}"

RENDER = r"""
async ({id, source, theme, logo}) => {
  mermaid.initialize({...theme.mermaid, deterministicIDSeed: id});
  const result = await mermaid.render(id, source);
  const template = document.createElement("template");
  template.innerHTML = result.svg;
  const svg = template.content.querySelector("svg");
  // Mermaid treats key names such as pk as reserved and accepts an asterisk prefix.
  for (const label of svg.querySelectorAll("text tspan")) {
    if (/^\*(?:pk|fk|uk)$/i.test(label.textContent)) {
      label.textContent = label.textContent.slice(1);
    }
  }
  const [x, y, width, height] = svg.getAttribute("viewBox").split(/\s+/).map(Number);
  const {padding, headerHeight, graphGap, background, border, logoWidth, logoTop} =
    theme.frame;
  const frameWidth = Math.max(width, logoWidth) + padding * 2;
  const graphTop = headerHeight + graphGap;
  const frameHeight = graphTop + height + padding;

  function element(tag, attributes) {
    const node = document.createElementNS(svg.namespaceURI, tag);
    for (const [key, value] of Object.entries(attributes)) {
      node.setAttribute(key, value);
    }
    return node;
  }

  const contents = element("g", {
    transform: `translate(${(frameWidth - width) / 2 - x}, ${graphTop - y})`,
  });
  for (const child of [...svg.children]) {
    if (!["title", "desc", "style", "defs"].includes(child.localName)) {
      contents.append(child);
    }
  }

  const brand = new DOMParser().parseFromString(logo, "image/svg+xml").documentElement;
  const [, , brandWidth, brandHeight] = brand.getAttribute("viewBox").split(/\s+/).map(Number);
  brand.setAttribute("x", padding);
  brand.setAttribute("y", logoTop);
  brand.setAttribute("width", logoWidth);
  brand.setAttribute("height", logoWidth * brandHeight / brandWidth);
  brand.setAttribute("aria-hidden", "true");
  svg.append(
    element("rect", {
      x: 0.5, y: 0.5, width: frameWidth - 1, height: frameHeight - 1, rx: 10,
      fill: background, stroke: border, "aria-hidden": "true",
    }),
    document.importNode(brand, true),
    element("line", {
      x1: padding, x2: frameWidth - padding, y1: headerHeight, y2: headerHeight,
      stroke: border, "aria-hidden": "true",
    }),
    contents,
  );
  svg.removeAttribute("style");
  svg.setAttribute("viewBox", `0 0 ${frameWidth} ${frameHeight}`);
  svg.setAttribute("width", frameWidth);
  svg.setAttribute("height", frameHeight);
  return new XMLSerializer().serializeToString(svg);
}
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mermaid-js", type=Path, required=True)
    parser.add_argument("--chromium", default="/usr/bin/chromium")
    args = parser.parse_args()
    theme = json.loads((DIAGRAMS / "theme.json").read_text(encoding="utf-8"))
    logo = (DIAGRAMS / "misp-logo.svg").read_text(encoding="utf-8")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=args.chromium)
        page = browser.new_page()
        page.add_script_tag(path=str(args.mermaid_js))
        for source in sorted(DIAGRAMS.glob("*.mmd")):
            svg = page.evaluate(
                RENDER,
                {
                    "id": source.stem,
                    "source": source.read_text(encoding="utf-8"),
                    "theme": theme,
                    "logo": logo,
                },
            )
            root = ElementTree.fromstring(svg)
            if (
                root.find(f"{SVG_NS}title") is None
                or root.find(f"{SVG_NS}desc") is None
                or root.find(f".//{SVG_NS}foreignObject") is not None
            ):
                raise ValueError(
                    f"{source.name} requires a title, description and native SVG text"
                )
            target = source.with_suffix(".svg")
            target.write_text(svg + "\n", encoding="utf-8")
            print(target.name)
        browser.close()


if __name__ == "__main__":
    main()
