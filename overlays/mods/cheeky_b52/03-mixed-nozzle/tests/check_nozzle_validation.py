#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright (c) 2026 cheekyb52
"""Exercise the actual print-start validation AST with synthetic tool data."""
import argparse
import ast
import copy
import hashlib
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace

BASELINE_SHA256 = '8298babc42526ef4a4026207927e91c52fd1ca5f1e1afe6b1f08b0dbdced82c0'
RELATIVE = Path('klippy/extras/print_task_config.py')


def validation(source):
    tree = ast.parse(source)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'PrintTaskConfig')
    method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'cmd_SET_PRINT_TASK_PARAMETERS')
    body = next(n for n in method.body if isinstance(n, ast.Try)).body
    marker = next(i + 1 for i, line in enumerate(source.splitlines()) if '########## check parameters' in line)
    start = next(i for i, n in enumerate(body) if n.lineno > marker)
    end = next(i for i, n in enumerate(body) if isinstance(n, ast.Assign) and
               any(isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and
                   t.value.id == 'self' and t.attr == 'print_task_config' for t in n.targets))
    return tree, body, body[start:end]


def check_sources(before, after):
    assert hashlib.sha256(before).hexdigest() == BASELINE_SHA256, 'Unreviewed stock source'
    original, body, selected = validation(before.decode())
    patched, _, _ = validation(after.decode())
    candidates = [n for n in selected if isinstance(n, ast.If) and
                  ast.dump(n.test) == ast.dump(ast.parse('nozzle_diameter is not None', mode='eval').body)]
    assert len(candidates) == 1
    assert "['nozzle_diameter'][0]" in ast.unparse(candidates[0])
    body.remove(candidates[0])
    assert ast.dump(original) == ast.dump(patched), 'Changes extend beyond the faulty diameter check'
    compile(before, 'stock_print_task_config.py', 'exec')
    compile(after, 'patched_print_task_config.py', 'exec')


class ValidationError(Exception):
    pass


def run_validation(source, diameters=None, used=(0, 1, 2, 3), volume=False, deny=None, high_flow=False):
    _, _, nodes = validation(source.decode())
    code = compile(ast.fix_missing_locations(ast.Module(body=copy.deepcopy(nodes), type_ignores=[])), '<actual validation>', 'exec')
    sizes = list(diameters or [0.4, 0.4, 0.8, 0.8])
    calls = []
    def compatible(*args):
        index = len(calls)
        calls.append(args)
        return index != deny
    task = {'extruders_used': [False] * 4, 'extruder_map_table': list(range(4)) + [0] * 28,
            'filament_vendor': ['GENERIC'] * 4, 'filament_type': ['PLA'] * 4,
            'filament_sub_type': ['NONE'] * 4}
    data = {'filament_used_g': [1.0 if i in used else 0.0 for i in range(32)],
            'filament_used_mm': [0.0] * 32, 'nozzle_diameter': sizes + [0.0] * 28,
            'filament_volume_type': ['high_flow' if volume else 'standard'] * 4 + [None] * 28}
    scope = dict(PHYSICAL_EXTRUDER_NUM=4, LOGICAL_EXTRUDER_NUM=32,
        nozzle_diameter='provided', filament_volume_type='provided' if volume else None,
        tmp_print_task_config=task, tmp_print_task_config_2=data,
        actual_nozzle_diameter=sizes[:], actual_nozzle_volume_type=['high_flow' if high_flow else 'standard'] * 4,
        self=SimpleNamespace(filament_param_obj=SimpleNamespace(is_allow_to_print=compatible)),
        gcmd=SimpleNamespace(error=lambda message: ValidationError(message)), exception_code=None, exception_index=None)
    before = copy.deepcopy(data)
    error = None
    try:
        exec(code, scope)
    except ValidationError as exc:
        error = str(exc)
    assert data == before, 'Validation unexpectedly changes nozzle or filament settings'
    assert scope['actual_nozzle_diameter'] == sizes
    return scope, calls, error


def exercise(before, after):
    checks = []
    check_sources(before, after)
    checks.append('only the faulty diameter-check AST is removed; full Python syntax valid')
    scope, _, error = run_validation(before)
    assert 'nozzle diameter mismatch:f2_0.4 != e2_0.8' in error and scope['exception_code'] == 14
    checks.append('stock mixed-nozzle false mismatch reproduced')
    scope, calls, error = run_validation(after)
    assert error is None and len(calls) == 4 and [args[-2] for args in calls] == [0.4, 0.4, 0.8, 0.8]
    assert scope['tmp_print_task_config']['extruders_used'] == [True] * 4
    checks.append('patched mixed-nozzle validation passes with actual tool sizes retained')
    for source in (before, after):
        _, calls, error = run_validation(source, diameters=[0.4] * 4)
        assert error is None and len(calls) == 4
    checks.append('uniform-nozzle validation still passes')
    scope, _, error = run_validation(after, volume=True)
    assert 'nozzle volume type mismatch' in error and scope['exception_code'] == 19
    checks.append('filament volume-type mismatch is still rejected')
    scope, calls, error = run_validation(after, deny=2)
    assert 'not allow to print' in error and scope['exception_code'] == 25 and scope['exception_index'] == 2
    assert len(calls) == 3
    checks.append('material/nozzle compatibility rejection is still active')
    _, calls, error = run_validation(after, volume=True, high_flow=True)
    assert error is None and len(calls) == 4
    checks.append('eligible high-flow nozzle combinations retain stock behavior')
    _, calls, error = run_validation(after, used=(0, 1))
    assert error is None and len(calls) == 2
    checks.append('unused tools remain excluded from compatibility checks')
    for message in checks:
        print('PASS: ' + message)
    print('All eight mixed-nozzle validation checks passed; no printer access.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--baseline', type=Path)
    group.add_argument('--patch', type=Path)
    args = parser.parse_args()
    after = args.source.read_bytes()
    if args.baseline:
        exercise(args.baseline.read_bytes(), after)
    else:
        with tempfile.TemporaryDirectory(prefix='mixed-nozzle-check-') as temp:
            root = Path(temp)
            path = root / RELATIVE
            path.parent.mkdir(parents=True)
            path.write_bytes(after)
            subprocess.run(['patch', '-R', '--batch', '--fuzz=0', '-p1', '--input', str(args.patch.resolve())],
                           cwd=root, check=True, capture_output=True)
            exercise(path.read_bytes(), after)


if __name__ == '__main__':
    main()
