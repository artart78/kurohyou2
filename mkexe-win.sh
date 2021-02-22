#!/bin/bash
for i in *.spec; do
    docker run -v "$(pwd):/src/" cdrx/pyinstaller-windows "pyinstaller $i"
done
