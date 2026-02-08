#!/bin/bash
# Fix OCLint dylib paths on macOS
# The Homebrew OCLint formula has hardcoded paths to libc++ and libunwind
# that don't exist on most systems. This script fixes all binaries to use
# the correct LLVM paths.

set -e

OCLINT_DIR="/opt/homebrew/Caskroom/oclint/24.11/oclint-24.11"
LLVM_DIR="/opt/homebrew/Cellar/llvm"

# Find the installed LLVM version
LLVM_VERSION=$(ls -1 "$LLVM_DIR" | head -1)
LLVM_PATH="$LLVM_DIR/$LLVM_VERSION"

if [ ! -d "$LLVM_PATH" ]; then
    echo "Error: LLVM not found at $LLVM_PATH"
    exit 1
fi

echo "Fixing OCLint binaries to use LLVM at: $LLVM_PATH"

# Find all binaries and dylibs
for file in $(find "$OCLINT_DIR" -type f \( -name "oclint*" -o -name "*.dylib" \)); do
    # Check if it's a Mach-O binary
    if file "$file" | grep -q "Mach-O"; then
        # Fix libc++.1.dylib
        if otool -L "$file" 2>/dev/null | grep -q "@rpath/libc++.1.dylib"; then
            install_name_tool -change @rpath/libc++.1.dylib "$LLVM_PATH/lib/c++/libc++.1.dylib" "$file" 2>/dev/null || true
        fi
        # Fix libunwind.1.dylib
        if otool -L "$file" 2>/dev/null | grep -q "@rpath/libunwind.1.dylib"; then
            install_name_tool -change @rpath/libunwind.1.dylib "$LLVM_PATH/lib/unwind/libunwind.1.dylib" "$file" 2>/dev/null || true
        fi
    fi
done

echo "Done! OCLint fixed successfully."
