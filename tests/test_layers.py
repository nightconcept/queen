"""Game rules never import pyxel (GDD 16.2). Only render/, app.py, audio.py and frames.py may."""

import ast
import unittest
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent.parent / "queen"
ALLOWED = ("render/", "app.py", "audio.py", "frames.py")


def imports(path: Path) -> set[str]:
    out = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            out |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            out.add(node.module.split(".")[0])
            if node.module.startswith("nightengine.host"):
                out.add("nightengine.host")
    return out


class Layers(unittest.TestCase):
    def test_rules_never_import_pyxel(self):
        bad = []
        for path in PACKAGE.rglob("*.py"):
            rel = path.relative_to(PACKAGE).as_posix()
            if rel.startswith(ALLOWED):
                continue
            found = imports(path) & {"pyxel", "js", "nightengine.host"}
            if found:
                bad.append(f"{rel} imports {sorted(found)}")
        self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()
