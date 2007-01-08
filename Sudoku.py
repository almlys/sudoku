#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# $Id$
#
#    Copyright (c) 2006 Juan Manuel Gimeno Illa
#    Copyright (C) 2007 Alberto Montañola Lacort
#    See the file AUTHORS for more info
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
#    USA.
#
#    Please see the file COPYING for the full license.
#

"""A Sudoku Solver"""

try:
    set
except NameError:
    from sets import Set as set
from copy import deepcopy

# Auxiliary functions to transform cordinates on the grid

def rc2i(row, col):
    return row * 9 + col

def i2r(index):
    return index / 9

def i2c(index):
    return index % 9

def i2rc(index):
    return i2r(index), i2c(index)

def rc2b(row, col):
    brow = row / 3
    bcol = col / 3
    return brow * 3 + bcol

# Model classes

class Contradiction(Exception): pass

class Grid(object):
        
    # Blocks that restrict values (no repetition in cols, rows and boxes)
    
    _rows  = [[i for i in xrange(81) if i2r(i)==row] for row in xrange(9)]
    _cols  = [[i for i in xrange(81) if i2c(i)==col] for col in xrange(9)]
    _boxes = [[rc2i(row, col) + 3 * bcol + 27 * brow
               for row in xrange(3) for col in xrange(3)] 
              for brow in xrange(3) for bcol in xrange(3)]
    _blocks = _rows + _cols + _boxes
    
    def __init__(self):
        self._cells = self._make_cells()

    def _make_cells(self):
        return [Cell() for _ in xrange(81)]

    def reset(self):
        for cell in self._cells: cell.reset()

    def set(self, row=None, col=None, value=None, idx=None):
        """Sets value to the cell and propagates restrictions"""
        if value==None:
            raise TypeError, "Value argument not supplied!"
        if idx!=None:
            row, col = i2rc(idx)
        elif row==None or col==None:
            raise TypeError, "Neither of (row, col) or idx required arguments were supplied"
        self._cells[rc2i(row, col)].set(value)
        for rest in (Grid._rows[row],
                     Grid._cols[col], 
                     Grid._boxes[rc2b(row, col)]):
            for index in rest:
                if self._cells[index].get() == 0:
                    self._cells[index].markImpossible(value)

    def copy_values_from(self, from_grid):
        self.reset()
        for index, from_cell in enumerate(from_grid._cells):
            if from_cell.get() != 0:
                self.set(i2r(index), i2c(index), from_cell.get())

    def load_from_file(self, filename):
        # Does NOT control any error !!!!
        self.reset()
        if filename.endswith(".gpe"):
            import xmlparser
            p=xmlparser.XMLParser()
            p.readfile(filename)
            for cell in p.xworksheet[0].xcell:
                if int(cell.pvalue)!=0:
                    self.set(idx=int(cell.pidx),value=int(cell.pvalue))
        else:
            for row, line in enumerate(file(filename)):
                for col, value in enumerate(line.strip()):
                    if value != "0":
                        self.set(row, col, int(value))
        
    def isSolved(self):
        for cell in self._cells:
            if cell.get() == 0: return False
        return True
	
    def print_(self):
        for row in xrange(9):
            if row % 3 == 0: print '-' * 25
            for col in xrange(9):
                if col % 3 == 0: print '|',
                print self._cells[rc2i(row, col)].get(),
            print '|'
        print '-'*25
   
class Cell(object):

    def __init__(self):
        # To avoid problems with subclasses that redefine reset
        Cell.reset(self)

    def reset(self):
        self._value = 0
        self._possibls = set(xrange(1,10))
        
    def set(self, value):
        if value not in self._possibls:
            raise Contradiction()
        self._value = value
        self._possibls = set((value,))

    def get(self):
        return self._value
    
    def getPossibleValues(self):
        return list(self._possibls)

    def markImpossible(self,value):
        self._possibls.discard(value)
        if len(self._possibls) == 0:
            raise Contradiction()
        
    def isSingleton(self):
        return self._value == 0 and len(self._possibls) == 1
    
    def isUndecided(self):
        return self._value == 0 and len(self._possibls) > 1

# Solver functions

def solve(grid):
    stack = [grid]
    while not len(stack) == 0:
        current = stack.pop()
        try:
            applyHeuristics(current)
        except Contradiction:
            continue
        if current.isSolved():
            return current
        row, col, values = findBranchingCell(current)
        for value in values:
            new_grid = deepcopy(current)
            new_grid.set(row,col,value)
            stack.append(new_grid)
    return None

def applyHeuristics(grid): 
    while(True):
        for heuristic in (getSingletons, getUniques):
            deduced =  heuristic(grid)
            if len(deduced) != 0: break # getS more efficient than getU
        if len(deduced) == 0:
            return
        for row, col, value in deduced:
            grid.set(row, col, value)

def getSingletons(grid):
    return [(i2r(i), i2c(i), grid._cells[i].getPossibleValues()[0])
            for i in xrange(81) if grid._cells[i].isSingleton()]

def getUniques(grid):
    result = []
    for block in Grid._blocks:
        for i, index in enumerate(block):
            if grid._cells[index].isUndecided():
                possibilities = set(grid._cells[index].getPossibleValues())
                for j in block[:i] + block[i+1:]:
                    possibilities -= set(grid._cells[j].getPossibleValues())
                if len(possibilities) == 1:
                    result.append((i2r(index), i2c(index), possibilities.pop()))
    return result

def findBranchingCell(grid):
    minspan = 9
    for index in xrange(81):
        if grid._cells[index].isUndecided():
            values = grid._cells[index].getPossibleValues()
            if len(values) < minspan:
                minspan = len(values)
                minvalues = values
                minindex = index
                if minspan ==2: break
    return i2r(minindex), i2c(minindex), minvalues 
	

