"""Run unchanged ladder hw, enforcing AGENTS stop-on-first-failure."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ladder

original_run = ladder.run
def strict_run(cmd, log=None, check=True):
    # ladder hw normally passes check=False for TRT/roofline children.
    return original_run(cmd, log=log, check=True)
ladder.run = strict_run
sys.argv = ['ladder.py', 'hw', *sys.argv[1:]]
ladder.main()
