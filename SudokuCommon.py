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

""" Common Sudoku Stuff, Glue with the model """

import BaseApp
import Sudoku
import observer

# Glue with the model

class MyGrid(Sudoku.Grid):

    def _make_cells(self):
        nvar=self.getNumVars()
        return [MyCell(self, index, nvar) for index in xrange(len(self))]
        
class MyCell(Sudoku.Cell, observer.Subject):

    def __init__(self, grid, index, max=9):
        Sudoku.Cell.__init__(self,max)
        observer.Subject.__init__(self)
        self._grid  = grid
        self._index = index

    def reset(self):
        Sudoku.Cell.reset(self)
        self.notify()

    def resetDomain(self):
        Sudoku.Cell.resetDomain(self)
        self.notify()

    def set(self, value):
        Sudoku.Cell.set(self, value)
        self.notify()

    def markImpossible(self,value):
        Sudoku.Cell.markImpossible(self, value)
        self.notify()


class History(object):
    """Handles the application History"""

    def __init__(self,maxSize=0):
        self.maxSize=maxSize
        self.undo=[]
        self.redo=[]

    def Stack(self,itm):
        self.redo=[]
        self.undo.append(itm)
        if self.maxSize!=0 and len(self.undo)>self.maxSize:
            self.undo.pop(0)

    def Undo(self):
        try:
            itm=self.undo.pop()
            self.redo.append(itm)
            return itm
        except IndexError:
            return None

    def Redo(self):
        try:
            itm=self.redo.pop()
            self.undo.append(itm)
            return itm
        except IndexError:
            return None

    def isEmpty(self):
        return len(self.undo)==0

    def isRedoEmpty(self):
        return len(self.redo)==0

    def Clear(self):
        self.undo=[]
        self.redo=[]



class SudokuBaseApplication(BaseApp.BaseApplication):
    """Base Common Sudoku Aplication"""

    def _setConfigDefaults(self):
        """
        Sets the configuration defaults
        Must be overrided
        """
        self.config.set("global","app.gettext.locales","locales")
        self.config.set("global","app.gettext.domain","alssudoku")

    def GetAboutMessage(self):
        return (_(u"""
Al's WxWidgets Python Sudoku.
Another Sudoku solver, written 100%% in Python and wxWidgets.

Version: %s

Original Author: Copyright (c) 2006 Juan Manuel Gimeno Illa
Current Author: Copyright (C) 2007 Alberto Montañola Lacort

This program is free software; you can redistribute it and/or\
 modify it under the terms of the GNU General Public License as\
 published by the Free Software Foundation; either version 2 of\
 the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,\
 but WITHOUT ANY WARRANTY; without even the implied warranty of\
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.\
 See the GNU General Public License for more details.

""") %(self.GetAppVersion(),),
                      _("About %s") %("Al's WxWidgets Python Sudoku",))

