#!/bin/sh

FILES="wxSudoku.py Sudoku.py tkSudoku.py"
xgettext -o sudoku.po $FILES
mv ca.po ca.po.bak
mv es.po es.po.bak
msgmerge -o ca.po ca.po.bak sudoku.po
msgmerge -o es.po es.po.bak sudoku.po
