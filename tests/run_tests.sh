#!/usr/bin/env bash
# Run pytest on various platforms to test pre-commit-hooks

set -e

print_system_info () {
  # Print path and pypthon path as diagnostic information.
  echo "SYSTEM:$OSTYPE"
  echo "PATH:$PATH"
}

pip_install () {
  if [[ "$(python --version 2>&1 | cut -c8-8)" == "2" ]]; then
    python3 -c "import sys; print('PYTHON PATH:' + '\n'.join(sys.path))"
    pip3 install . -r requirements.txt
  else
    python -c "import sys; print('PYTHON PATH:' + '\n'.join(sys.path))"
    pip install . -r requirements.txt
  fi
}

print_command_versions () {
  num_cmds="$(command -v cppcheck clang-format oclint uncrustify cppcheck | wc -l)"
  if [[ ${num_cmds} -eq "5" ]]; then
    clang-format --version
    clang-tidy --version
    oclint --version
    uncrustify --version
    cppcheck --version
  fi
}

install_linux_oclint () {
  wget https://github.com/oclint/oclint/releases/download/v0.13.1/oclint-0.13.1-x86_64-linux-4.4.0-112-generic.tar.gz
  tar -xvzf oclint-0.13.1-x86_64-linux-4.4.0-112-generic.tar.gz
  sudo cp -v oclint-0.13.1/bin/oclint /usr/local/bin/
  sudo cp -vr oclint-0.13.1/lib/* /usr/local/lib/
}

install_linux_cmds () {
  apt -y install clang clang-format clang-tidy uncrustify cppcheck
  install_linux_oclint
}

install_macos_cmds () {
  # If brew is available and the owner of the homebrew is not you
  if [[ $(command -v brew) && "$(whoami)" == "$(stat /usr/local/var/homebrew | awk '{ print $5 }')" ]]; then
    export HOMEBREW_NO_INSTALL_CLEANUP=1
    export HOMEBREW_NO_AUTO_UPDATE=1
    brew install llvm uncrustify cppcheck
    brew cask install oclint
  else
    echo "Brew not available. Tests may fail."
  fi
  # So that system llvm tools like clang-format and clang-tidy are available.
  export PATH="/usr/local/opt/llvm/bin:$PATH"
}

install_windows_cmds () {
  # Windows powershell
  choco install python --version 3.7.5 -y
  # llvm is already installed
  choco install llvm uncrustify cppcheck -y -f
  # Check installations
  command -v python clang-format clang-tidy uncrustify cppcheck
  cd /c/ProgramData/chocolatey/bin/
  /c/tools/miniconda3/python --version
  /c/Program\ Files/LLVM/bin/clang-format --version
  /c/Program\ Files/LLVM/bin/clang-tidy --version
  /c/ProgramData/chocolatey/bin/uncrustify --version
  /c/Program\ Files/Cppcheck/cppcheck.exe --version
  # Manually add programs to path
  export PATH="$PATH:/c/Python37:/c/Program Files/LLVM/bin:/c/Program Files/Cppcheck"
}


run_tests () {
  print_system_info
  COMMAND="pytest -vvv -x --internal"

  if [[ "$OSTYPE" == "linux-gnu" ]]; then
    # travis takes care of installation of other commands
    install_linux_oclint
    COMMAND="$COMMAND --oclint"
  elif [[ "$OSTYPE" == "darwin"* ]]; then
    install_macos_cmds
    COMMAND="$COMMAND --oclint"
  elif [[ "$OSTYPE" == "msys" ]]; then
    # CircleCI "bash"
    install_windows_cmds
  else
    # In windows powershell, this var is not set
    install_windows_cmds
  fi

  print_command_versions
  pip_install
  # Try to parallelize with xdist, but fall back if there's an error.
  ${COMMAND} -n 32 || ${COMMAND}
}

run_tests
