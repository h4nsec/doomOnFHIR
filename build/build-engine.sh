#!/bin/sh
# Rebuild smartdoom-engine.js (doomgeneric -> single-file WebAssembly) using Docker + Emscripten.
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
WORK=$(mktemp -d)
git clone -q --depth 1 https://github.com/ozkl/doomgeneric.git "$WORK/doomgeneric"
cp "$HERE/doomgeneric_smart.c" "$WORK/doomgeneric/doomgeneric/"
cd "$WORK/doomgeneric/doomgeneric"
SRCS=$(grep '^SRC_DOOM' Makefile.emscripten | sed 's/SRC_DOOM = //; s/\.o/.c/g' | tr ' ' '\n' \
  | grep -v -E '^(doomgeneric_emscripten|i_sdlmusic|i_sdlsound)\.c$' | tr '\n' ' ')
docker run --rm -u "$(id -u):$(id -g)" -v "$PWD":/src -w /src emscripten/emsdk:3.1.74 \
  emcc -O2 -w $SRCS doomgeneric_smart.c -o smartdoom-engine.js \
  -s MODULARIZE=1 -s EXPORT_NAME=SmartDoomEngine -s SINGLE_FILE=1 -s INVOKE_RUN=0 \
  -s ALLOW_MEMORY_GROWTH=1 -s EXIT_RUNTIME=0 -s FORCE_FILESYSTEM=1 -s ENVIRONMENT=web \
  -s 'EXPORTED_FUNCTIONS=["_main","_smartdoom_key","_smartdoom_stats"]' \
  -s 'EXPORTED_RUNTIME_METHODS=["callMain","FS","HEAPU8","HEAP32"]'
cp smartdoom-engine.js "$HERE/../smartdoom-engine.js"
rm -rf "$WORK"
echo "wrote smartdoom-engine.js"
