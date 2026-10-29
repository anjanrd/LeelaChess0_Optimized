"""Inventory/share large research artifacts without committing binaries to Git.

    python -B maintenance/artifacts.py inventory
    python -B maintenance/artifacts.py verify
    python -B maintenance/artifacts.py pack D:/handoff/lc0-artifacts.zip
    python -B maintenance/artifacts.py restore D:/handoff/lc0-artifacts.zip

Runtime installations, virtual environments and external WSL files are excluded.
Restore verifies hashes and refuses to replace different existing files.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ROOTS = ("models", "nets", "data", "results", "reports",
         "archive/person-a-week1/models")
MANIFEST = Path("artifacts/manifest.json")


def digest(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def target(root, relative):
    rel = PurePosixPath(relative)
    if rel.is_absolute() or ".." in rel.parts or ":" in relative or "\\" in relative:
        raise ValueError(f"unsafe artifact path: {relative}")
    if not any(relative.startswith(prefix + "/") for prefix in ROOTS):
        raise ValueError(f"outside artifact roots: {relative}")
    resolved = (root / rel).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError(f"artifact escapes checkout: {relative}")
    return resolved


def inventory(root=ROOT):
    entries = []
    for prefix in ROOTS:
        for f in sorted((root / prefix).rglob("*")):
            if f.is_file() and "__pycache__" not in f.parts:
                entries.append({"path": f.relative_to(root).as_posix(),
                                "bytes": f.stat().st_size, "sha256": digest(f)})
    return {"schema_version": 1, "roots": list(ROOTS), "files": entries}


def verify(manifest, root=ROOT):
    failures = []
    seen = set()
    for e in manifest["files"]:
        p = target(root, e["path"])
        if e["path"] in seen:
            raise ValueError(f"duplicate artifact: {e['path']}")
        seen.add(e["path"])
        if not p.is_file():
            failures.append(f"missing: {e['path']}")
        elif p.stat().st_size != e["bytes"] or digest(p) != e["sha256"]:
            failures.append(f"changed: {e['path']}")
    return failures


def pack(destination, manifest, root=ROOT):
    destination = Path(destination).expanduser().resolve()
    if destination.is_relative_to(root.resolve()):
        raise ValueError("write the artifact bundle outside the checkout")
    failures = verify(manifest, root)
    if failures:
        raise ValueError("artifact verification failed: " + "; ".join(failures[:5]))
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation prevents accidental replacement of a previous bundle.
    with zipfile.ZipFile(destination, "x", compression=zipfile.ZIP_STORED,
                         allowZip64=True) as z:
        z.writestr("artifact-manifest.json", json.dumps(manifest, indent=2))
        for e in manifest["files"]:
            z.write(target(root, e["path"]), e["path"])


def restore(bundle, root=ROOT):
    restored = skipped = 0
    with zipfile.ZipFile(bundle) as z:
        manifest = json.loads(z.read("artifact-manifest.json"))
        names = [e["path"] for e in manifest["files"]]
        if len(names) != len(set(names)):
            raise ValueError("duplicate manifest members")
        if sorted(z.namelist()) != sorted(names + ["artifact-manifest.json"]):
            raise ValueError("bundle members differ from the manifest")
        # Preflight every path/conflict before writing any restored file.
        for e in manifest["files"]:
            p = target(root, e["path"])
            if p.exists() and (not p.is_file() or p.stat().st_size != e["bytes"]
                               or digest(p) != e["sha256"]):
                raise ValueError(f"refusing to overwrite different file: {e['path']}")
        with tempfile.TemporaryDirectory(prefix="lc0-artifact-restore-") as scratch:
            for e in manifest["files"]:
                p = target(root, e["path"])
                if p.exists():
                    skipped += 1
                    continue
                staged = Path(scratch) / "member"
                with z.open(e["path"]) as source, staged.open("wb") as output:
                    shutil.copyfileobj(source, output)
                if staged.stat().st_size != e["bytes"] or digest(staged) != e["sha256"]:
                    raise ValueError(f"corrupt bundle member: {e['path']}")
                p.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(staged), p)
                restored += 1
    return restored, skipped


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("action", choices=["inventory", "verify", "pack", "restore"])
    ap.add_argument("bundle", nargs="?")
    a = ap.parse_args()
    if a.action == "inventory":
        m = inventory()
        (ROOT / MANIFEST).parent.mkdir(parents=True, exist_ok=True)
        (ROOT / MANIFEST).write_text(json.dumps(m, indent=2) + "\n", encoding="utf-8")
        print(f"Inventoried {len(m['files'])} files, {sum(e['bytes'] for e in m['files'])} bytes")
    elif a.action == "restore":
        if not a.bundle:
            ap.error("restore requires a bundle path")
        restored, skipped = restore(a.bundle)
        print(f"Restored {restored} files; {skipped} identical files retained")
    else:
        m = json.loads((ROOT / MANIFEST).read_text(encoding="utf-8"))
        if a.action == "verify":
            failures = verify(m)
            print(f"Checked {len(m['files'])} files; {len(failures)} failures")
            if failures:
                raise SystemExit("\n".join(failures[:20]))
        else:
            if not a.bundle:
                ap.error("pack requires a bundle path")
            pack(a.bundle, m)
            print(f"Wrote {a.bundle}")


if __name__ == "__main__":
    main()
