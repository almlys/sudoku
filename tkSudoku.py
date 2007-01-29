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

import Tkinter as tki
import tkFont
import SudokuCommon
import Sudoku
import observer


# View classes

class TCell(tki.Frame,observer.Observer):
    """A TCells is the view of a Sudoku's cell"""
    
    def __init__(self, master, row, col, bg):
        observer.Observer.__init__(self)
        tki.Frame.__init__(self,master, bg=bg)

        self._possibls = tki.StringVar()
        label=tki.Label(self,
                        textvariable=self._possibls,
                        width=9,
                        font="Arial 9",
                        justify=tki.CENTER,
                        bg=bg)
        label.pack()
        self._value_var = tki.StringVar()
        self._value_entry = tki.Entry(self,
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

        try:
            self._hide_possib = self.master.parent.hide_possib
            self._hide_possib.trace_variable("w", self.update)
        except AttributeError:
            # Parent app does not have a hide_possib variable implemented
            self._hide_possib = tki.IntVar()

        try:
            self._focus = self.master._focus
        except AttributeError:
            self._focus = tki.IntVar()

        try:
            self._history_hook = self.master.parent._history_callback
        except AttributeError:
            self._history_hook = None

        self._row = row
        self._col = col

        
    def update(self, *args):
        """The model cell has changed so we must update the view"""
        mcell = self.getSubject()
        if mcell._value == 0:
            new_value = ""
            # When model resets, we must re-enable entries
            #self._value_entry.config(state=tki.NORMAL)
        else:
            new_value = str(mcell._value)
            #self._value_entry.config(state=tki.DISABLED)
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
        old_value = mcell._value
        try:
            new_value = int(self._value_var.get())
        except ValueError:
            new_value = 0
        if new_value==0:
            self._value_var.set("")
        if new_value == old_value:
            return

        if old_value!=0:
            mcell._grid.unset(mcell._index)
        if new_value!=0:
            try:
                mcell._grid.set(mcell._index, new_value)
            except Sudoku.Contradiction:
                mcell._grid.unset(mcell._index)
                new_value=0

        if new_value!=old_value and self._history_hook != None:
            self._history_hook("s",mcell._index,old_value,new_value)

    def on_move(self, event):
        key = event.keysym
        r , c = self._row , self._col
        if   key == "Up"   : r = (r - 1) % 9
        elif key == "Down" : r = (r + 1) % 9
        elif key == "Left" : c = (c - 1) % 9
        elif key == "Right": c = (c + 1) % 9
        self._focus.set(self.getSubject()._grid.rc2i(r, c))


class TGrid(tki.Frame):
    """Represents the 9x9 grid formed by 3x3 Tboxes"""
    def __init__(self, master, master_panel=None):
        if master_panel==None:
            master_panel=master
        self.parent=master
        tki.Frame.__init__(self,master_panel,borderwidth=2,relief=tki.GROOVE)
        self._focus = tki.IntVar()
        self._focus.trace_variable("w", self.focus_set)
        self._tcells = [self._make_tcell(r, c)
                        for r in xrange(9)
                        for c in xrange(9)]
        self.pack()

    def _make_tcell(self, row, col):
        #background = ("#cb83ac","#cb9eac")[Sudoku.rc2b(row, col) % 2],
        background = ("#cb83ac","#cb9eac")[((row/3)*3 + (col/3)) % 2],
        tcell = TCell(self,
                      row,
                      col,
                      background)
        tcell.grid(row=row, column=col)
        return tcell
    
    def update(self):
        for tcell in self._tcells:
            tcell.instance().update()

    def focus_set(self, *args):
        self._tcells[self._focus.get()]._value_entry.focus_set()
     

class StatusBar(tki.Frame):
    """Status Bar for our app"""

    def __init__(self,master):
        tki.Frame.__init__(self,master)
        self.label = tki.Label(self,bd=1,relief=tki.SUNKEN,anchor=tki.W)
        self.label.pack(fill=tki.X)

    def set(self,val):
        self.label.config(text=val)
        self.label.update_idletasks()

    def clear(self):
        self.label.config(text="")
        self.label.update_idletasks()


# Controller class 

class SudokuFrame(tki.Frame):
    """Application class"""
    
    def __init__(self, app):
        tki.Frame.__init__(self,app.root)
        self.app=app
        self._bind_callbacks()
        self._create_tki_vars()
        self._create_history()
        self._create_view()
        self._create_model()
        self._connect()

    def _bind_callbacks(self):
        self.master.protocol("WM_DELETE_WINDOW", self._do_exit)

    def _create_tki_vars(self):
        self.hide_possib = tki.IntVar()
        self.hide_possib.set(0)
        self.app_language = tki.StringVar()
        self.app_language.set(self.app.GetLanguage())
        self.app_language.trace_variable("w",self._do_changeLanguage)

    def _create_history(self):
        self.History=SudokuCommon.History()

    def _create_view(self):
        self.pack()
        self._create_menu()
        self._create_3layout()
        self._create_toolbar()
        self._create_sudoku()
        self._create_statusBar()

    def _create_menu(self):
        try:
            self.menu.destroy()
        except AttributeError:
            pass
        self.menu = tki.Menu(self.master)
        self.master.config(menu=self.menu)

        filemenu = tki.Menu(self.menu)
        self.menu.add_cascade(label=_("File"), menu=filemenu)
        filemenu.add_command(label=_("New..."), command=self._do_new)
        filemenu.add_command(label=_("Open..."), command=self._do_loadFromFile)
        filemenu.add_command(label=_("Open URL..."), command=self._do_loadFromURL)
        #filemenu.add_command(label=_("Save..."), command=self._do_save)
        filemenu.add_separator()
        filemenu.add_command(label=_("Exit"), command=self._do_exit)

        sudomenu = tki.Menu(self.menu)
        self.menu.add_cascade(label=_("Sudoku"), menu=sudomenu)
        sudomenu.add_command(label=_("Solve"), command=self._do_solve)
        sudomenu.add_separator()
        sudomenu.add_command(label=_("Undo"), command=self._do_undo, state=tki.DISABLED)
        sudomenu.add_command(label=_("Redo"), command=self._do_redo, state=tki.DISABLED)
        self._sudomenu=sudomenu

        optsmenu=tki.Menu(self.menu)
        self.menu.add_cascade(label=_("Options"), menu=optsmenu)
        optsmenu.add_checkbutton(label=_("Show Hints"), variable=self.hide_possib)

        langmenu=tki.Menu(optsmenu)
        optsmenu.add_cascade(label=_("Change Language"), menu=langmenu)

        tmplglist=[]
        for k,l in self.app.GetLanguages().iteritems():
            tmplglist.append((_(l),k))
        tmplglist.sort()
        
        for lan,k in tmplglist:
            langmenu.add_radiobutton(label=lan, variable=self.app_language, value=k)

        helpmenu=tki.Menu(self.menu)
        self.menu.add_cascade(label=_("Help"), menu=helpmenu)
        #helpmenu.add_command(label=_("Help"), command=self._do_help)
        #helpmenu.add_command(label=_("Check for updates..."), command=self._do_checkForUpdates)
        #helpmenu.add_command(label=_("Console..."), command=self._do_console)
        helpmenu.add_command(label=_("About..."), command=self._do_about)

    def _create_3layout(self):
        self.lToolBar = tki.Frame(self)
        self.lToolBar.pack()
        self.lSudokuGrid = tki.Frame(self)
        self.lSudokuGrid.pack()
        self.lStatusBar = tki.Frame(self)
        self.lStatusBar.pack(side=tki.BOTTOM,fill=tki.X)

    def _create_toolbar(self):
        try:
            self.ToolBar.destroy()
        except AttributeError:
            pass

        self.ToolBar = tki.Frame(self.lToolBar)
        self.ToolBar.pack()

        tki.Button(self.ToolBar,
                   text=_("Load"),
                   command=self._do_loadFromFile).pack(side=tki.LEFT)

        tki.Button(self.ToolBar,
                   text=_("Solve"),
                   command=self._do_solve).pack(side=tki.LEFT)

        self._undobtn=tki.Button(self.ToolBar,
                                 text=_("Undo"),
                                 command=self._do_undo,
                                 state=tki.DISABLED)
        self._undobtn.pack(side=tki.LEFT)
        self._redobtn=tki.Button(self.ToolBar,
                                 text=_("Redo"),
                                 command=self._do_redo,
                                 state=tki.DISABLED)
        self._redobtn.pack(side=tki.LEFT)
        
        tki.Checkbutton(self.ToolBar,
                        text=_("Show Hints"),
                        variable=self.hide_possib).pack(side=tki.LEFT)


    def _create_sudoku(self):
        self._tgrid = TGrid(self,self.lSudokuGrid)

    def _create_statusBar(self):
        self.StatusBar = StatusBar(self.lStatusBar)
        self.StatusBar.pack(side=tki.BOTTOM,fill=tki.X)
        #self.StatusBar.set(_("Idle"))

    def _create_model(self):
        self._grid = SudokuCommon.MyGrid()

    def _connect(self):
        for index in xrange(81):
            mcell = self._grid._cells[index]
            tcell = self._tgrid._tcells[index]
            mcell.attach(tcell)
            mcell.notify()

    # History

    def EnableUndo(self,enabled=True):
        if enabled:
            self._undobtn.config(state=tki.NORMAL)
            self._sudomenu.entryconfigure(3,state=tki.NORMAL)
        else:
            self._undobtn.config(state=tki.DISABLED)
            self._sudomenu.entryconfigure(3,state=tki.DISABLED)

    def EnableRedo(self,enabled=True):
        if enabled:
            self._redobtn.config(state=tki.NORMAL)
            self._sudomenu.entryconfig(4,state=tki.NORMAL)
        else:
            self._redobtn.config(state=tki.DISABLED)
            self._sudomenu.entryconfig(4,state=tki.DISABLED)
    
    def _history_callback(self,*args):
        self.EnableUndo(True)
        self.EnableRedo(False)
        self.History.Stack(args)
        print args

    # Actions

    def _do_exit(self):
        from tkMessageBox import askokcancel
        if askokcancel(title=_("Are you sure?"),
                                    message=_("Are you really sure that you wish to quit?")):
            self.master.destroy()

    def _do_new(self):
        print "New"
        self._grid.reset()
    
    def _do_loadFromFile(self):
        # TODO: Check errors !!!
        from tkFileDialog import askopenfilename
        filename = askopenfilename(filetypes=((_("GPE files"),"*.gpe"),
                                                (_("TSudoku files"),"*.tsdk"),
                                                (_("All Files"), "*")))
        if not isinstance(filename, basestring): return # Exit if Cancel or Closed
        self.StatusBar.set(_("Opening %s, please wait...") %(filename,))
        try:
            grid=Sudoku.Grid()
            grid.load_from_file(filename)
            self._grid.copy_values_from(grid)
        except Sudoku.Contradiction: # Dialog guarantees filename exists
            from tkMessageBox import showinfo
            showinfo(message=_("Invalid sudoku file"))
        except Exception, detail:
            # Any other issue, is a filesystem, parse, etc, etc, etc... error
            from tkMessageBox import showerror
            showerror(message=(_("Malformed, unconsistent, or unexistent file.\n%s") %(detail,)))
        self.StatusBar.set("")

    def _do_loadFromURL(self):
        print "open url"
        from tkSimpleDialog import askstring
        filename = askstring(_("Enter the URL"),_("Enter the URL"),
                             initialvalue="http://sudoku.udl.es/Problems/Easy-4-1.gpe")
        if not isinstance(filename, basestring): return
        self.StatusBar.set(_("Opening %s, please wait...") % (filename,))
        import urllib2 as urllib
        from tkMessageBox import showinfo
        try:
            f=urllib.urlopen(filename)
            grid=Sudoku.Grid()
            if filename.lower().endswith(".gpe"):
                ftype="gpe"
            else:
                ftype="tsdk"
            grid.load_from_stream(f,ftype)
            self._grid.copy_values_from(grid)
            f.close()
        except Sudoku.Contradiction:
            f.close()
            showinfo(message=_("Invalid sudoku file"),title=_("Invalid sudoku file"))
        except urllib.HTTPError,detail:
            showinfo(message=_("The server said:\n%s\nRequesting the %s resource") %(detail,filename),
                          title=_("Remote server error"))
        except (urllib.URLError,ValueError),detail:
            showinfo(message=_("Cannot open %s, reason %s") %(filename,detail))
        except Exception, detail:
            # Any other issue, is a filesystem, parse, etc, etc, etc... error
            from tkMessageBox import showerror
            showerror(message=(_("Malformed, unconsistent, or unexistent file.\n%s") %(detail,)))
        self.StatusBar.set("")


    def _do_solve(self):
        self.StatusBar.set(_("Solving Sudoku, please wait...."))
        try:
            grid = Sudoku.Grid()
            grid.copy_values_from(self._grid)
            solution = Sudoku.solve(grid)
        except Sudoku.Contradiction:
            solution = None
        if solution is None:
            from tkMessageBox import showinfo
            showinfo(message=_("No solution has been found."))
        else:
            bkgrid = Sudoku.Grid()
            bkgrid.copy_values_from(self._grid)
            self._grid.copy_values_from(solution)
        self.StatusBar.set("")

    def _do_undo(self):
        print "undo"
        self.EnableRedo(True)
        hist = self.History.Undo()
        if self.History.isEmpty():
            self.EnableUndo(False)
        cmd = hist[0]
        if cmd=="s":
            # Single value was stacked
            idx, old, new = hist[1:]
            self._grid.unset(idx)
            if old!=0:
                self._grid.set(idx,old)
        elif cmd=="t":
            # An entire Sudoku was stacked
            pass
        else:
            raise NotImplemented

    def _do_redo(self):
        print "redo"
        self.EnableUndo(True)
        hist = self.History.Redo()
        if self.History.isRedoEmpty():
            self.EnableRedo(False)
        cmd = hist[0]
        if cmd=="s":
            idx, old, new = hist[1:]
            self._grid.unset(idx)
            if new!=0:
                self._grid.set(idx,new)

    def _do_changeLanguage(self, *args):
        print "change language %s" %(self.app_language.get())
        self.app.SetLanguage(self.app_language.get())
        self._create_menu()
        self._create_toolbar()

    def _do_about(self):
        from tkMessageBox import showinfo
        m,t=self.app.GetAboutMessage()
        showinfo(message=m,title=t)


class SudokuApp(SudokuCommon.SudokuBaseApplication):
    """main tki.Tk App"""

    def __init__(self):
        SudokuCommon.SudokuBaseApplication.__init__(self,config="alsSudoku.cfg")
        self._loadConfig()
        self._installGettext()
        self.root=tki.Tk()
        self.root.resizable(0,0)
        self.root.title("tkSudoku")
        SudokuFrame(self)

    def GetAppVersion(self):
        return "$Id$"
        
    def MainLoop(self):
        self.root.mainloop()
        
    def __del__(self):
        self._saveConfig()


if __name__ == "__main__":

    # open log
    redirect = False
    import sys,sdlogger
    if redirect:
        log = sdlogger.mlog(sys.stdout,"stdout.log","w")
        logerr = sdlogger.mlog(sys.stderr,"stderr.log","w")
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout=log
        sys.stderr=logerr
    try:
        app = SudokuApp()
        app.MainLoop()
        del app
    except:
        import traceback
        trace=file("traceback.log","w")
        traceback.print_exc(file=trace)
        trace.close()
        traceback.print_exc(file=sys.stderr)
        from tkMessageBox import showerror
        showerror("Traceback",traceback.format_exc())
    # close log
    if redirect:
        sys.stdout=old_stdout
        sys.stderr=old_stderr
        log.close()
        logerr.close()
