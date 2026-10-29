# Independent tool calibration

**Project: 0.2.0-dev3 | CFG: 0.1.1 | Nozzle workaround: 0.1.0 | Updated: 2026-10-29**

Optional usermod maintained by cheekyb52. Compose it with the existing extended
firmware using `PROFILE=extended-cheeky_b52`. This adds no new base firmware profile.

## Features

| Macro | Action |
| --- | --- |
| `CALIBRATE_TOOL_1`, `CALIBRATE_TOOL_2`, `CALIBRATE_TOOL_3` | Clean and measure the reference and selected tool; save only the selected tool, preserving the other three tools and shared reference |
| `CALIBRATE_TOOL_0` | Show a Mainsail/Fluidd warning directing the operator to stock four-tool calibration |
| `CLEAN_AND_VALIDATE_OFFSETS` | Clean all four tools and compare all six pairs against XYZ tolerances without saving |
| `OFFSET_CONTINUE` | Confirm manual cleaning or PEI plate removal |
| `OFFSET_ABORT` | Exit a waiting custom cycle; completed saves remain saved |

**Macro buttons:** These are clickable Klipper macro buttons. In Mainsail, put all
seven buttons in a **Tool Calibration** macro group (Interface Settings → Macros
→ Management: Expert → Add Group) and enable **Standby** visibility.

The native patch adds opt-in `PRESERVE_REFERENCE=1` and atomic pinned-reference
persistence in three Python files. Stock full calibration saves all four results
and retires that reference. Native probing, heating, wiping and docking algorithms
and stock command defaults remain in use.

## Mixed-nozzle print-start workaround

This build also removes the faulty nozzle-diameter comparison in
`klippy/extras/print_task_config.py`, inside `cmd_SET_PRINT_TASK_PARAMETERS`.
Stock code compares every used tool against `nozzle_diameter[0]`; mixed
0.4/0.4/0.8/0.8 mm setups can therefore fail even when their configured sizes agree.

Stage `03-mixed-nozzle` removes only that diameter-validation block. Filament
volume-type and material/nozzle compatibility checks remain active. Keep the real
nozzle sizes correctly configured in both the printer and slicer; this build no
longer enforces that print-start diameter comparison.

The change is baked into the firmware's Python file and survives normal reboots
of this image. Installing only the macro CFG cannot provide it. Flash this full
image after obtaining verified configuration/native backups. Installing another
firmware image may restore its original check.

The stage rejects an unreviewed source hash before patching, checks the modified
hash and Python syntax, and runs eight checks against the actual validation AST.
They reproduce the stock false mismatch, exercise mixed/uniform and unused-tool
cases, preserve the rest of the module, and retain volume/material rejection.
The previous manual workaround has been used on one U1; this integrated image
still needs its own hardware acceptance.

## Build

Place this directory at `overlays/mods/cheeky_b52/` in the Extended Firmware repository.
The live-tested upstream commit is `4bd40f7eb4e396d275c7ede0b7f15d0788588696`.
The current build base is synced to upstream `2c80e3dc495fdf724bc53c5c35c875010ee1668f`
(2026-10-29), the final upstream 2.0 source before the 2.1 transition.
This includes HelixScreen 1.0.7, the v4l2-mpp update, and preservation of the
extra MCU payload and header version when repacking firmware.
The 2.1 port is maintained separately; this build remains based on 2.0.0.205.
The calibration native sources and stock calibration components are unchanged.
Stage `03-mixed-nozzle` separately changes the print-start nozzle check.
All exact source and packed-payload guards remain enabled.
The new full image requires its own hardware acceptance; earlier live results remain
specific to the previously tested builds.
This image uses only `extended-cheeky_b52`; combining source-replacing mods requires
separate review.

```sh
./dev.sh make tools
./dev.sh make firmware
./dev.sh make build PROFILE=extended-cheeky_b52 OUTPUT_FILE=firmware/U1_calibration.bin
```

Source guards require the reviewed three native baselines and unchanged atomic
writer. Post-patch guards verify native hashes/syntax and the macro template.
Adapt and review a changed source set instead of bypassing a guard. Other mods
that edit these files require a reviewed combination.

## Use

Obtain and verify private configuration and native-file backups before installing
or saving calibration. Use normal firmware operation; never enable debug or
factory mode. After installation verify native capability, saved calibration,
the shared reference and all applied offsets. After startup, wait for automatic
tool activation and a matching G-code origin as well as Klipper readiness.

For independent calibration, T0 must remain an unchanged reference. Press the desired
tool button directly; no separate arming command is required by default. Sites may
explicitly enable `variable_require_backup_arm: True` to retain the optional
`OFFSET_ARM_SAVE BACKUP=<verified-backup-timestamp>` acknowledgement. That option
does not create or verify a backup and clears on restart. Then clean each presented nozzle, and press `OFFSET_CONTINUE`. Remove the
PEI plate and clear the ring when prompted, then confirm to begin measurement.
Custom confirmations use the web console; the stock touchscreen controller stays idle.

Cleaning defaults to 200 C; use temperatures appropriate for the loaded material.
Validation defaults to 0.05 mm per axis. For example:

```gcode
CLEAN_AND_VALIDATE_OFFSETS TOL_X=0.05 TOL_Y=0.05 TOL_Z=0.05
```


Firmware upgrades replace an unmodified packaged CFG 0.1.0 through the existing
checksum-based config cleanup. Locally modified CFGs are preserved and receive
a `.default` copy; review those customizations against CFG 0.1.1 before replacing.

## Tested status

Planned testing completed on one U1 and the exact captured PR760 source set:
94 offline checks; independent T1/T2/T3 saves and restart persistence; stock full
calibration and a subsequent independent save; Mainsail/Fluidd T0 warnings;
manual-wait abort; default validation and a deliberately tight-limit warning run.

A complete firmware image built successfully. Five unpacked payload hashes and
17 build-guard fixture checks passed. The operator flashed that image; 20 boot,
16 independent T2 save, nine settled restart and 16 default validation checks
passed. All six final validation pairs were within 0.05 mm, and saved calibration,
all offsets and the reference stayed unchanged. Recovered native parking retries
and an early startup snapshot are documented in the standalone acceptance record.

This establishes behavior on the tested printer/source set. The owner reports
successful-looking prints using the macros; measured alignment-artifact testing
and live interruption during active probing are outside the completed scope.
Speed tuning is deferred: retain ten calibration points, six validation points
and three XY repeats. Those live results used CFG 0.1.0. Current CFG 0.1.1 changes the default button-start policy only; the native payload remains 0.2.0-dev1. The new CFG has offline coverage; live acceptance of that revision is pending.

Full instructions, source hashes, regression sources, results and rollback guidance:
[standalone project](https://github.com/cheekyb52/Snapmaker-U1-Single-Tool-Calibration).

## Attribution

GPL-3.0; see [NOTICE](NOTICE.md). Builds on Snapmaker U1 Klipper and Klipper,
preserving existing source notices. Thanks to Paxx and the Extended Firmware
contributors for the optional-mod infrastructure and documentation conventions.
Independently maintained on a best-effort basis.
