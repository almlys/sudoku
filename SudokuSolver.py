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

from copy import deepcopy
import Sudoku

# Solver functions

class Solver(object):
    def __init__(self,grid=None):
        if grid!=None:
            self.setGrid(grid)
        else:
            self.startup_grid=None

    def setGrid(self,grid):
        self.startup_grid=Sudoku.Grid(grid)
        self.stack=[deepcopy(self.startup_grid),]
        self.solution=None

    def step(self):
        try:
            current = self.stack.pop()
            try:
                applyHeuristics(current)
            except Sudoku.Contradiction:
                return False
            if current.isSolved():
                self.solution=current
                return True
            row, col, values = findBranchingCell(current)
            for value in values:
                new_grid = deepcopy(current)
                new_grid.set((row,col),value)
                self.stack.append(new_grid)
        except Sudoku.Contradiction:
            self.stack=[]
        return False

    def isFinished(self):
        return self.solution!=None or len(self.stack)==0

    def solve(self):
        while not len(self.stack) == 0:
            if self.step():
                return self.solution
        return None


def solve(grid):
    a=Solver(grid)
    return a.solve()


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
	

