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
import Tkinter as tki
import tkFont
from Sudoku import Grid, Cell, i2r, i2c, rc2b, Contradiction, solve
import gettext
gettext.install("awxsudoku","locales",True)

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
                   text=_("Load"),
                   command=self._do_loadFromFile).pack(side=tki.LEFT)

        tki.Button(buttonsFrame,
                   text=_("Solve"),
                   command=self._do_solve).pack(side=tki.LEFT)
        
        hide_possib = tki.IntVar()
        hide_possib.set(0)
        tki.Checkbutton(buttonsFrame,
                        text=_("Show Hints"),
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
        filename = askopenfilename(filetypes=((_("GPE files"),"*.gpe"),
                                                (_("TSudoku files"),"*.tsdk"),
                                                (_("All Files"), "*")))
        if not isinstance(filename, basestring): return # Exit if Cancel or Closed
        try:
            grid=Grid()
            grid.load_from_file(filename)
            self._grid.copy_values_from(grid)
        except Contradiction: # Dialog guarantees filename exists
            from tkMessageBox import showinfo
            showinfo(message=_("Invalid sudoku file"))

    def _do_solve(self):
        try:
            grid = Grid()
            grid.copy_values_from(self._grid)
            solution = solve(grid)
        except Contradiction:
            solution = None
        if solution is None:
            from tkMessageBox import showinfo
            showinfo(message=_("No solution has been found."))
        else:
            self._grid.copy_values_from(solution)

if __name__ == "__main__":
    # open log
    import sys,logging
    log = logging.mlog(sys.stdout,"stdout.log","w")
    logerr = logging.mlog(sys.stderr,"stderr.log","w")
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout=log
    sys.stderr=logerr
    try:
        root = tki.Tk()
        root.resizable(0,0)
        root.title("tkSudoku")
        Sudoku(root)
        root.mainloop()
    except:
        import traceback
        trace=file("traceback.log","w")
        traceback.print_exc(file=trace)
        trace.close()
        traceback.print_exc(file=sys.stderr)
        import wx
        app=wx.App(redirect=False)
        wx.MessageBox(traceback.format_exc(),"Traceback",wx.ICON_ERROR)
    # close log
    sys.stdout=old_stdout
    sys.stderr=old_stderr
    log.close()
    logerr.close()
