#!/usr/bin/env bash
# Test whether the test files produce the expected return code for each utility
# These are the most basic versions of commands that should return 0/1 correctly
# If this script returns 0, all tests passed

#### FUNCTIONS ####
function testfn {
  for f in $2
    do retcode=0
    $1 "$f" >/dev/null 2>&1 || retcode=1
    assert_eq "$3" "$retcode" "$f" "${1: 4}"
    echo "[PASSED] ${1: 4} on $f: exit code $3 (expected)"
  done
}

function run_clang_format {
  diff <(clang-format "$1") "$1"
}

function run_clang_tidy {
  clang-tidy "$1" -checks=* -warnings-as-errors=* -- -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
}

function run_oclint {
  if [[ "$(oclint "$1" 2>&1)" != *'Violations=0'* ]]
    then return 1
  fi
}

function run_uncrustify {
  uncrustify -f "$1" -c defaults.cfg --check --set indent_columns=2
}

function run_cppcheck {
  cppcheck "$1" -q --error-exitcode=1 --suppress=missingIncludeSystem --enable=all
}

function assert_eq {
  if [[ "$1" != "$2" ]]
    then echo "[FAILED] $4: Expected error code $1 but got $2 for file $3"
    exit 1
  fi
}

function cleanup {
  rm defaults.cfg
}
####################

ok_files="$(find tests/files/ok*)"
err_files="$(find tests/files/err*)"

### clang-format ###
testfn run_clang_format "$ok_files" 0
testfn run_clang_format "$err_files" 1
### clang-tidy ###
testfn run_clang_tidy "$ok_files" 0
testfn run_clang_tidy "$err_files" 1
### oclint ###
testfn run_oclint "$ok_files" 0
testfn run_oclint "$err_files" 1
### uncrustify ###
# generate a config file to be used by uncrustify
uncrustify --show-config > defaults.cfg
trap cleanup EXIT
testfn run_uncrustify "$ok_files" 0
testfn run_uncrustify "$err_files" 1
### cppcheck ###
testfn run_cppcheck "$ok_files" 0
testfn run_cppcheck "$err_files" 1
