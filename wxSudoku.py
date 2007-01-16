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
    import wx
except ImportError:
    print "WxPython 2.6 or higher is required to run this application!!!"
    print
    print "You can get it from http://www.wxpython.org"
    print "Or you can just type as root \"apt-get install python-wxgtk2.6\" on Debian, Ubuntu and any other Debian based distros"
    print "On other distros you may try similar commands, yum, urpmi, emerge,..., just check your Distro documentation"
    print "but if you don't have root access you will need to manually install wxPython in your home directory, have fun!"
    #import webbrowser
    #webbrowser.open_new("http://www.wxpython.org")
    import sys
    sys.exit(-1)
import gettext
import Sudoku
import observer

# Glue with the model

class MyGrid(Sudoku.Grid):

    def _make_cells(self):
        return [MyCell(self, index) for index in xrange(81)]
        
class MyCell(Sudoku.Cell, observer.Subject):

    def __init__(self, grid, index):
        Sudoku.Cell.__init__(self)
        observer.Subject.__init__(self)
        self._grid  = grid
        self._index = index

    def reset(self):
        Sudoku.Cell.reset(self)
        self.notify()

    def set(self, value):
        Sudoku.Cell.set(self, value)
        self.notify()

    def markImpossible(self,value):
        Sudoku.Cell.markImpossible(self, value)
        self.notify()


class History(object):
    """Handles the application History"""

    def __init__(self):
        self.undo=[]
        self.redo=[]

    def Stack(self,itm):
        self.redo=[]
        self.undo.append(itm)

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


# View classes

class CellPanel(wx.Panel,observer.Observer):
    """A CellPanel is the view of a Sudoku's cell"""

    def __init__(self, parent, idx, bgcolor=(255,0,0), *args, **kwargs):
        self.parent=parent
        wx.Panel.__init__(self,parent,*args,**kwargs)
        self.SetBackgroundColour(bgcolor)
        observer.Observer.__init__(self)
        self.row, self.col = idx
        self._initLayout()

    def _initLayout(self):
        self._sizer=wx.GridSizer(0,1)
        self.SetSizer(self._sizer)
        self.HintsLabel=wx.StaticText(self,style=wx.ALIGN_RIGHT | wx.SIMPLE_BORDER)
        self.HintsLabel.SetLabel("123456789")
        self.HintsLabel.SetFont(wx.FFont(9,wx.FONTFAMILY_DEFAULT,face="Arial"))
        self._sizer.Add(self.HintsLabel,0,flag=wx.ALIGN_RIGHT | wx.EXPAND)
        self.TextBox=wx.TextCtrl(self,value="%i,%i" %(self.row,self.col),style=wx.TE_PROCESS_ENTER)
        self.TextBox.SetFont(wx.FFont(18,wx.FONTFAMILY_DEFAULT,face="Arial",flags=wx.FONTFLAG_BOLD))
        self.TextBox.SetBackgroundColour(self.GetBackgroundColour())
        #self.TextBox.SetSize((30,5))
        self.TextBox.Bind(wx.EVT_KEY_DOWN,self.OnKey)
        self.TextBox.Bind(wx.EVT_TEXT_ENTER,self.OnChange)
        self.TextBox.Bind(wx.EVT_KILL_FOCUS,self.OnChange)
        self._sizer.Add(self.TextBox,1,flag=wx.ALIGN_RIGHT | wx.EXPAND)

    def update(self, *args):
        """The model cell has changed so we must update the view"""
        mcell = self.getSubject()
        if mcell._value==0:
            new_value=""
        else:
            new_value=str(mcell._value)
        self.TextBox.SetValue(new_value)
        if self.parent._ShowHints and mcell._value==0:
            new_possi = list(mcell._possibls)
            new_possi.sort()
            new_possi = "".join([str(c) for c in new_possi])
        else:
            new_possi = ""
        self.HintsLabel.SetLabel(new_possi)

    def OnKey(self,evt):
        #print evt
        code=evt.GetKeyCode()
        if code==wx.WXK_UP:
            print "UP"
        elif code==wx.WXK_DOWN:
            print "DOWN"
        elif code==wx.WXK_RIGHT:
            print "RIGHT"
        elif code==wx.WXK_LEFT:
            print "LEFT"
        else:
            evt.Skip()

    def OnChange(self,evt):
        """The entry has changed so we must notify the model."""
        mcell = self.getSubject()
        old_value = mcell._value
        try:
            new_value = int(self.TextBox.GetValue())
        except ValueError:
            new_value = 0
        if new_value == old_value:
            return
        try:
            mcell._grid.set(mcell._index, new_value)
        except:
            pass
        self.parent.parent.EnableUndo(True)
        self.parent.parent.EnableRedo(False)
        self.parent.History.Stack([mcell._index,old_value,new_value])


class SudokuGridPanel(wx.Panel):
    """Represents the 9x9 grid formed by 3x3 Tboxes"""

    def __init__(self, parent, *args, **kwargs):
        wx.Panel.__init__(self,parent,*args,**kwargs)
        self.parent=parent
        self.SetBackgroundColour((48,7,11))
        self._ShowHints=False
        self.sbr=3
        self.sbc=3
        self.r=3
        self.c=3
        self._initLayout()
        self._addHistory()
        self._create_model()
        self._connect()

    def _initLayout(self):
        self._addGrid()

    def _addGrid(self):
        self._ViewCells=[None for a in xrange(self.r*self.c*self.sbc*self.sbr)]
        self._GridSizer=wx.GridSizer(self.r,self.c)
        self.SetSizer(self._GridSizer)
        for r in xrange(self.r):
            for c in xrange(self.c):
                flag=wx.ALL | wx.EXPAND
                bgcolor = ((0xCB,0x83,0xAC),(0xCB,0x9E,0xAC))[(r*self.r + c) % 2]
                cgrid=wx.GridSizer(self.sbr,self.sbc)
                self._GridSizer.Add(cgrid,1,border=1,flag=flag)
                for br in xrange(self.sbc):
                    for bc in xrange(self.sbr):
                        #itm=wx.TextCtrl(self,value="%i,%i" %(c*self.sbc + bc,r*self.sbr + br))s
                        itm=CellPanel(self,(r*self.sbr + br,c*self.sbc + bc),bgcolor)
                        cgrid.Add(itm,1,border=1,flag=wx.ALL | wx.EXPAND)
                        #itm.Bind(wx.EVT_KEY_DOWN, self.OnKey)
                        self._ViewCells[(r*self.sbr + br) * self.sbc * self.c + c*self.sbc + bc]=itm

    def _addHistory(self):
        self.History=History()

    def _create_model(self):
        self._ModelGrid=MyGrid()

    def _connect(self):
        for idx in xrange(81):
            mcell = self._ModelGrid._cells[idx]
            wcell = self._ViewCells[idx]
            mcell.attach(wcell)
            mcell.notify()

    def ShowHints(self,show):
        self._ShowHints=show
        for lala in self._ViewCells:
            lala.update()

    def Solve(self):
        try:
            grid = Sudoku.Grid()
            grid.copy_values_from(self._ModelGrid)
            solution = Sudoku.solve(grid)
        except Sudoku.Contradiction:
            solution = None
        if solution is None:
            return False
        else:
            self._ModelGrid.copy_values_from(solution)
            return True

    def Reset(self):
        self.History.Clear()
        self.parent.EnableRedo(False)
        self.parent.EnableUndo(False)
        self._ModelGrid.reset()

    def Undo(self):
        self.parent.EnableRedo(True)
        idx, old, new=self.History.Undo()
        if self.History.isEmpty():
            self.parent.EnableUndo(False)
        print idx,old
        self._ModelGrid.set(idx,old)

    def Redo(self):
        self.parent.EnableUndo(True)
        idx, old, new=self.History.Redo()
        if self.History.isRedoEmpty():
            self.parent.EnableRedo(False)
        print idx,new
        self._ModelGrid.set(idx,new)



class SudokuMainFrame(wx.Frame):
    """Sudoku Main Frame"""

    def __init__(self,app,parent=None):
        wx.Frame.__init__(self, parent, title="Al's WxWidgets Python Sudoku", style=wx.DEFAULT_FRAME_STYLE | wx.VSCROLL | wx.HSCROLL | wx.ALWAYS_SHOW_SB)
        self.app=app
        self.SetMinSize((630,430))
        self.ShowHints=False
        self._initLayout()

    def _initLayout(self):
        self.SetIcon(wx.Icon(self.app.config.get("global","gui.icon"),wx.BITMAP_TYPE_ICO))
        self._loadAccessKeys()
        self._loadHelpTips()
        self._bindEvents()
        self._addStatusBar()
        self._addMenus()
        self._addSizer()
        self._addToolBar()
        self._addSudoku()

    def _loadAccessKeys(self):
        # Put here something that gets the access keys from the system configuration
        # but I currently don't have any clue how to do that, yet...
        self.__accesskeys = {"new":"Ctrl+N","open":"Ctrl+O","open_url":"Ctrl+Shift+O",
                             "save":"Ctrl+S","exit":"Ctrl+Q","solve":"Ctrl+R",
                             "undo":"Ctrl+Z","redo":"Ctrl+Shift+Z","hints":"Ctrl+H",
                             "console":"F12"}

    def _loadHelpTips(self):
        self.__HelpTips = {"new":_("Creates a New Sudoku"),"open":_("Opens a Sudoku"),
                           "open_url":_("Opens a Sudoku from a Web server"),
                           "save":_("Saves a Sudoku"),"exit":_("The application terminates"),
                           "solve":_("Solves the Sudoku (I thought that you were smart!)"),
                           "undo":_("Goes back to the past, well, it undoes your latest mess"),
                           "redo":_("Redoes your latest undo"),
                           "hints":_("It shows you some helpful information"),
                           "lan":_("Changes your app language to %s"),
                           "clan":_("It allows you to change the language"),
                           "help":_("Shows some documentation of how does work this thing"),
                           "update":_("Checks if you are running the latest version"),
                           "about":_("I need to explain what does this thing do?"),
                           "console":_("Opens a Python Interactive console, It's that cool")
                           }

    def _getAKey(self,key):
        """Returns the Access key"""
        if key in self.__accesskeys:
            return "\t" + self.__accesskeys[key]
        return ""

    def _getTip(self,key):
        if key in self.__HelpTips:
            return self.__HelpTips[key]
        return ""

    def _bindEvents(self):
        self.Bind(wx.EVT_CLOSE, self.OnExit)

    def _addStatusBar(self):
        self.StatusBar = wx.StatusBar(self)
        self.StatusBar.SetFieldsCount(1)
        self.SetStatusBar(self.StatusBar)

    def _getMenuArt(self,id):
        isize=(16,16)
        return wx.ArtProvider_GetBitmap(id,wx.ART_MENU,isize)

    def _getToolBarArt(self,id):
        isize=(16,16)
        return wx.ArtProvider_GetBitmap(id,wx.ART_TOOLBAR,isize)

    def _addMenus(self):
        self.MenuBar=wx.MenuBar()
        filemenu=wx.Menu()

        itm=wx.MenuItem(filemenu,wx.ID_ANY,_("&New...") + self._getAKey("new"),self._getTip("new"))
        itm.SetBitmap(self._getMenuArt(wx.ART_NEW))
        self.Bind(wx.EVT_MENU, self.OnNew, itm)
        filemenu.AppendItem(itm)

        itm=wx.MenuItem(filemenu,wx.ID_ANY,_("&Open...")+ self._getAKey("open"),self._getTip("open"))
        itm.SetBitmap(self._getMenuArt(wx.ART_FILE_OPEN))
        self.Bind(wx.EVT_MENU, self.OnOpen, itm)
        filemenu.AppendItem(itm)

        itm=wx.MenuItem(filemenu,wx.ID_ANY,_("&Open URL...")+ self._getAKey("open_url"),self._getTip("open_url"))
        itm.SetBitmap(self._getMenuArt(wx.ART_FILE_OPEN))
        self.Bind(wx.EVT_MENU, self.OnOpenURL, itm)
        filemenu.AppendItem(itm)


        #itm=wx.MenuItem(filemenu,wx.ID_ANY,_("&Save...")+ self._getAKey("save"),self._getTip("save"))
        #itm.SetBitmap(self._getMenuArt(wx.ART_FILE_SAVE))
        #self.Bind(wx.EVT_MENU, self.OnSave, itm)
        #filemenu.AppendItem(itm)
        filemenu.AppendSeparator()

        itm=wx.MenuItem(filemenu,wx.ID_ANY,_("&Exit")+ self._getAKey("exit"),self._getTip("exit"))
        itm.SetBitmap(self._getMenuArt(wx.ART_QUIT))
        self.Bind(wx.EVT_MENU, self.OnExit, itm)
        filemenu.AppendItem(itm)

        self.MenuBar.Append(filemenu,_("&File"))

        #-
        filemenu=wx.Menu()
        itm=wx.MenuItem(filemenu,wx.ID_ANY,_("&Solve")+ self._getAKey("solve"),self._getTip("solve"))
        itm.SetBitmap(self._getMenuArt(wx.ART_TICK_MARK))
        self.Bind(wx.EVT_MENU, self.OnSolve, itm)
        filemenu.AppendItem(itm)
        filemenu.AppendSeparator()

        self.__undo=itm=wx.MenuItem(filemenu,wx.ID_ANY,_("&Undo")+ self._getAKey("undo"),self._getTip("undo"))
        itm.SetBitmap(self._getMenuArt(wx.ART_UNDO))
        self.Bind(wx.EVT_MENU, self.OnUndo, itm)
        filemenu.AppendItem(itm)
        itm.Enable(False)

        self.__redo=itm=wx.MenuItem(filemenu,wx.ID_ANY,_("&Redo")+ self._getAKey("redo"),self._getTip("redo"))
        itm.SetBitmap(self._getMenuArt(wx.ART_REDO))
        self.Bind(wx.EVT_MENU, self.OnRedo, itm)
        filemenu.AppendItem(itm)
        itm.Enable(False)

        self.MenuBar.Append(filemenu,_("&Sudoku"))

        #-
        filemenu=wx.Menu()
        self.__hints=itm=filemenu.AppendCheckItem(wx.ID_ANY,_("&Show Hints")+ self._getAKey("hints"),self._getTip("hints"))
        if self.ShowHints:
            itm.Toggle()
        self.Bind(wx.EVT_MENU, self.OnShowHints, itm)

        submenu=wx.Menu()
        self.__LangList={}
        tmplglist=[]
        for k,l in self.app.GetLanguages().iteritems():
            tmplglist.append((_(l),k))
        tmplglist.sort()
        lc=self.app.GetLanguage()
        for lan,k in tmplglist:
            itm=submenu.AppendRadioItem(wx.ID_ANY,"&"+lan,self._getTip("lan") %(lan,))
            if lc==k:
                itm.Toggle()
            self.__LangList[itm.GetId()]=k
            self.Bind(wx.EVT_MENU, self.OnChangeLanguage, itm)
        
        filemenu.AppendMenu(wx.ID_ANY,_("&Change Language"),submenu,self._getTip("clan"))
        self.MenuBar.Append(filemenu,_("&Options"))

        #-
        filemenu=wx.Menu()
        #itm=wx.MenuItem(filemenu,wx.ID_ANY,_("&Help...")+ self._getAKey("help"),self._getTip("help"))
        #itm.SetBitmap(self._getMenuArt(wx.ART_HELP))
        #self.Bind(wx.EVT_MENU, self.OnHelp, itm)
        #filemenu.AppendItem(itm)
        #filemenu.AppendSeparator()

        #itm=wx.MenuItem(filemenu,wx.ID_ANY,_("&Check for updates...")+ self._getAKey("update"),self._getTip("update"))
        #itm.SetBitmap(self._getMenuArt(wx.ART_HELP))
        #self.Bind(wx.EVT_MENU, self.OnCheckForUpdates, itm)
        #filemenu.AppendItem(itm)
        #filemenu.AppendSeparator()

        itm=wx.MenuItem(filemenu,wx.ID_ANY,_("&Console...")+ self._getAKey("console"),self._getTip("console"))
        #itm.SetBitmap(self._getMenuArt(wx.ART_HELP))
        self.Bind(wx.EVT_MENU, self.OnConsole, itm)
        filemenu.AppendItem(itm)
        filemenu.AppendSeparator()

        itm=wx.MenuItem(filemenu,wx.ID_ANY,_("&About...")+ self._getAKey("about"),self._getTip("about"))
        itm.SetBitmap(self._getMenuArt(wx.ART_INFORMATION))
        self.Bind(wx.EVT_MENU, self.OnAbout, itm)
        filemenu.AppendItem(itm)
        self.MenuBar.Append(filemenu,_("&Help"))

        self.SetMenuBar(self.MenuBar)

    def _addSizer(self):
        self.Sizer=wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.Sizer)

    def _addToolBar(self):
        self.ToolBar=wx.ToolBar(self,style=wx.NO_BORDER|wx.TB_HORIZONTAL|wx.TB_TEXT)
        itm=self.ToolBar.AddSimpleTool(wx.ID_ANY,self._getToolBarArt(wx.ART_NEW),_("New..."),self._getTip("new"))
        self.Bind(wx.EVT_TOOL, self.OnNew, itm)
        itm=self.ToolBar.AddSimpleTool(wx.ID_ANY,self._getToolBarArt(wx.ART_FILE_OPEN),_("Open..."),self._getTip("open"))
        self.Bind(wx.EVT_TOOL, self.OnOpen, itm)
        #itm=self.ToolBar.AddSimpleTool(wx.ID_ANY,self._getToolBarArt(wx.ART_FILE_SAVE),_("Save..."),self._getTip("save"))
        #self.Bind(wx.EVT_TOOL, self.OnSave, itm)
        self.ToolBar.AddSeparator()
        itm=self.ToolBar.AddSimpleTool(wx.ID_ANY,self._getToolBarArt(wx.ART_TICK_MARK),_("Solve"),self._getTip("solve"))
        self.Bind(wx.EVT_TOOL, self.OnSolve, itm)
        self.ToolBar.AddSeparator()
        itm=self.ToolBar.AddSimpleTool(wx.ID_ANY,self._getToolBarArt(wx.ART_UNDO),_("Undo"),self._getTip("undo"))
        self.__undobtid=itm.GetId()
        self.ToolBar.EnableTool(itm.GetId(),False)
        self.Bind(wx.EVT_TOOL, self.OnUndo, itm)
        itm=self.ToolBar.AddSimpleTool(wx.ID_ANY,self._getToolBarArt(wx.ART_REDO),_("Redo"),self._getTip("redo"))
        self.__redobtid=itm.GetId()
        self.ToolBar.EnableTool(itm.GetId(),False)
        self.Bind(wx.EVT_TOOL, self.OnRedo, itm)
        self.ToolBar.AddSeparator()
        itm=self.ToolBar.AddCheckTool(wx.ID_ANY,self._getToolBarArt(wx.ART_INFORMATION),shortHelp=_("Show Hints"),longHelp=self._getTip("hints"))
        self.__hintsbtid=itm.GetId()
        self.ToolBar.ToggleTool(self.__hintsbtid,self.ShowHints)
        self.Bind(wx.EVT_TOOL, self.OnShowHints, itm)
        self.ToolBar.Realize()
        self.Sizer.Remove(0)
        self.Sizer.Insert(0,self.ToolBar,flag=wx.EXPAND)

    def _addSudoku(self):
        if 1:
            self.SudokuGrid=SudokuGridPanel(self)
            self.Sizer.Insert(1,self.SudokuGrid,1,wx.EXPAND)
        else:
            panel=wx.ScrolledWindow(self)
            #panel.AdjustScrollbars()
            panel.SetScrollbars(10,10,10,10)
            panel.SetBackgroundColour((0,100,0))
            self.Sizer.Insert(1,panel,1,wx.EXPAND)
            sizer=wx.GridSizer()
            panel.SetSizer(sizer)
            self.SudokuGrid=SudokuGridPanel(panel)
            sizer.Add(self.SudokuGrid,0,wx.ALIGN_CENTER | wx.ALIGN_CENTER_VERTICAL)

    def EnableUndo(self,enabled=True):
        self.__undo.Enable(enabled)
        self.ToolBar.EnableTool(self.__undobtid,enabled)

    def EnableRedo(self,enabled=True):
        self.__redo.Enable(enabled)
        self.ToolBar.EnableTool(self.__redobtid,enabled)

    def OnExit(self,evt):
        if type(evt)!=wx.CloseEvent or evt.CanVeto():
            ans=wx.MessageBox(_("Are you really sure that you wish to quit?"),_("Are you sure?"),wx.YES_NO)
            if ans!=wx.YES:
                if type(evt)==wx.CloseEvent:
                    evt.Veto()
                return
        self.Destroy()

    def OnNew(self,evt):
        print "new"
        self.SudokuGrid.Reset()

    def OnOpen(self,evt):
        print "open"
        dlg=wx.FileDialog(self,wildcard="".join((
            _("GPE files")," (*.gpe)|*.gpe|",
            _("TSudoku files")," (*.tsdk)|*.tsdk|",
            _("All Files"), "|*"
            )),style=wx.OPEN)
        if dlg.ShowModal()==wx.ID_OK:
            try:
                grid=Sudoku.Grid()
                grid.load_from_file(dlg.GetDirectory() + "/" + dlg.GetFilename())
                self.SudokuGrid._ModelGrid.copy_values_from(grid)
            except Sudoku.Contradition:
                wx.MessageBox(_("Invalid sudoku file"),_("Invalid sudoku file"),
                              style=wx.ICON_INFORMATION)
        dlg.Destroy()

    def OnOpenURL(self,evt):
        print "open url"
        dlg=wx.TextEntryDialog(self,_("Enter the URL"),
                               defaultValue="http://sudoku.udl.es/Problems/Easy-4-1.gpe")
        if dlg.ShowModal() == wx.ID_OK:
            import urllib2 as urllib
            try:
                f=urllib.urlopen(dlg.GetValue())
                grid=Sudoku.Grid()
                grid.load_from_stream(f)
                self.SudokuGrid._ModelGrid.copy_values_from(grid)
            except Sudoku.Contradition:
                wx.MessageBox(_("Invalid sudoku file"),_("Invalid sudoku file"),
                              style=wx.ICON_INFORMATION)
            except:
                pass
            f.close()

        dlg.Destroy()
        

    def OnSolve(self,evt):
        print "solve"
        if not self.SudokuGrid.Solve():
            wx.MessageBox(_("No solution has been found."),style=wx.ICON_INFORMATION)

    def OnUndo(self,evt):
        print "undo"
        self.SudokuGrid.Undo()

    def OnRedo(self,evt):
        print "redo"
        self.SudokuGrid.Redo()

    def OnShowHints(self,evt):
        self.ShowHints = not self.ShowHints
        if evt.GetId()==self.__hintsbtid:
            self.__hints.Toggle()
        else:
            self.ToolBar.ToggleTool(self.__hintsbtid,self.ShowHints)
        assert((evt.Checked() and self.ShowHints) or not(evt.Checked() and self.ShowHints))
        self.SudokuGrid.ShowHints(self.ShowHints)
        if evt.Checked():
            print "showhints enabled"
        else:
            print "showhints dissabled"

    def OnChangeLanguage(self,evt):
        print "Change language", self.__LangList[evt.GetId()]
        self.app.SetLanguage(self.__LangList[evt.GetId()])
        self._loadHelpTips()
        self._addMenus()
        self._addToolBar()

    def OnAbout(self,evt):
        wx.MessageBox(_(u"""
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

""") %("$Id$",),_("About %s") %("Al's WxWidgets Python Sudoku",),wx.OK)

    def OnConsole(self,evt):
        try:
            self.shellframe.Close()
            self.shellframe=None
        except: # wx.PyDeadObjectError:
            try:
                print "Launching Shell..."
                from wx import py
                self.shellframe=py.crust.CrustFrame()
                self.shellframe.Show()
                self.shellframe.shell.interp.locals['app']=self.app
            except Exception, detail:
                print "Failed launching shell, reason %s" %(detail,)
        

class SudokuApp(wx.App):
    """main wxApp"""

    def __init__(self,config="wxSudoku.cfg"):
        self.__configFile=config
        self.config=None
        wx.App.__init__(self,redirect=False)

    def _loadConfig(self,cfg=None):
        """Load App configuration"""
        import ConfigParser
        if cfg==None:
            cfg=self.__configFile
        self.config=ConfigParser.SafeConfigParser()
        self.config.add_section("global")
        self.config.set("global","gui.icon","favicon.ico")
        self.config.set("global","app.gettext.locales","locales")
        self.config.set("global","app.gettext.domain","alssudoku")
        if cfg!=None:
            self.config.read(cfg)

    def _saveConfig(self,cfg=None):
        """Save App configuration"""
        if cfg==None:
            cfg=self.__configFile
        fo=file(cfg,"w")
        self.config.write(fo)
        fo.close()

    def _getcfg(self,section,key):
        try:
            return self.config.get(section,key)
        except ConfigParser.NoOptionError:
            return None

    def _installGettext(self,lang=None):
        if lang==None:
            gettext.install(self._getcfg("global","app.gettext.domain"),
                            self._getcfg("global","app.gettext.locales"),True)
        else:
            gettext.translation(self._getcfg("global","app.gettext.domain"),
                                self._getcfg("global","app.gettext.locales"),(lang,)).install(True)

    def _showMainFrame(self):
        self.mainFrame=SudokuMainFrame(self)
        self.SetTopWindow(self.mainFrame)
        self.mainFrame.Show(True)

    def GetLanguages(self):
        try:
            return self.__Languages
        except:
            import dircache
            self.__Languages={}
            # Dirty hardcoded ugly LangDict
            _ = lambda x : x
            LangDict={"en":_("English"),"es":_("Spanish"),"ca":_("Catalan")}
            for lan in dircache.listdir(self._getcfg("global","app.locales")):
                if lan in LangDict:
                    self.__Languages[lan]=LangDict[lan]
                else:
                    self.__Languages[lan]=lan
            return self.__Languages

    def SetLanguage(self,lang):
        #import locale
        #locale.setlocale(locale.LC_ALL, (lang,"utf-8"))
        self.__Language=lang
        self._installGettext(lang)

    def GetLanguage(self):
        try:
            return self.__Language
        except:
            import locale
            self.__Language=locale.getdefaultlocale()[0][:2]
            return self.__Language

    def OnInit(self):
        self._loadConfig()
        self._installGettext()
        self._showMainFrame()
        return True

    def OnExit(self):
        self._saveConfig()


if __name__ == "__main__":
    # open log
    redirect = True
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
    except:
        import traceback
        trace=file("traceback.log","w")
        traceback.print_exc(file=trace)
        trace.close()
        traceback.print_exc(file=sys.stderr)
        wx.MessageBox(traceback.format_exc(),"Traceback",wx.ICON_ERROR)
    # close log
    if redirect:
        sys.stdout=old_stdout
        sys.stderr=old_stderr
        log.close()
        logerr.close()
