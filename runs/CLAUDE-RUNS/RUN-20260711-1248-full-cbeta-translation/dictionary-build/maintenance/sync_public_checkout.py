"""Copy the installed dictionary into a Git publish worktree, then audit parity."""

import argparse
import json
import subprocess
from pathlib import Path


PUBLIC = Path("C:/temp/NewTranslationrepos/CbetaZenTranslations").resolve()


def git(checkout: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=checkout)


parser = argparse.ArgumentParser()
parser.add_argument("--checkout", required=True)
args = parser.parse_args()
checkout = Path(args.checkout).resolve(strict=True)
assert checkout != PUBLIC
assert Path(git(checkout, "rev-parse", "--show-toplevel").decode().strip()).resolve() == checkout
assert "Fabulu/CbetaZenTranslations" in git(checkout, "remote", "get-url", "origin").decode()

for name in ("termbase.json", "termbase.v2.json"):
    data = (PUBLIC / name).read_bytes().replace(b"\r\n", b"\n")
    (checkout / name).write_bytes(data.replace(b"\n", b"\r\n"))
(checkout / "termbase.index.json").write_bytes(
    (PUBLIC / "termbase.index.json").read_bytes()
)

source_shards = {path.name: path for path in (PUBLIC / "termbase").glob("*.json")}
checkout_shards = {path.name: path for path in (checkout / "termbase").glob("*.json")}
stale = sorted(checkout_shards.keys() - source_shards.keys())
if stale:
    raise RuntimeError(f"Checkout contains stale shards requiring explicit retirement: {stale}")
for name, source in source_shards.items():
    (checkout / "termbase" / name).write_bytes(source.read_bytes())

subprocess.run(
    ["python", "scripts/audit-dictionary-integrity.py"],
    cwd=checkout, check=True,
)
before = json.loads(git(checkout, "show", "HEAD:termbase.v2.json"))["Entries"]
after = json.loads((checkout / "termbase.v2.json").read_text(encoding="utf-8"))["Entries"]
old = {entry["Id"]: entry for entry in before}
new = {entry["Id"]: entry for entry in after}
print(json.dumps({
    "publicCount": len(after),
    "added": sorted(new.keys() - old.keys()),
    "retired": sorted(old.keys() - new.keys()),
    "changed": sorted(key for key in old.keys() & new.keys() if old[key] != new[key]),
}, ensure_ascii=False))
