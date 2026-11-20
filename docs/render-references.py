"""Prepare the generated Python reference and release notes for Quarto."""

import re
import subprocess
import sys
from pathlib import Path

docs = Path(__file__).resolve().parent
output = docs / "_generated"
output.mkdir(exist_ok=True)

subprocess.run([sys.executable, "-m", "quartodoc", "build"], cwd=docs, check=True)

# Quartodoc's single-page builder appends .qmd to its default index name.
raw_reference = output / "index.qmd.qmd"
reference = raw_reference.read_text(encoding="utf-8")

# Quartodoc lists attributes in summary tables without creating sections for them.
anchors = set(re.findall(r"^#+ .*\{\s*#(opentaxii\.[\w.]+)", reference, re.M))
reference = re.sub(
    r"\[(\w+)\]\(#(opentaxii\.[\w.]+)\)",
    lambda match: match[0] if match[2] in anchors else f"`{match[1]}`",
    reference,
)
subprocess.run(
    [
        "quarto",
        "pandoc",
        "--from=markdown",
        "--to=markdown",
        "--shift-heading-level-by=1",
        "--wrap=none",
        "--output",
        output / "python-api.qmd",
    ],
    input=reference,
    text=True,
    check=True,
)
raw_reference.unlink()

changelog = (docs.parent / "CHANGES.md").read_text(encoding="utf-8")
(output / "changes.md").write_text(
    changelog.partition("\n")[2].lstrip(), encoding="utf-8"
)
