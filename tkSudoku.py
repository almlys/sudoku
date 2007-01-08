#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# $Id$
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
import Tkinter as tki
import tkFont

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
	

# Util classes 

class Observer(object):
    def __init__(self):
        self._subject = None
	
    def setSubject(self,subject):
        self._subject = subject

    def getSubject(self):
        return self._subject
    
class Subject(object):
    def __init__(self):
        self._observers = []

    def attach(self, observer):
        observer.setSubject(self)
        self._observers.append(observer)

    def notify(self):
        for observer in self._observers:
            observer.update()
    
# View classes

class TGrid(object):
    """Represents the 9x9 grid formed by 3x3 Tboxes"""

    def __init__(self, master, hide_possib):
        self._widget = tki.Frame(master,
                                 borderwidth=2,
                                 relief=tki.GROOVE)
        self._focus = tki.IntVar()
        self._focus.trace_variable("w", self.focus_set)
        self._tcells = [self._make_tcell(r, c, hide_possib)
                        for r in xrange(9)
                        for c in xrange(9)]
        self._widget.pack()

    def _make_tcell(self, row, col, hide_possib):
        background = ("#cb83ac","#cb9eac")[rc2b(row, col) % 2],
        tcell = TCell(row,
                      col,
                      self._focus,
                      self._widget,
                      background,
                      hide_possib)
        tcell._widget.grid(row=row, column=col)
        return tcell
    
    def update(self):
        for tcell in self._tcells:
            tcell.instance().update()

    def focus_set(self, *args):
        self._tcells[self._focus.get()]._value_entry.focus_set()
     
class TCell(Observer):
    """A TCells is the view of a Sudoku's cell"""
    
    def __init__(self, row, col, focus, master, bg, hide_possib):
        Observer.__init__(self)
        self._widget = tki.Frame(master, bg=bg)

        self._possibls = tki.StringVar()
        label=tki.Label(self._widget,
                        textvariable=self._possibls,
                        width=9,
                        font="Arial 9",
                        justify=tki.CENTER,
                        bg=bg)
        label.pack()
        self._value_var = tki.StringVar()
        self._value_entry = tki.Entry(self._widget,
                                      width=1,
                                      font="Arial 18 bold",
                                      textvariable=self._value_var,
                                      bg=bg,
                                      highlightbackground=bg,
                                      disabledbackground=bg,
                                      disabledforeground=label["fg"])
        self._value_entry.bind('<Return>', self.on_change)
        self._value_entry.bind('<FocusOut>', self.on_change)
        self._value_entry.bind('<Up>', self.on_move)
        self._value_entry.bind('<Down>', self.on_move)
        self._value_entry.bind('<Left>', self.on_move)
        self._value_entry.bind('<Right>', self.on_move)
        self._value_entry.pack()

        hide_possib.trace_variable("w", self.update)
        self._hide_possib = hide_possib

        self._row = row
        self._col = col
        self._focus = focus
        
    def update(self, *args):
        """The model cell has changed so we must update the view"""
        mcell = self.getSubject()
        if mcell._value == 0:
            new_value = ""
            # When model resets, we must re-enable entries
            self._value_entry.config(state=tki.NORMAL)
        else:
            new_value = str(mcell._value)
            self._value_entry.config(state=tki.DISABLED)
        self._value_var.set(new_value)
        if self._hide_possib.get() == 0 or mcell._value != 0:
            new_possi = ""
        else:
            new_possi = list(mcell._possibls)
            new_possi.sort()
            new_possi = "".join([str(c) for c in new_possi])
        self._possibls.set(new_possi)
  
    def on_change(self, event):
        """The entry has changed so we must notify the model."""
        mcell = self.getSubject()
        try:
            new_value = int(self._value_var.get())
            mcell._grid.set(i2r(mcell._index), i2c(mcell._index), new_value)
            self._value_entry.config(state=tki.DISABLED)
        except (Contradiction, ValueError):
            self._value_var.set("")

    def on_move(self, event):
        key = event.keysym
        r , c = self._row , self._col
        if   key == "Up"   : r = (r - 1) % 9
        elif key == "Down" : r = (r + 1) % 9
        elif key == "Left" : c = (c - 1) % 9
        elif key == "Right": c = (c + 1) % 9
        self._focus.set(rc2i(r, c))
        
# Glue with the model

class MyGrid(Grid):

    def _make_cells(self):
        return [MyCell(self, index) for index in xrange(81)]
        
class MyCell(Cell, Subject):

    def __init__(self, grid, index):
        Cell.__init__(self)
        Subject.__init__(self)
        self._grid  = grid
        self._index = index
        
    def reset(self):
        Cell.reset(self)
        self.notify()
        
    def set(self, value):
        Cell.set(self, value)
        self.notify()

    def markImpossible(self,value):
        Cell.markImpossible(self, value)
        self.notify()

# Controller class 

class Sudoku(object):
    """Application class"""
    
    def __init__(self, master):
        self._create_view(master)
        self._create_model()
        self._connect()

    def _create_view(self, master):
        frame = tki.Frame(master)
        frame.pack()
        
        buttonsFrame = tki.Frame(frame)
        buttonsFrame.pack()

        tki.Button(buttonsFrame,
                   text="Load",
                   command=self._do_loadFromFile).pack(side=tki.LEFT)

        tki.Button(buttonsFrame,
                   text="Solve",
                   command=self._do_solve).pack(side=tki.LEFT)
        
        hide_possib = tki.IntVar()
        hide_possib.set(0)
        tki.Checkbutton(buttonsFrame,
                        text="Show Hints",
                        variable=hide_possib).pack(side=tki.LEFT)

        self._tgrid = TGrid(frame,
                            hide_possib=hide_possib)

    def _create_model(self):
        self._grid = MyGrid()

    def _connect(self):
        for index in xrange(81):
            mcell = self._grid._cells[index]
            tcell = self._tgrid._tcells[index]
            mcell.attach(tcell)
            mcell.notify()

    # Actions
    
    def _do_loadFromFile(self):
        # TODO: Check errors !!!
        from tkFileDialog import askopenfilename
        filename = askopenfilename(filetypes=(("TSudoku files","*.tsdk"),
                                              ("All Files", "*")))
        if not isinstance(filename, basestring): return # Exit if Cancel or Closed
        try:
            grid=Grid()
            grid.load_from_file(filename)
            self._grid.copy_values_from(grid)
        except Contradiction: # Dialog guarantees filename exists
            from tkMessageBox import showinfo
            showinfo(message="Invalid sudoku file")

    def _do_solve(self):
        try:
            grid = Grid()
            grid.copy_values_from(self._grid)
            solution = solve(grid)
        except Contradiction:
            solution = None
        if solution is None:
            from tkMessageBox import showinfo
            showinfo(message="No solution has been found.")
        else:
            self._grid.copy_values_from(solution)

if __name__ == "__main__":

    root = tki.Tk()
    root.resizable(0,0)
    root.title("tkSudoku")
    Sudoku(root)
    root.mainloop()

    
