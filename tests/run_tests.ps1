# Powershell module to run pytest

function install_windows_cmds {
  # Windows powershell
  choco install python --version 3.7.5 -y
  # llvm is already installed
  choco install llvm uncrustify cppcheck -y
  # Check installations
  where python clang-format clang-tidy uncrustify cppcheck
}

function pip_install {
  python -c "import sys; print('PYTHON PATH:' + '\n'.join(sys.path))"
  pip install . -r requirements.txt
}

function run {
  install_windows_cmds
  pip_install
  pytest -vvv -x --internal -n 32
}

run
