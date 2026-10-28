#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright (c) 2026 cheekyb52
set -euo pipefail
[[ "${CREATE_FIRMWARE:-}" == 1 && $# == 1 ]] || { echo "Run through the firmware builder" >&2; exit 1; }
rootfs=$(realpath -- "$1")
[[ -d "$rootfs/home/lava/klipper/klippy" ]] || { echo "Missing Klipper tree" >&2; exit 1; }
cd -- "$rootfs"
sha256sum --check --strict <<'MIXED_NOZZLE_BASELINE'
8298babc42526ef4a4026207927e91c52fd1ca5f1e1afe6b1f08b0dbdced82c0  home/lava/klipper/klippy/extras/print_task_config.py
MIXED_NOZZLE_BASELINE
