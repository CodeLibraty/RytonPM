#!/bin/bash

NUITKA_OPTIONS="--jobs=6 --output-dir=dist --standalone --onefile --follow-imports"
echo Сборка через Nuitka
python3 -m nuitka $NUITKA_OPTIONS cli.py

echo Сборка завершена
