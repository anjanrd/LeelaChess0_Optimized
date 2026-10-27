#!/usr/bin/env bash
# Development dependencies/builds live on WSL's Linux filesystem.
set -euo pipefail
PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_ROOT="${XDG_DATA_HOME:-$HOME/.local/share}/lc0-int8"
VENV="$RUNTIME_ROOT/venv"
LC0_SOURCE="$RUNTIME_ROOT/source/lc0"
LC0_BUILD="$RUNTIME_ROOT/build/lc0-tools"
LC0_COMMIT=9f45ea446baf9ce55e299250cde3053b7e93a035

case "${1:-}" in
  bootstrap)
    mkdir -p "$RUNTIME_ROOT/source" "$RUNTIME_ROOT/build"
    if [[ ! -x "$VENV/bin/python" ]]; then
      python3 -m venv "$VENV"
    fi
    "$VENV/bin/python" -m pip install --disable-pip-version-check 'pip==25.3' 'meson==1.9.1'
    if [[ ! -e "$LC0_SOURCE" ]]; then
      git clone --depth 1 --branch v0.33.0-rc0 https://github.com/LeelaChessZero/lc0.git "$LC0_SOURCE"
    fi
    test "$(git -C "$LC0_SOURCE" rev-parse HEAD)" = "$LC0_COMMIT"
    test -z "$(git -C "$LC0_SOURCE" status --porcelain)"
    printf 'Runtime: %s\nSource commit: %s\n' "$RUNTIME_ROOT" "$LC0_COMMIT"
    ;;
  install)
    LOG_DIRECTORY="$(mktemp -d /tmp/lc0-step3-install.XXXXXX)"
    printf 'Installation log: %s/pip.log\n' "$LOG_DIRECTORY"
    if ! "$VENV/bin/python" -m pip install --disable-pip-version-check --progress-bar off -r "$PROJECT_ROOT/requirements/step3.in" >"$LOG_DIRECTORY/pip.log" 2>&1; then
      tail -n 80 "$LOG_DIRECTORY/pip.log"
      exit 1
    fi
    tail -n 4 "$LOG_DIRECTORY/pip.log"
    "$VENV/bin/python" -m pip check
    ;;
  build)
    export PATH="$VENV/bin:$PATH"
    test "$(git -C "$LC0_SOURCE" rev-parse HEAD)" = "$LC0_COMMIT"
    # Eigen provides an independent native CPU evaluator for later parity work.
    # This is an exporter/reference build, not the final GPU benchmark binary.
    if [[ ! -f "$LC0_BUILD/build.ninja" ]]; then
      meson setup "$LC0_BUILD" "$LC0_SOURCE" --buildtype=release \
        -Dgtest=false -Dpython_bindings=true -Dblas=true -Dopenblas=false \
        -Dplain_cuda=false -Dcudnn=false -Dcutlass=false -Donnx=false \
        -Dnvcc=false -Dispc=false -Dmetal=disabled -Db_lto=false
    fi
    meson compile -C "$LC0_BUILD" -j 4
    "$LC0_BUILD/lc0" describenet --help
    "$LC0_BUILD/lc0" describenet --weights="$PROJECT_ROOT/models/source/BT3-768x15x24h-swa-2790000.pb.gz"
    ;;
  verify)
    export OMP_NUM_THREADS=2
    export OPENBLAS_NUM_THREADS=2
    "$VENV/bin/python" "$PROJECT_ROOT/scripts/verify_step3.py"
    ;;
  *)
    printf 'Usage: bash scripts/setup_step3.sh {bootstrap|install|build|verify}\n' >&2
    exit 2
    ;;
esac
