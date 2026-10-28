#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright (c) 2026 cheekyb52
set -euo pipefail
[[ "${CREATE_FIRMWARE:-}" == 1 && $# == 1 ]] || { echo "Run through the firmware builder" >&2; exit 1; }
rootfs=$(realpath -- "$1")
[[ -d "$rootfs/home/lava/klipper/klippy" ]] || { echo "Missing Klipper tree" >&2; exit 1; }
stage_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
(cd -- "$rootfs" && sha256sum --check --strict <<'MIXED_NOZZLE_MODIFIED'
1ef6e8ade716fab99715e00e58502016197f43d3147620018a34c681e9d312eb  home/lava/klipper/klippy/extras/print_task_config.py
MIXED_NOZZLE_MODIFIED
)
python3 -B "$stage_dir/tests/check_nozzle_validation.py" \
  --source "$rootfs/home/lava/klipper/klippy/extras/print_task_config.py" \
  --patch "$stage_dir/patches/home/lava/klipper/01_disable_nozzle_diameter_check.patch"
