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

import SudokuCommon
import Sudoku
import observer

try:
    import wx
except ImportError:
    # Show a localized Import error
    a=SudokuCommon.SudokuBaseApplication()
    a._installGettext()
    print _("""
WxPython 2.6 or higher is required to run this application!!!

You can get it from http://www.wxpython.org

Or you can just type as root "apt-get install python-wxgtk2.6" on Debian, Ubuntu and any other Debian based distros
On other distros you may try similar commands, yum, urpmi, emerge,..., just check your Distro documentation
but if you don't have root access you will need to manually install wxPython in your home directory, have fun!\n""")
    #import webbrowser
    #webbrowser.open_new("http://www.wxpython.org")
    import sys
    sys.exit(-1)

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
        self._sizer=wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self._sizer)
        self.HintsLabel=wx.StaticText(self,style=wx.ALIGN_CENTER)
        self.HintsLabel.SetLabel("123456789")
        self.HintsLabel.SetFont(wx.FFont(8,wx.FONTFAMILY_DEFAULT,face="Arial"))
        self._sizer.Add(self.HintsLabel,0,flag=wx.ALIGN_CENTER)
        self.TextBox=wx.TextCtrl(self,style=wx.TE_PROCESS_ENTER | wx.NO_BORDER | wx.TE_CENTRE)
        self.TextBox.SetFont(wx.FFont(16,wx.FONTFAMILY_DEFAULT,face="Arial",flags=wx.FONTFLAG_BOLD))
        self.TextBox.SetBackgroundColour(self.GetBackgroundColour())
        self.TextBox.Bind(wx.EVT_KEY_DOWN,self.OnKey)
        self.TextBox.Bind(wx.EVT_TEXT_ENTER,self.OnChange)
        self.TextBox.Bind(wx.EVT_KILL_FOCUS,self.OnChange)
        self._sizer.Add(self.TextBox,1,flag=wx.ALIGN_CENTER | wx.EXPAND)

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
        self._sizer.Layout()

    def OnKey(self,evt):
        #print evt
        code=evt.GetKeyCode()
        r,c = self.row, self.col
        grid = self.getSubject()._grid
        if code==wx.WXK_UP:
            r = (r-1) % grid.getTotalNumRows()
        elif code==wx.WXK_DOWN:
            r = (r+1) % grid.getTotalNumRows()
        elif code==wx.WXK_RIGHT:
            c = (c+1) % grid.getTotalNumCols()
        elif code==wx.WXK_LEFT:
            c = (c-1) % grid.getTotalNumCols()
        else:
            evt.Skip()
        self.parent.SetFocus(grid.rc2i(r,c))

    def OnChange(self,evt):
        """The entry has changed so we must notify the model."""
        mcell = self.getSubject()
        old_value = mcell._value
        try:
            new_value = int(self.TextBox.GetValue())
        except ValueError:
            new_value = 0
        if new_value == 0:
            self.TextBox.SetValue("")
        if new_value == old_value:
            return

        if old_value!=0:
            mcell._grid.unset(mcell._index)
        if new_value!=0:
            try:
                mcell._grid.set(mcell._index, new_value)
            except Sudoku.Contradiction:
                mcell._grid.unset(mcell._index)
                #self.TextBox.SetValue("")
                new_value=0

        if new_value!=old_value:
            self.parent.parent._history_callback("s",mcell._index,old_value,new_value)

    def SetFocus(self):
        self.TextBox.SetFocus()


class SudokuGridPanel(wx.Panel):
    """Represents the 9x9 grid formed by 3x3 Tboxes"""

    def __init__(self, appparent, parentpanel=None, type=None, *args, **kwargs):
        if parentpanel==None:
            parentpanel=appparent
        wx.Panel.__init__(self,parentpanel,*args,**kwargs)
        self.parent=appparent
        self.SetBackgroundColour((48,7,11))
        self._ShowHints=False
        if type==None:
            type=Sudoku.NormalSudoku(3,3,3,3)
        self._type=type
        self.sbr=type.sbr
        self.sbc=type.sbc
        self.r=type.r
        self.c=type.c
        self._initLayout()
        self._create_model()
        self._connect()

    def _initLayout(self):
        self._addGrid()

    def _addGrid(self):
        self._ViewCells=[None for a in xrange(self.r*self.c*self.sbc*self.sbr)]
        self._GridSizer=wx.GridSizer(self.r,self.c)
        self.SetSizer(self._GridSizer)
        samurai = isinstance(self._type,Sudoku.SamuraiSudoku)
        if samurai:
            vhole=(self.c - 1) / 2
            hhole=(self.r - 1) / 2
        for r in xrange(self.r):
            for c in xrange(self.c):
                flag=wx.ALL | wx.EXPAND
                ci=r*self.r + c
                if self.c % 2 == 0 and r % 2:
                    ci+=1
                bgcolor = ((0xCB,0x83,0xAC),(0xCB,0x9E,0xAC))[ci % 2]
                if samurai and ((c==vhole and (r<hhole-1 or r>hhole+1)) or (r==hhole and (c<vhole-1 or c>vhole+1))):
                    self._GridSizer.AddSpacer((0,0))
                else:
                    cgrid=wx.GridSizer(self.sbr,self.sbc)
                    self._GridSizer.Add(cgrid,1,border=1,flag=flag)
                    for br in xrange(self.sbr):
                        for bc in xrange(self.sbc):
                            itm=CellPanel(self,(r*self.sbr + br,c*self.sbc + bc),bgcolor)
                            cgrid.Add(itm,1,border=1,flag=wx.ALL | wx.EXPAND)
                            self._ViewCells[(r*self.sbr + br) * self.sbc * self.c + c*self.sbc + bc]=itm

    def _create_model(self):
        self._ModelGrid=SudokuCommon.MyGrid(self._type)

    def _connect(self):
        for idx in xrange(len(self._ModelGrid)):
            wcell = self._ViewCells[idx]
            if wcell==None: continue
            mcell = self._ModelGrid._cells[idx]
            mcell.attach(wcell)
            mcell.notify()

    def ShowHints(self,show):
        self._ShowHints=show
        self.Update()

    def Update(self):
        for lala in self._ViewCells:
            if lala!=None:
                lala.update()

    def Reset(self):
        self._ModelGrid.reset()

    def SetFocus(self,idx):
        if self._ViewCells[idx]!=None:
            self._ViewCells[idx].SetFocus()


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
        self._addHistory()
        self._addStatusBar()
        self._addMenus()
        self._addSizer()
        self._addToolBar()
        self._addSudoku(Sudoku.NormalSudoku(3,3,3,3))

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

    def _addHistory(self):
        self.History=SudokuCommon.History()

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
        if self.History.isEmpty():
            itm.Enable(False)

        self.__redo=itm=wx.MenuItem(filemenu,wx.ID_ANY,_("&Redo")+ self._getAKey("redo"),self._getTip("redo"))
        itm.SetBitmap(self._getMenuArt(wx.ART_REDO))
        self.Bind(wx.EVT_MENU, self.OnRedo, itm)
        filemenu.AppendItem(itm)
        if self.History.isRedoEmpty():
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
        if self.History.isEmpty():
            self.ToolBar.EnableTool(itm.GetId(),False)
        self.Bind(wx.EVT_TOOL, self.OnUndo, itm)
        itm=self.ToolBar.AddSimpleTool(wx.ID_ANY,self._getToolBarArt(wx.ART_REDO),_("Redo"),self._getTip("redo"))
        self.__redobtid=itm.GetId()
        if self.History.isRedoEmpty():
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

    def _addSudoku(self,type=None):
        self.Freeze()
        try:
            self.SudokuGrid.Destroy()
            self._scrollpanel.Destroy()
        except AttributeError:
            pass
        self.Sizer.Remove(1)
        # Documentation says that Remove destroys the item, BUT it is not DESTROYED!!!!!!!, it is only detached!!
        if 1:
            self.SudokuGrid=SudokuGridPanel(self,type=type)
            self.Sizer.Insert(1,self.SudokuGrid,1,wx.EXPAND)
        else:
            self._scrollpanel=wx.ScrolledWindow(self)
            #panel.AdjustScrollbars()
            self._scrollpanel.SetScrollbars(10,10,10,10)
            self._scrollpanel.SetBackgroundColour((0,100,0))
            self.Sizer.Insert(1,self._scrollpanel,1,wx.EXPAND)
            sizer=wx.GridSizer()
            self._scrollpanel.SetSizer(sizer)
            self.SudokuGrid=SudokuGridPanel(self,self._scrollpanel,type)
            sizer.Add(self.SudokuGrid,0,wx.ALIGN_CENTER | wx.ALIGN_CENTER_VERTICAL)
        self.SudokuGrid.ShowHints(self.ShowHints)
        self.Thaw()

    # History

    def EnableUndo(self,enabled=True):
        self.__undo.Enable(enabled)
        self.ToolBar.EnableTool(self.__undobtid,enabled)

    def EnableRedo(self,enabled=True):
        self.__redo.Enable(enabled)
        self.ToolBar.EnableTool(self.__redobtid,enabled)

    def _history_callback(self,*args):
        self.EnableUndo(True)
        self.EnableRedo(False)
        self.History.Stack(args)

    # Actions

    def OnExit(self,evt):
        if type(evt)!=wx.CloseEvent or evt.CanVeto():
            ans=wx.MessageBox(_("Are you really sure that you wish to quit?"),
                              _("Are you sure?"),wx.YES_NO,self)
            if ans!=wx.YES:
                if type(evt)==wx.CloseEvent:
                    evt.Veto()
                return
        self.Destroy()

    def OnNew(self,evt):
        #self.SudokuGrid.Reset()
        import wxNewSudokuDialog
        dlg=wxNewSudokuDialog.NewSudokuDialog(self)
        dlg.ShowModal()
        if dlg.OkStatus:
            bkgrid = Sudoku.Grid(self.SudokuGrid._ModelGrid)
            bkgrid.copy_values_from(self.SudokuGrid._ModelGrid)
            type=dlg.type.GetValue()
            sbr=int(dlg.brows.GetValue())
            sbc=int(dlg.bcols.GetValue())
            c=sbr
            r=sbc
            if type==_("Samurai"):
                su=Sudoku.SamuraiSudoku(r,c,sbr,sbc)
            else:
                su=Sudoku.NormalSudoku(r,c,sbr,sbc)
            self.SetStatusText(_("Creating Sudoku, please wait...."))
            self.app.Yield()
            if su!=bkgrid._type:
                self._addSudoku(su)
            else:
                self.SudokuGrid.Reset()
            emptygrid = Sudoku.Grid(su)
            if bkgrid!=emptygrid:
                self._history_callback("t",bkgrid,emptygrid)

            self.SetStatusText("")
        dlg.Destroy()

    def OnOpen(self,evt):
        dlg=wx.FileDialog(self,wildcard="".join((
            _("GPE files")," (*.gpe)|*.gpe|",
            _("TSudoku files")," (*.tsdk)|*.tsdk|",
            _("All Files"), "|*"
            )),style=wx.OPEN)
        if dlg.ShowModal()==wx.ID_OK:
            filep=dlg.GetDirectory() + "/" + dlg.GetFilename()
            self.SetStatusText(_("Opening %s, please wait...") % (filep,))
            self.app.Yield()
            try:
                bkgrid = Sudoku.Grid(self.SudokuGrid._ModelGrid)
                bkgrid.copy_values_from(self.SudokuGrid._ModelGrid)
                grid=Sudoku.Grid() #TODO we must scan de file and get the Sudoku Type
                grid.load_from_file(filep)
                if grid._type!=bkgrid._type:
                    self._addSudoku(grid._type)
                self.SudokuGrid._ModelGrid.copy_values_from(grid)
                if bkgrid!=grid:
                    self._history_callback("t",bkgrid,grid)
            except Sudoku.Contradiction:
                wx.MessageBox(_("Invalid sudoku file"),_("Invalid sudoku file"),
                              style=wx.ICON_INFORMATION,parent=self)
            except Exception,detail:
                wx.MessageBox(_("Malformed, unconsistent, or unexistent file.\n%s") %(detail,),
                              _("Invalid sudoku file"),
                              style=wx.ICON_ERROR,parent=self)
        dlg.Destroy()
        self.SetStatusText("")

    def OnOpenURL(self,evt):
        dlg=wx.TextEntryDialog(self,_("Enter the URL"),_("Enter the URL"),
                               defaultValue="http://sudoku.udl.es/Problems/Easy-4-1.gpe")
        if dlg.ShowModal() == wx.ID_OK:
            self.SetStatusText(_("Opening %s, please wait...") % (dlg.GetValue(),))
            self.app.Yield()
            import urllib2 as urllib
            try:
                f=urllib.urlopen(dlg.GetValue())
                bkgrid = Sudoku.Grid(self.SudokuGrid._ModelGrid)
                bkgrid.copy_values_from(self.SudokuGrid._ModelGrid)
                grid=Sudoku.Grid() #TODO we must scan de file and get the Sudoku Type
                if dlg.GetValue().lower().endswith(".gpe"):
                    ftype="gpe"
                else:
                    ftype="tsdk"
                grid.load_from_stream(f,ftype)
                if grid._type!=bkgrid._type:
                    self._addSudoku(grid._type)
                self.SudokuGrid._ModelGrid.copy_values_from(grid)
                if bkgrid!=grid:
                    self._history_callback("t",bkgrid,grid)
                f.close()
            except Sudoku.Contradiction:
                f.close()
                wx.MessageBox(_("Invalid sudoku file"),_("Invalid sudoku file"),
                              style=wx.ICON_INFORMATION,parent=self)
            except urllib.HTTPError,detail:
                wx.MessageBox(_("The server said:\n%s\nRequesting the %s resource") %(detail,dlg.GetValue()),
                              _("Remote server error"),
                              style=wx.ICON_INFORMATION,parent=self)
            except (urllib.URLError,ValueError),detail:
                wx.MessageBox(_("Cannot open %s, reason %s") %(dlg.GetValue(),detail),parent=self)
            except Exception,detail:
                wx.MessageBox(_("Malformed, unconsistent, or unexistent file.\n%s") %(detail,),
                              _("Invalid sudoku file"),
                              style=wx.ICON_ERROR,parent=self)
        dlg.Destroy()
        self.SetStatusText("")
        

    def OnSolve(self,evt):
        self.SetStatusText(_("Solving Sudoku, please wait...."))
        self.app.Yield()

        try:
            grid = Sudoku.Grid(self.SudokuGrid._ModelGrid)
            grid.copy_values_from(self.SudokuGrid._ModelGrid)
            solution = Sudoku.solve(grid)
        except Sudoku.Contradiction:
            solution = None
        if solution is None:
            wx.MessageBox(_("No solution has been found."),style=wx.ICON_INFORMATION,parent=self)
        else:
            bkgrid = Sudoku.Grid(self.SudokuGrid._ModelGrid)
            bkgrid.copy_values_from(self.SudokuGrid._ModelGrid)
            self.SudokuGrid._ModelGrid.copy_values_from(solution)
            if bkgrid!=solution:
                self._history_callback("t",bkgrid,solution)

        self.SetStatusText("")

    def Reset(self):
        self.History.Clear()
        self.parent.EnableRedo(False)
        self.parent.EnableUndo(False)
        self.SudokuGrid._ModelGrid.reset()

    def OnUndo(self,evt):
        self.EnableRedo(True)
        hist = self.History.Undo()
        if self.History.isEmpty():
            self.EnableUndo(False)
        cmd = hist[0]
        if cmd=="s":
            # Single value was stacked
            idx, old, new = hist[1:]
            self.SudokuGrid._ModelGrid.unset(idx)
            if old!=0:
                self.SudokuGrid._ModelGrid.set(idx,old)
        elif cmd=="t":
            # An entire Sudoku was stacked
            old, new = hist[1:]
            if old._type!=new._type:
                self.SetStatusText(_("Creating Sudoku, please wait...."))
                self.app.Yield()
                self._addSudoku(old._type)
                self.SetStatusText("")
            self.SudokuGrid._ModelGrid.copy_values_from(old)
        else:
            raise NotImplemented


    def OnRedo(self,evt):
        self.EnableUndo(True)
        hist = self.History.Redo()
        if self.History.isRedoEmpty():
            self.EnableRedo(False)
        cmd = hist[0]
        if cmd=="s":
            idx, old, new = hist[1:]
            self.SudokuGrid._ModelGrid.unset(idx)
            if new!=0:
                self.SudokuGrid._ModelGrid.set(idx,new)
        elif cmd=="t":
            old, new = hist[1:]
            if old._type!=new._type:
                self.SetStatusText(_("Creating Sudoku, please wait...."))
                self.app.Yield()
                self._addSudoku(new._type)
                self.SetStatusText("")
            self.SudokuGrid._ModelGrid.copy_values_from(new)
        else:
            raise NotImplemented

    def OnShowHints(self,evt):
        self.ShowHints = not self.ShowHints
        if evt.GetId()==self.__hintsbtid:
            self.__hints.Toggle()
        else:
            self.ToolBar.ToggleTool(self.__hintsbtid,self.ShowHints)
        assert((evt.Checked() and self.ShowHints) or not(evt.Checked() and self.ShowHints))
        self.SudokuGrid.ShowHints(self.ShowHints)

    def OnChangeLanguage(self,evt):
        self.app.SetLanguage(self.__LangList[evt.GetId()])
        self._loadHelpTips()
        self._addMenus()
        self._addToolBar()

    def OnAbout(self,evt):
        m,t = self.app.GetAboutMessage()
        wx.MessageBox(m,t,wx.OK,self)

    def OnConsole(self,evt):
        try:
            self.shellframe.Close()
            self.shellframe=None
        except: # wx.PyDeadObjectError:
            try:
                print _("Launching Shell...")
                from wx import py
                self.shellframe=py.crust.CrustFrame()
                self.shellframe.Show()
                self.shellframe.shell.interp.locals['app']=self.app
            except Exception, detail:
                print _("Failed launching shell, reason %s") %(detail,)


class SudokuApp(wx.App,SudokuCommon.SudokuBaseApplication):
    """main wxApp"""

    def __init__(self,config="alsSudoku.cfg"):
        SudokuCommon.SudokuBaseApplication.__init__(self,config)
        wx.App.__init__(self,redirect=False)

    def _setConfigDefaults(self):
        """Set App default configuration"""
        SudokuCommon.SudokuBaseApplication._setConfigDefaults(self)
        self.config.set("global","gui.icon","favicon.ico")

    def GetAppVersion(self):
        return "$Id$"

    def _showMainFrame(self):
        self.mainFrame=SudokuMainFrame(self)
        self.SetTopWindow(self.mainFrame)
        self.mainFrame.Show(True)

    def OnInit(self):
        self._loadConfig()
        self._installGettext()
        self._showMainFrame()
        return True

    def OnExit(self):
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
    except:
        import traceback
        trace=file("traceback.log","w")
        traceback.print_exc(file=trace)
        trace.close()
        traceback.print_exc(file=sys.stderr)
        try:
            wx.MessageBox(traceback.format_exc(),"Traceback",wx.ICON_ERROR)
        except:
            pass
    # close log
    if redirect:
        sys.stdout=old_stdout
        sys.stderr=old_stderr
        log.close()
        logerr.close()
