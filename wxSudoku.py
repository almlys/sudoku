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

import wx
import gettext

class SudokuMainFrame(wx.Frame):
    """Sudoku Main Frame"""
    def __init__(self,app,parent=None):
        wx.Frame.__init__(self, parent, title="Al's WxWidgets Python Sudoku")
        self.app=app
        self.SetMinSize((630,430))
        self._initLayout()
    def _initLayout(self):
        self.SetIcon(wx.Icon(self.app.config.get("global","gui.icon"),wx.BITMAP_TYPE_ICO))
        self._loadAccessKeys()
        self._bindEvents()
        self._addStatusBar()
        self._addMenus()
        self._addToolBar()
    def _loadAccessKeys(self):
        # Put here something that gets the access keys from the system configuration
        # but I currently don't have any clue how to do that, yet...
        self._accesskeys = {"new":"Ctrl+N","open":"Ctrl+O","save":"Ctrl+S",
                            "exit":"Ctrl+Q","solve":"Ctrl+R","undo":"Ctrl+Z",
                            "redo":"Ctrl+Shift+Z","hints":"Ctrl+H"}
    def _getAKey(self,key):
        """Returns the Access key"""
        if key in self._accesskeys:
            return "\t" + self._accesskeys[key]
        return ""
    def _bindEvents(self):
        self.Bind(wx.EVT_CLOSE, self.OnExit)
        #self.Bind(wx.EVT_KEY, self.OnKey)
    def _addStatusBar(self):
        self.StatusBar = wx.StatusBar(self)
        self.StatusBar.SetFieldsCount(1)
        self.SetStatusBar(self.StatusBar)
    def _addMenus(self):
        isize=(16,16)
        self.MenuBar=wx.MenuBar()
        filemenu=wx.Menu()

        itm=wx.MenuItem(filemenu,wx.ID_ANY,_("&New...") + self._getAKey("new"),_("Creates a New Sudoku"))
        itm.SetBitmap(wx.ArtProvider_GetBitmap(wx.ART_NEW,wx.ART_MENU,isize))
        self.Bind(wx.EVT_MENU, self.OnNew, itm)
        filemenu.AppendItem(itm)

        itm=wx.MenuItem(filemenu,wx.ID_ANY,_("&Open...")+ self._getAKey("open"),_("Opens a Sudoku"))
        itm.SetBitmap(wx.ArtProvider_GetBitmap(wx.ART_FILE_OPEN,wx.ART_MENU,isize))
        self.Bind(wx.EVT_MENU, self.OnOpen, itm)
        filemenu.AppendItem(itm)

        itm=wx.MenuItem(filemenu,wx.ID_ANY,_("&Save...")+ self._getAKey("save"),_("Saves a Sudoku"))
        itm.SetBitmap(wx.ArtProvider_GetBitmap(wx.ART_FILE_SAVE,wx.ART_MENU,isize))
        #self.Bind(wx.EVT_MENU, self.OnSave, itm)
        filemenu.AppendItem(itm)
        filemenu.AppendSeparator()

        itm=wx.MenuItem(filemenu,wx.ID_ANY,_("&Exit")+ self._getAKey("exit"),_("The application terminates"))
        itm.SetBitmap(wx.ArtProvider_GetBitmap(wx.ART_QUIT,wx.ART_MENU,isize))
        self.Bind(wx.EVT_MENU, self.OnExit, itm)
        filemenu.AppendItem(itm)

        self.MenuBar.Append(filemenu,_("&File"))

        #-
        filemenu=wx.Menu()
        itm=wx.MenuItem(filemenu,wx.ID_ANY,_("&Solve")+ self._getAKey("solve"),_("Solves the Sudoku (I thought that you were smart!)"))
        itm.SetBitmap(wx.ArtProvider_GetBitmap(wx.ART_TICK_MARK,wx.ART_MENU,isize))
        self.Bind(wx.EVT_MENU, self.OnSolve, itm)
        filemenu.AppendItem(itm)
        filemenu.AppendSeparator()

        self.__undo=itm=wx.MenuItem(filemenu,wx.ID_ANY,_("&Undo")+ self._getAKey("undo"),_("Goes back to the past, well, it undoes your latest mess"))
        itm.SetBitmap(wx.ArtProvider_GetBitmap(wx.ART_UNDO,wx.ART_MENU,isize))
        self.Bind(wx.EVT_MENU, self.OnUndo, itm)
        filemenu.AppendItem(itm)
        itm.Enable(False)

        self.__redo=itm=wx.MenuItem(filemenu,wx.ID_ANY,_("&Redo")+ self._getAKey("redo"),_("Redoes your latest undo"))
        itm.SetBitmap(wx.ArtProvider_GetBitmap(wx.ART_REDO,wx.ART_MENU,isize))
        self.Bind(wx.EVT_MENU, self.OnRedo, itm)
        filemenu.AppendItem(itm)
        itm.Enable(False)

        self.MenuBar.Append(filemenu,_("&Sudoku"))

        #-
        filemenu=wx.Menu()
        itm=filemenu.AppendCheckItem(wx.ID_ANY,_("&Show Hints")+ self._getAKey("hints"),_("It shows you some helpful information"))
        self.Bind(wx.EVT_MENU, self.OnShowHints, itm)

        submenu=wx.Menu()
        self.__LangList={}
        tmplglist=[]
        for k,l in self.app.GetLanguages().iteritems():
            tmplglist.append((_(l),k))
        tmplglist.sort()
        lc=self.app.GetLanguage()
        for lan,k in tmplglist:
            itm=submenu.AppendRadioItem(wx.ID_ANY,lan,_("Changes your app language to %s") %(lan,))
            if lc==k:
                itm.Toggle()
            self.__LangList[itm.GetId()]=k
            self.Bind(wx.EVT_MENU, self.OnChangeLanguage, itm)
        
        filemenu.AppendMenu(wx.ID_ANY,_("&Change Language"),submenu,_("It allows you to change the language"))
        self.MenuBar.Append(filemenu,_("&Options"))

        #-
        filemenu=wx.Menu()
        itm=wx.MenuItem(filemenu,wx.ID_ANY,_("&Help...")+ self._getAKey("help"),_("Shows some documentation of how does work this thing"))
        itm.SetBitmap(wx.ArtProvider_GetBitmap(wx.ART_HELP,wx.ART_MENU,isize))
        #self.Bind(wx.EVT_MENU, self.OnHelp, itm)
        filemenu.AppendItem(itm)
        filemenu.AppendSeparator()

        itm=wx.MenuItem(filemenu,wx.ID_ANY,_("&Check for updates...")+ self._getAKey("update"),_("Checks if you are running the latest version"))
        #itm.SetBitmap(wx.ArtProvider_GetBitmap(wx.ART_HELP,wx.ART_MENU,isize))
        #self.Bind(wx.EVT_MENU, self.OnCheckForUpdates, itm)
        filemenu.AppendItem(itm)
        filemenu.AppendSeparator()

        itm=wx.MenuItem(filemenu,wx.ID_ANY,_("&About...")+ self._getAKey("help"),_("I need to explain what does this thing do?"))
        itm.SetBitmap(wx.ArtProvider_GetBitmap(wx.ART_INFORMATION,wx.ART_MENU,isize))
        self.Bind(wx.EVT_MENU, self.OnAbout, itm)
        filemenu.AppendItem(itm)
        self.MenuBar.Append(filemenu,_("&Help"))

        self.SetMenuBar(self.MenuBar)
    def _addToolBar(self):
        pass
    def EnableUndo(self,enabled=True):
        self.__undo.Enable(enabled)
    def EnableRedo(self,enabled=True):
        self.__redo.Enable(enabled)
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
    def OnOpen(self,evt):
        print "open"
    def OnSolve(self,evt):
        print "solve"
    def OnUndo(self,evt):
        print "undo"
    def OnRedo(self,evt):
        print "redo"
    def OnShowHints(self,evt):
        if evt.Checked():
            print "showhints enabled"
        else:
            print "showhints dissabled"
    def OnChangeLanguage(self,evt):
        print "Change language", self.__LangList[evt.GetId()]
        self.app.SetLanguage(self.__LangList[evt.GetId()])
        self._addMenus()
        self._addToolBar()
    def OnKey(self,evt):
        print evt
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
        self.config.set("global","app.locales","locales")
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
            gettext.install("awxpysudoku",self._getcfg("global","app.locales"),True)
        else:
            gettext.translation("awxpysudoku",self._getcfg("global","app.locales"),(lang,)).install(True)
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
    import sys,logging
    if redirect:
        log = logging.mlog(sys.stdout,"stdout.log","w")
        logerr = logging.mlog(sys.stderr,"stderr.log","w")
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
