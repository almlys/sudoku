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
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#    Please see the file COPYING for the full license.
#    Please see the file DISCLAIMER for more details, before doing nothing.
#

import xml.parsers.expat as xmlp

class pnode(object):
    """Implements a node from the XML tree"""
    def __init__(self,name,attrs):
        self.name=name
        self.attrs=attrs
        self.data=""
    def __getattribute__(self,name):
#        if name.startswith("x"):
#            attr=object.__getattribute__(self,name)
#            if len(attr)==1:
#                return attr[0]
#            else:
#                return attr
        if name.startswith("p"):
            if name[1:] in self.attrs:
                return self.attrs[name[1:]]
            else:
                return AtrributeError,name
        else:
            return object.__getattribute__(self,name)

class XMLParser(object):
    def __init__(self):
        self.stack=[]
        self.current=None
    def start_element(self,name,attrs):
        #print "Start element:", name, attrs
        if self.current==None:
            self.current=self
        node=pnode(name,attrs)
        try:
            var=getattr(self.current,"x" + name)
            var.append(node)
        except AttributeError:
            setattr(self.current,"x" + name.lower(),[node,])
        self.current=node
        self.stack.append(node)            
    def end_element(self,name):
        #print "End element", name
        if self.current!=None:
            self.stack.remove(self.current)
            if len(self.stack)>0:
                self.current=self.stack[len(self.stack)-1]
            else:
                self.current=None
    def char_data(self,data):
        #print "Character data:", repr(data), str(data)
        self.current.data = self.current.data + str(data)
    def parse(self,input):
        p = xmlp.ParserCreate()

        p.StartElementHandler = self.start_element
        p.EndElementHandler = self.end_element
        p.CharacterDataHandler = self.char_data

        p.Parse(input,1)
    def readfile(self,inn):
        f = file(inn,"r")
        self.parse(f.read())
        f.close()


if __name__ == "__main__":
    a=XMLParser()
    a.parse("""<worksheet name="Easy-#1-(37)-[08/01/2007]">
        <cell value="7" idx="0"></cell>
        <cell value="8" idx="1"></cell>
        <cell value="0" idx="2"></cell>
        </worksheet>""")
    #print a.xworksheet[0].pname
    assert(a.xworksheet[0].pname=="Easy-#1-(37)-[08/01/2007]")
    for i,cell in enumerate(a.xworksheet[0].xcell):
        assert(int(cell.pidx)==i)
        if i==0:
            assert(int(cell.pvalue)==7)
        elif i==1:
            assert(int(cell.pvalue)==8)
        else:
            assert(int(cell.pvalue)==0)
