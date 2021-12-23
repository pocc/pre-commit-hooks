#!/usr/bin/env python3
"""Adapted for from LLVM's clang-format-diff.py found here:

https://github.com/llvm/llvm-project/blob/main/clang/tools/clang-format/clang-format-diff.py

Logic behind `--line-diff` flag: Gets git diff of most recent commit to get the
lines that have changed and the files they were changed in.
"""

import re
import subprocess as sp
from typing import Any, Dict, List

TypeLineNumsToChange = List[List[int]]
TypeFilesToChange = Dict[str, TypeLineNumsToChange]


def get_changed_lines():
    """Extract changed lines for each file."""
    diff_lines_str = get_added_diff_text()
    diff_lines_json = parse_diff_lines(diff_lines_str)
    return diff_lines_json

def check_errors(program: List[str], child: Any):
    if child.stderr or child.returncode != 0:
        raise RuntimeError(f"""{program} failed due to a nonzero return code or stderr.
returncode: {child.returncode}\nstdout: `{child.stdout}`\nstderr: `{child.stderr}`""")

def get_added_diff_text() -> str:
    """Return a git diff as a list of lines altered since last commit.
    Compare to clang-format-diff, which does a post-commit comparison"""
    command = ["git", "diff", "HEAD"]
    child = sp.run(command, stdout=sp.PIPE, stderr=sp.PIPE)
    check_errors(command, child)
    return child.stdout.decode()

def parse_diff_lines(diff_lines_str: str) -> TypeFilesToChange:
    changed_lines: TypeFilesToChange = {}  # {filename: [[start_line, end_line], ...], ...}
    filename = ''
    diff_lines = [line + '\n' for line in diff_lines_str.split('\n')[:-1]]

    # Keeping regex logic intact as the LLVM has already done testing with it
    for line in diff_lines:
        match = re.search(r'^\+\+\+\ b/(.+)', line)
        if match:
            filename = match.group(1)
        match = re.search(r'^@@.*\+(\d+)(,(\d+))?', line)
        if match:
            start_line = int(match.group(1))
            line_count = 1
            if match.group(3):
                line_count = int(match.group(3))
            # Also format lines range if line_count is 0 in case of deleting
            # surrounding statements.
            end_line = start_line
            if line_count != 0:
                end_line += line_count - 1
            if filename not in changed_lines:
                changed_lines[filename] = []
            changed_lines[filename].append([start_line, end_line])

    return changed_lines
