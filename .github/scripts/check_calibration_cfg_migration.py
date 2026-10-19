#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright (c) 2026 cheekyb52
"""Check the real macro guard and stock startup migration using temporary files."""
import os
from pathlib import Path
import subprocess
import tempfile

REPO = Path(__file__).resolve().parents[2]
MOD = REPO / "overlays/mods/cheeky_b52"
RELATIVE = "overlays/mods/cheeky_b52/02-macros/root/usr/local/share/firmware-config/extended/klipper/70_tool_offsets.cfg"
new_cfg = (REPO / RELATIVE).read_bytes()
old_cfg = subprocess.check_output(["git", "show", "518884de146a42d79c230fd561534a4995dd464b:" + RELATIVE], cwd=REPO)
guard = MOD / "02-macros/scripts/01-verify-macro.sh"
stock_init = (REPO / "overlays/firmware-extended/02-firmware-config/root/etc/init.d/S49extended-config").read_text()
checks = []
with tempfile.TemporaryDirectory(prefix="calibration-migration-") as temp:
    root = Path(temp)
    fs = root / "rootfs"
    defaults = fs / "usr/local/share/firmware-config/extended"
    (defaults / "klipper").mkdir(parents=True)
    (fs / "home/lava/klipper/klippy").mkdir(parents=True)
    cfg = defaults / "klipper/70_tool_offsets.cfg"
    cfg.write_bytes(new_cfg)
    cleanup = defaults.parent / "force-cleanup.sha256"
    cleanup.write_text("# preserved original entries\n")
    subprocess.run(["bash", "-n", str(guard)], check=True)
    env = dict(os.environ, CREATE_FIRMWARE="1")
    def run_guard(accepted):
        result = subprocess.run(["bash", str(guard), str(fs)], env=env, capture_output=True, text=True)
        assert (result.returncode == 0) == accepted, result.stderr
    run_guard(True)
    first = cleanup.read_bytes()
    checks.append("valid macro and migration entry")
    run_guard(True)
    assert cleanup.read_bytes() == first and first.startswith(b"# preserved original entries\n")
    checks.append("idempotent guard preserves existing entries")
    cfg.write_bytes(new_cfg + b"\n# changed fixture\n")
    run_guard(False)
    assert cleanup.read_bytes() == first
    checks.append("wrong macro rejected without changing migration list")
    cfg.write_bytes(new_cfg)
    for label, existing in [("packaged-old", old_cfg), ("custom-old", old_cfg + b"\n# local setting\n"), ("current", new_cfg)]:
        dest = root / label / "extended"
        (dest / "klipper").mkdir(parents=True)
        target = dest / "klipper/70_tool_offsets.cfg"
        target.write_bytes(existing)
        other = dest / "klipper/owner.cfg"
        other.write_bytes(b"# owner file\n")
        init = stock_init.replace("/usr/local/share/firmware-config/extended", str(defaults))
        init = init.replace("/home/lava/printer_data/config/extended", str(dest))
        init = init.replace("/usr/local/share/firmware-config/force-cleanup.sha256", str(cleanup))
        init = init.replace("/mnt/udisk", str(root / "absent-usb")).replace("/oem", str(root / "absent-oem"))
        init = init.replace("/sbin/reboot", "false").replace('chown -R lava:lava "$EXTENDED_DIR"', "true")
        startup = root / (label + ".sh")
        startup.write_text(init)
        subprocess.run(["bash", "-n", str(startup)], check=True)
        result = subprocess.run(["bash", str(startup), "start"], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        if label == "packaged-old":
            assert target.read_bytes() == new_cfg
        elif label == "custom-old":
            assert target.read_bytes() == existing
            assert Path(str(target) + ".default").read_bytes() == new_cfg
        else:
            assert target.read_bytes() == existing
        assert other.read_bytes() == b"# owner file\n"
        checks.append(label + " migration preserves unrelated files")
assert len(checks) == 6
for check in checks:
    print("PASS: " + check)
print("All six stock config migration checks passed; no printer access.")
