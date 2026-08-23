#!/usr/bin/env python3
"""Unit tests for OCLintCmd.has_findings (regression for #45).

Uses captured OCLint report text so the check is exercised without OCLint
installed and independently of its version.
"""
from hooks.oclint import OCLintCmd

# Rule violations, no compiler error. This is the case the old `b"Errors" in
# stdout` check missed: the report contains no "Errors" substring at all.
VIOLATIONS = b"""
OCLint Report

Summary: TotalFiles=1 FilesWithViolations=1 P1=0 P2=0 P3=2

x.c:1:7: short variable name [naming|P3] Length of variable name `aa` is 2
x.c:1:15: unused local variable [unused|P3] The local variable 'unusedvar' is unused.

[OCLint (https://oclint.org) v24.11]
"""

# File that fails to compile: OCLint reports FilesWithViolations=0 but a
# "Compiler Errors" section, so the count alone is not enough.
COMPILER_ERROR = b"""
Compiler Errors:
(please be aware that these errors will prevent OCLint from analyzing this source code)

err.c:2:18: non-void function 'main' should return a value

OCLint Report

Summary: TotalFiles=0 FilesWithViolations=0 P1=0 P2=0 P3=0
"""

CLEAN = b"""
OCLint Report

Summary: TotalFiles=1 FilesWithViolations=0 P1=0 P2=0 P3=0

[OCLint (https://oclint.org) v24.11]
"""


def test_detects_rule_violations():
    assert OCLintCmd.has_findings(VIOLATIONS) is True


def test_detects_compiler_errors():
    assert OCLintCmd.has_findings(COMPILER_ERROR) is True


def test_passes_clean_output():
    assert OCLintCmd.has_findings(CLEAN) is False
