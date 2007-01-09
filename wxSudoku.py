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


class SudokuMainFrame(wx.Frame):
    """Sudoku Main Frame"""
    def __init__(self,app,parent=None):
        wx.Frame.__init__(self, parent, -1, _("Al's WxWidgets Python Sudoku"))
        self.app=app
        self.SetMinSize((630,430))
        self._initLayout()
    def _initLayout(self):
        # Set Icon
        self.SetIcon(wx.Icon(self.app.config.get("global","gui.icon"),wx.BITMAP_TYPE_ICO))

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
    def _showMainFrame(self):
        self.mainFrame=SudokuMainFrame(self)
        self.SetTopWindow(self.mainFrame)
        self.mainFrame.Show(True)
    def OnInit(self):
        self._loadConfig()
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
