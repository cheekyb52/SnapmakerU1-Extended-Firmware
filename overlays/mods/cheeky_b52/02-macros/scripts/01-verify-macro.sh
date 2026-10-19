#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright (c) 2026 cheekyb52
set -euo pipefail
[[ "${CREATE_FIRMWARE:-}" == 1 && $# == 1 ]] || { echo "Run through the firmware builder" >&2; exit 1; }
rootfs=$(realpath -- "$1")
[[ -d "$rootfs/home/lava/klipper/klippy" ]] || { echo "Missing Klipper tree" >&2; exit 1; }
cd -- "$rootfs"
printf '%s  %s\n' 'ea4733329ae5575a5b42d26284f8d79178f5153bdb2cbe832907df749625cde0' 'usr/local/share/firmware-config/extended/klipper/70_tool_offsets.cfg' | sha256sum --check --strict

# Let the stock checksum-based cleanup replace only the unmodified CFG 0.1.0.
cleanup=usr/local/share/firmware-config/force-cleanup.sha256
[[ -f "$cleanup" ]] || { echo "Missing stock config migration list" >&2; exit 1; }
old_cfg='5d73c5f489bccd124a6343f8b32968d52f29f8ab353cc45607f0ba556ac42ccd  klipper/70_tool_offsets.cfg'
grep -Fxq -- "$old_cfg" "$cleanup" || printf '\n%s\n' "$old_cfg" >> "$cleanup"
