# Source attribution

**Native work: 0.2.0-dev1 | CFG: 0.1.1 | Updated: 2026-10-18**

The 2026-10-18 macro revision starts secondary-tool calibration directly by default. Backup acknowledgement is optional; native source changes are unchanged.

This usermod is distributed under GPL-3.0. The complete license is available in
the [standalone project](https://github.com/cheekyb52/Snapmaker-U1-Single-Tool-Calibration/blob/main/LICENSE).
Original copyright, license and warranty notices in upstream sources are retained.

The calibration project modifies `klippy/kinematics/extruder.py` for opt-in
independent saving, shared-reference centering and active-tool origin refresh;
`klippy/extras/extruder_config_bak.py` for validated reference metadata and atomic
selected/batched saves; and `klippy/extras/probe_inductance_coil.py` for compatible
stock batch saving and reference retirement. It adds the macro CFG and build guards.
Original and modified source fixtures, manifests and regression tests accompany
the standalone project. The patch is matched to the reviewed source hashes.

Upstream source projects:

- [Snapmaker U1 Klipper](https://github.com/Snapmaker/U1-klipper)
- [Klipper](https://github.com/Klipper3d/klipper)
- [Paxx Snapmaker U1 Extended Firmware](https://github.com/paxx12-snapmaker-u1/SnapmakerU1-Extended-Firmware)

Thanks to Paxx and contributors for the firmware builder, numbered overlays and
documentation conventions. This optional mod is independently maintained;
affiliation with or endorsement by the upstream projects is not implied.
