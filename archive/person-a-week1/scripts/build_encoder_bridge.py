"""Link an explicit-history encoder adapter against the pinned lc0 objects."""

import hashlib
import json
import os
import shlex
import subprocess
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
RUNTIME = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share"))) / "lc0-int8"
SOURCE = RUNTIME / "source/lc0"
BUILD = RUNTIME / "build/lc0-tools"
COMMIT = "9f45ea446baf9ce55e299250cde3053b7e93a035"


def main():
    commit = subprocess.check_output(["git", "-C", str(SOURCE), "rev-parse", "HEAD"], text=True).strip()
    assert commit == COMMIT
    assert not subprocess.check_output(["git", "-C", str(SOURCE), "status", "--porcelain"], text=True).strip()
    destination = RUNTIME / "build/encoder-bridge"
    destination.mkdir(parents=True, exist_ok=True)
    adapter = PROJECT / "src/native/encoder_bridge.cc"
    obj = destination / "encoder_bridge.o"
    binary = destination / "encoder_bridge"
    compile_command = ["c++", "-std=c++20", "-O2", "-march=native", "-pthread", "-DNO_PEXT", "-DNOMINMAX",
                       "-I" + str(BUILD / "lc0.p"), "-I" + str(BUILD), "-I" + str(SOURCE / "src"),
                       "-I" + str(SOURCE / "third_party"), "-c", str(adapter), "-o", str(obj)]
    subprocess.run(compile_command, check=True)
    commands = subprocess.check_output(["ninja", "-C", str(BUILD), "-t", "commands", "lc0"], text=True)
    link_command = shlex.split(commands.splitlines()[-1])
    assert link_command[1:3] == ["-o", "lc0"]
    assert "lc0.p/src_main.cc.o" in link_command
    link_command[2] = str(binary)
    link_command[link_command.index("lc0.p/src_main.cc.o")] = str(obj)
    subprocess.run(link_command, cwd=BUILD, check=True)
    record = {"lc0_commit": commit, "upstream_worktree": "clean", "history_fill": "explicit no or fen_only",
              "adapter_source_sha256": hashlib.sha256(adapter.read_bytes()).hexdigest(),
              "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
              "binary": str(binary), "compile_command": compile_command,
              "link_recipe": "Reuse lc0's link command, replacing only the main object and output path"}
    (PROJECT / "environment/step4-bridge.json").write_text(json.dumps(record, indent=2) + "\n")
    print("Built explicit-history native encoder bridge:", binary)


if __name__ == "__main__":
    main()
