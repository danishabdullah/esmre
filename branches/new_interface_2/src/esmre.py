#!/usr/bin/env python
# encoding: utf-8

# esmre.py - clue-indexed regular expressions module
# Copyright (C) 2007 Tideway Systems Limited.
# 
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
# 
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
# USA

import esm
import threading
import re
import itertools

def hints(regex):
    hints = [""]
    to_append = ""
    
    group_level = 0
    in_class = False
    in_backslash = False
    in_braces = False
    
    for ch in regex:
        if in_backslash:
            in_backslash = False
            
        elif in_class:
            if ch == "]":
                in_class = False
                
            elif ch == "\\":
                in_backslash = True
            
            else:
                pass
            
        elif group_level > 0:
            if ch == ")":
                group_level -= 1
                
            elif ch == "(":
                group_level += 1
                
            elif ch == "[":
                in_class = True
                
            elif ch == "\\":
                in_backslash = True
                
            else:
                pass
        
        elif in_braces:
            if ch == "}":
                in_braces = False
            
            else:
                pass
        
        else:
            if ch in "?*":
                to_append = ""
                hints.append("")
            
            elif ch in "+.^$":
                if to_append:
                    hints[-1] += to_append
                
                to_append = ""
                hints.append("")
            
            elif ch == "(":
                if to_append:
                    hints[-1] += to_append
                    
                to_append = ""
                hints.append("")
                group_level += 1
            
            elif ch == "[":
                if to_append:
                    hints[-1] += to_append
                
                to_append = ""
                hints.append("")
                in_class = True
            
            elif ch == "{":
                if to_append:
                    hints[-1] += to_append[:-1]
                
                to_append = ""
                hints.append("")
                in_braces = True
                
            elif ch == "\\":
                if to_append:
                    hints[-1] += to_append
                
                to_append = ""
                hints.append("")
                in_backslash = True
                
            elif ch == "|":
                return []
                
            else:
                if to_append:
                    hints[-1] += to_append
                
                to_append = ch
            
    if to_append:
        hints[-1] += to_append
            
    return [hint for hint in hints if hint]


def shortlist(hints):
    if not hints:
        return []
    
    best = ""
    
    for hint in hints:
        if len(hint) > len(best):
            best = hint
            
    return [best]


def memomatcher(regex):
    def match(string):
        return match._match(string)
        
    def _match(string):
        match._match = re.compile(regex).search
        return match._match(string)
        
    match._match = _match
    match.regex = regex
    return match


class Index(object):
    def __init__(self):
        self.esm = esm.Index()
        self.hintless_objects = list()
        self.fixed = False
        self.lock = threading.Lock()
        
        
    def enter(self, regex, obj):
        self.lock.acquire()
        try:
            
            if self.fixed:
                raise TypeError, "enter() cannot be called after query()"
            
            keywords = shortlist(hints(regex))
            
            if not keywords:
                self.hintless_objects.append((memomatcher(regex), obj))
            
            for hint in shortlist(hints(regex)):
                self.esm.enter(hint.lower(), (memomatcher(regex), obj))
        
        finally:
            self.lock.release()
            
            
    def query(self, string):
        self.lock.acquire()
        try:
            
            if not self.fixed:
                self.esm.fix()
                self.fixed = True
            
        finally:
            self.lock.release()
        
        return [obj for (matcher, obj) in itertools.chain(
                    self.hintless_objects,
                    (pair for (_, pair) in self.esm.query(string.lower())))
                if matcher(string)]