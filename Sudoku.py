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
# -----------------------------------------------------------------------------
# ORIGINAL LICENSE FOR tkSudoku.py - Revision 49 and Revision 52
#
# Only the pieces of code submitted under Revisions 49 and 52
# are under the next License. The revision numbers may change when the
# code is moved from the MPL private repository to the projects public
# one. (Current Address of this file $HeadURL$)
#
# Copyright (c) 2006 Juan Manuel Gimeno Illa
# 
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""A Sudoku Solver"""

try:
    set
except NameError:
    from sets import Set as set
from copy import deepcopy

# Suported Sudoku types

class SudokuType(object): pass

class NormalSudoku(SudokuType):
    """
    Defines a Normal Sudoku
    """

    def __init__(self,row_blocks=3,col_blocks=3,rows_per_block=3,cols_per_block=3):
        self.r=row_blocks
        self.c=col_blocks
        self.sbr=rows_per_block
        self.sbc=cols_per_block

    def __len__(self):
        return self.getTotalNumCols()*self.getTotalNumRows()

    def getTotalNumRows(self):
        """
        Returns the total number of rows (or colum height)
        """
        return self.r*self.sbr

    def getTotalNumCols(self):
        """
        Returns total length size (num cols) of a row
        """
        return self.c*self.sbc

    def getBlockDimensions(self):
        """
        Returns the dimensions of a Sudoku Block
        Height X Width (rows x cols)
        """
        return self.sbr,self.sbc

    def getNumCols(self):
        """
        Returns the Total sudoku width (cols) in blocks
        """
        return self.c

    def getNumRows(self):
        """
        Returns the Total sudoku height (rows) in blocks
        """
        return self.r

    def getNumVars(self):
        """
        Returns the total number of possible vars for this Sudoku
        """
        return self.sbr*self.sbc
        

class SamuraiSudoku(NormalSudoku):

    def __init__(self,row_blocks=3,col_blocks=3,rows_per_block=3,cols_per_block=3):
        self.r=row_blocks*2+1
        self.c=col_blocks*2+1
        self.sbr=rows_per_block
        self.sbc=cols_per_block

# Auxiliary functions to transform cordinates on the grid

class CoordinateInterface(object):
    """
    Defines a mixin with functions to transform coordinates on the grid
    """

    def __init__(self,stype=None):
        if stype==None:
            stype=NormalSudoku()
        elif isinstance(stype,CoordinateInterface):
            stype=stype._type
        elif not isinstance(stype,SudokuType):
            raise TypeError, "stype is neither a CoordinateInterface or a SudokuType"
        self._type=stype
        self._rowsize=self.getTotalNumCols()
        self._cached_len=len(self._type)

    def __getattr__(self,attr):
        return getattr(self._type,attr)

    def __len__(self):
        return self._cached_len

    def rc2i(self,row,col):
        return row * self._rowsize + col

    def i2r(self,index):
        return index / self._rowsize

    def i2c(self,index):
        return index % self._rowsize

    def i2rc(self,index):
        return self.i2r(index), self.i2c(index)

    def rc2b(self,row, col):
        brow = row / self.sbr
        bcol = col / self.sbc
        return brow * self.c + bcol

    def t2i(self,tidx):
        if not isinstance(tidx,tuple):
            return tidx
        elif len(tidx)==2:
            return self.rc2i(tidx)
        else:
            raise TypeError, "Too many items in idx tuple"

    def t2r(self,tidx):
        if not isinstance(tidx,tuple):
            return self.i2r(tidx)
        elif len(tidx)==2:
            return tidx[0]
        else:
            raise TypeError, "Too many items in idx tuple"

    def t2c(self,tidx):
        if not isinstance(tidx,tuple):
            return self.i2r(tidx)
        elif len(tidx)==2:
            return tidx[1]
        else:
            raise TypeError, "Too many items in idx tuple"

    def t2rc(self,tidx):
        if not isinstance(tidx,tuple):
            return self.i2rc(tidx)
        elif len(tidx)==2:
            return tidx
        else:
            raise TypeError, "Too many items in idx tuple"


# Model classes

class Contradiction(Exception): pass

class Grid(CoordinateInterface):

    def __init__(self,stype=None):
        CoordinateInterface.__init__(self,stype)
        self._buildUp()
        self._cells = self._make_cells()

    def _buildUp(self):
        # Blocks that restrict values (no repetition in cols, rows and boxes)
        l=len(self)
        nrt=self.r*self.sbr
        nct=self.c*self.sbc
        block_size=self.c * self.sbc * self.sbr
    
        self._rows = [[i for i in xrange(l) if self.i2r(i)==row]
                      for row in xrange(nrt)]
        self._cols = [[i for i in xrange(l) if self.i2c(i)==col]
                      for col in xrange(nct)]
        self._boxes = [[self.rc2i(row, col) + self.sbc * bcol + block_size * brow
                        for row in xrange(self.sbr) for col in xrange(self.sbc)]
                        for brow in xrange(self.r) for bcol in xrange(self.c)]
        self._blocks = self._rows + self._cols + self._boxes
    
    def _make_cells(self):
        nvar=self.getNumVars()
        return [Cell(nvar) for _ in xrange(len(self))]

    def reset(self):
        for cell in self._cells: cell.reset()

    def resetDomain(self):
        for cell in self._cells: cell.resetDomain()

    def set(self, idx, value=None):
        """Sets value to the cell and propagates restrictions"""
        row, col = self.t2rc(idx)
        self._cells[self.rc2i(row, col)].set(value)
        for rest in (self._rows[row],
                     self._cols[col], 
                     self._boxes[self.rc2b(row, col)]):
            for index in rest:
                if self._cells[index].get() == 0:
                    self._cells[index].markImpossible(value)

    def unset(self, idx):
        """UnSets value to the cell and propagates restrictions"""
        self._cells[self.t2i(idx)].reset()
        self.UpdateRestrictions()

    def UpdateRestrictions(self):
        self.resetDomain()
        for index, cell in enumerate(self._cells):
            if cell.get()!=0:
                self.set(index,cell.get())

    def copy_values_from(self, from_grid):
        self.reset()
        for index, from_cell in enumerate(from_grid._cells):
            if from_cell.get() != 0:
                self.set(index, from_cell.get())

    def load_from_file(self, filename):
        f=file(filename)
        if filename.lower().endswith(".gpe"):
            ftype="gpe"
        else:
            ftype="tsdk"
        self.load_from_stream(f,ftype)
        f.close()

    def load_from_stream(self, data, ftype):
        # Does NOT control any error !!!!
        # Error control is performed in the calling code
        self.reset()
        if ftype=="gpe":
            import xmlparser
            p=xmlparser.XMLParser()
            p.parse(data.read())
            for cell in p.xworksheet[0].xcell:
                if int(cell.pvalue)!=0:
                    self.set(idx=int(cell.pidx),value=int(cell.pvalue))
        else:
            for row, line in enumerate(data):
                for col, value in enumerate(line.strip()):
                    if value != "0":
                        self.set((row, col), int(value))

        
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

    def __init__(self,max=9):
        self.max=max
        # To avoid problems with subclasses that redefine reset
        Cell.reset(self)

    def reset(self):
        self._value = 0
        self._possibls = set(xrange(1,self.max+1))

    def resetDomain(self):
        if self._value == 0:
            self._possibls = set(xrange(1,self.max+1))
        
    def set(self, value):
        if value not in self._possibls:
            print value,self._possibls
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
            raise Contradiction
        
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
            new_grid.set((row,col),value)
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
            grid.set((row, col), value)

def getSingletons(grid):
    return [(grid.i2r(i), grid.i2c(i), grid._cells[i].getPossibleValues()[0])
            for i in xrange(len(grid)) if grid._cells[i].isSingleton()]

def getUniques(grid):
    result = []
    for block in grid._blocks:
        for i, index in enumerate(block):
            if grid._cells[index].isUndecided():
                possibilities = set(grid._cells[index].getPossibleValues())
                for j in block[:i] + block[i+1:]:
                    possibilities -= set(grid._cells[j].getPossibleValues())
                if len(possibilities) == 1:
                    result.append((grid.i2r(index), grid.i2c(index), possibilities.pop()))
    return result

def findBranchingCell(grid):
    # Workaround for anyone attempting to solve an empty Sudoku
    minindex = 0
    minvalues = [1,]
    # End workaround
    minspan = grid.getNumVars() # was 9 for an 3 3 3 3 sudoku
    for index in xrange(len(grid)):
        if grid._cells[index].isUndecided():
            values = grid._cells[index].getPossibleValues()
            if len(values) < minspan:
                minspan = len(values)
                minvalues = values
                minindex = index
                if minspan ==2: break
    return grid.i2r(minindex), grid.i2c(minindex), minvalues 
	

