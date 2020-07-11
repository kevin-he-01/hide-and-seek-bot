#! /usr/bin/env bash

for file in "$@"; do
    strip-hints "bot/$file" > "out/$file"
done
cd out && zip -r bot.zip . -x .gitignore