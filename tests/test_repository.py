"""Portability and artifact-sharing regression tests; no model/GPU execution."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

import ladder

SPEC = importlib.util.spec_from_file_location(
    "artifact_tools", Path(__file__).resolve().parents[1] / "maintenance/artifacts.py")
ART = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ART)


class ConfigTests(unittest.TestCase):
    def test_config_paths_do_not_depend_on_caller_directory(self):
        with tempfile.TemporaryDirectory(prefix="lc0-config-test-") as temp:
            base = Path(temp)
            config = base / "config.json"
            config.write_text(json.dumps({"work": "run", "bt3": "nets/BT3.pb.gz",
                                          "lc0": "tools/lc0.exe", "nsys": "nsys",
                                          "syzygy": "tables"}), encoding="utf-8-sig")
            before = Path.cwd()
            try:
                os.chdir(base.parent)
                cfg = ladder.load_config(config)
            finally:
                os.chdir(before)
            self.assertEqual(cfg["_w"], (base / "run").resolve())
            self.assertEqual(Path(cfg["lc0"]), (base / "tools/lc0.exe").resolve())
            self.assertEqual(Path(cfg["bt3"]), (base / "run/nets/BT3.pb.gz").resolve())
            self.assertEqual(Path(cfg["syzygy"]), (base / "tables").resolve())
            self.assertEqual(cfg["nsys"], "nsys")

    def test_shared_recipe_matches_frozen_run(self):
        root = Path(ladder.__file__).resolve().parent
        cfg = json.loads((root / "config.example.json").read_text())
        old = json.loads((root / "archive/person-b-import/config.json").read_text())
        for key in ("backend", "fp16_opts", "int8_opts", "native_backend", "native_opts",
                    "recipe", "best", "tbset", "calib", "study", "extras", "match", "hw"):
            self.assertEqual(cfg[key], old[key], key)
        # The shared limit follows the actually completed resized Study C run.
        self.assertEqual(cfg["studyc"], {"movetimes": "200,800", "models": "fp16,BEST", "limit": 2437})


class ArtifactTests(unittest.TestCase):
    def make_fixture(self, root):
        (root / "models").mkdir()
        (root / "models/toy.onnx").write_bytes(b"artifact-example\x00\xff")
        return ART.inventory(root)

    def test_bundle_round_trip_and_idempotent_restore(self):
        with tempfile.TemporaryDirectory(prefix="lc0-bundle-test-") as temp:
            base = Path(temp)
            source, dest = base / "source", base / "destination"
            source.mkdir(); dest.mkdir()
            manifest = self.make_fixture(source)
            bundle = base / "handoff.zip"
            ART.pack(bundle, manifest, source)
            self.assertEqual(ART.restore(bundle, dest), (1, 0))
            self.assertEqual(ART.verify(manifest, dest), [])
            self.assertEqual(ART.restore(bundle, dest), (0, 1))

    def test_different_file_is_not_overwritten(self):
        with tempfile.TemporaryDirectory(prefix="lc0-conflict-test-") as temp:
            base = Path(temp)
            source, dest = base / "source", base / "destination"
            source.mkdir(); dest.mkdir()
            manifest = self.make_fixture(source)
            self.make_fixture(dest)
            (dest / "models/toy.onnx").write_bytes(b"teammate-change")
            ART.pack(base / "handoff.zip", manifest, source)
            with self.assertRaisesRegex(ValueError, "overwrite"):
                ART.restore(base / "handoff.zip", dest)
            self.assertEqual((dest / "models/toy.onnx").read_bytes(), b"teammate-change")

    def test_paths_cannot_escape_or_target_code(self):
        with tempfile.TemporaryDirectory(prefix="lc0-path-test-") as temp:
            for path in ("../outside", "models/../../outside", "C:/outside", "ladder.py", "models\\bad"):
                with self.subTest(path=path), self.assertRaises(ValueError):
                    ART.target(Path(temp), path)

    def test_tampering_is_detected(self):
        with tempfile.TemporaryDirectory(prefix="lc0-tamper-test-") as temp:
            root = Path(temp)
            manifest = self.make_fixture(root)
            (root / "models/toy.onnx").write_bytes(b"changed")
            self.assertEqual(len(ART.verify(manifest, root)), 1)


if __name__ == "__main__":
    unittest.main()
