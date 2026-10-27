"""Acquire the fixed source checkpoint; keep partial downloads in system temp."""

import gzip
import hashlib
import json
import shutil
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NAME = "BT3-768x15x24h-swa-2790000"
URL = f"https://storage.lczero.org/files/networks-contrib/{NAME}.pb.gz"
EXPECTED_BYTES = 190_937_780


def fingerprint(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    destination = ROOT / "models" / "source" / f"{NAME}.pb.gz"
    record_path = destination.parent / "checkpoint.json"
    previous = json.loads(record_path.read_text()) if record_path.exists() else None
    if not destination.exists():
        with tempfile.TemporaryDirectory(prefix="lc0-checkpoint-") as scratch:
            partial = Path(scratch) / "checkpoint.pb.gz"
            request = urllib.request.Request(
                URL, headers={"Range": "bytes=0-", "User-Agent": "LC0-project-acquisition"}
            )
            with urllib.request.urlopen(request, timeout=120) as response:
                if response.status not in (200, 206):
                    raise RuntimeError(f"Unexpected HTTP status: {response.status}")
                if response.status == 206:
                    content_range = response.headers.get("Content-Range", "")
                    expected_range = f"bytes 0-{EXPECTED_BYTES - 1}/{EXPECTED_BYTES}"
                    if content_range != expected_range:
                        raise RuntimeError(f"Unexpected Content-Range: {content_range}")
                received = 0
                milestone = 32 * 1024 * 1024
                with partial.open("wb") as output:
                    while chunk := response.read(4 * 1024 * 1024):
                        output.write(chunk)
                        received += len(chunk)
                        if received >= milestone:
                            print(f"Downloaded {received / 1024**2:.0f} MiB", flush=True)
                            milestone += 32 * 1024 * 1024
            if partial.stat().st_size != EXPECTED_BYTES:
                raise RuntimeError(f"Size mismatch: {partial.stat().st_size}")
            # Read to EOF to verify gzip trailer/CRC before publishing the artifact.
            with gzip.open(partial, "rb") as uncompressed:
                while uncompressed.read(4 * 1024 * 1024):
                    pass
            digest = fingerprint(partial)
            if previous and previous["sha256_compressed"] != digest:
                raise RuntimeError("Downloaded bytes differ from the recorded checkpoint")
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(partial, destination)
    if destination.stat().st_size != EXPECTED_BYTES:
        raise RuntimeError("Existing checkpoint has an unexpected size")
    digest = fingerprint(destination)
    if previous and previous["sha256_compressed"] != digest:
        raise RuntimeError("Existing checkpoint differs from its recorded SHA-256")
    with gzip.open(destination, "rb") as stream:
        uncompressed_bytes = sum(len(chunk) for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""))
    record = {
        "checkpoint": NAME,
        "url": URL,
        "relative_path": destination.relative_to(ROOT).as_posix(),
        "compressed_bytes": destination.stat().st_size,
        "uncompressed_bytes": uncompressed_bytes,
        "sha256_compressed": digest,
        "acquired_at_utc": previous["acquired_at_utc"] if previous else datetime.now(timezone.utc).isoformat(),
        "checksum_provenance": "Computed locally; not a publisher-authenticated digest",
        "gzip_integrity": "passed",
    }
    record_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
