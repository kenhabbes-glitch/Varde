#!/bin/bash
# go.sh [side] : bygg, lag pdf og høyoppløst png av en side
cd "$(dirname "$0")"
python3 build.py || exit 1
node pdf.js || exit 1
p=${1:-1}
rm -f hi/*; pdftoppm -r 170 -png -f $p -l $p schem.pdf hi/p
ls hi
