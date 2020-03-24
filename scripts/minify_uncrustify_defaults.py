#!/usr/bin/env python3
"""Generate the uncrustify_defaults.cfg by printing the default config
with `uncrustify --show-config`. This is required because the default
config varies between operating systems. Use this with osx uncrustify v0.68
"""
import re
import subprocess as sp

filename = "tests/uncrustify_defaults.cfg"
defaults = sp.check_output(["uncrustify", "--show-config"]).decode("utf-8")
# Remove all lines that start with # except first. Remove spaces and tabs.
result = re.sub(r"(?:(?<!^)#[^\n\r]*|[ \t])", "", defaults)
# Replace multiple newlines with one
result = re.sub(r"[\r\n]{2,}", "\n", result)
# Replace indent_columns with 2, as that matches LLVM
result = re.sub(r"(indent_columns)=\d", r"\1=2", result)
with open("tests/uncrustify_defaults.cfg", "w") as f:
    f.write(result)
