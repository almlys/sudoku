#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# $Id$
#
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

from threading import Thread
from SudokuSolver import Solver

class SolverThread(Thread,Solver):
    """ A running thread """

    def __init__(self,grid=None):
        Thread.__init__(self)
        self.__running=False
        Solver.__init__(self,grid)

    def run(self):
        self.__running=True
        print "Started new solver thread"
        while not self.isFinished() and self.__running:
            self.step()
        print "The solver finished"
        if self.solution!=None:
            print "The solver found a solution"

    def stop(self):
        self.__running=False

class thSolver(object):
    """ A threaded Solver """

    def __init__(self):
        self.solver=None

    def setGrid(self,grid):
        # Stop an already running thread
        if self.solver!=None and self.solver.isAlive():
            print "is Alive"
            self.solver.stop()
            self.solver.join()

        if not (self.solver!=None
                and self.solver.startup_grid!=None
                and self.solver.solution!=None
                and self.solver.solution.contains(grid)):
            self.solver=SolverThread()
            self.solver.setGrid(grid)
            self.solver.start()

    def waitForSolution(self):
        if self.solver==None:
            return None

        if self.solver.isAlive():
            self.solver.join()

        return self.solver.solution


    def getHint(self):
        solution=self.waitForSolution()
        if solution==None: return None
        var=0
        idx=0
        # The Current UgLy Samurai implementation has cells with are zeroes
        # and we need to ignore them
        while var==0:
            import random
            idx=random.randrange(len(solution))
            var=solution._cells[idx].get()
        return idx,var


