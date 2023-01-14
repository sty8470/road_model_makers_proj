#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../'))) 

from basic_viewer_event_handler import SimpleEventHandler


if __name__ == u'__main__':
    handler = SimpleEventHandler()
    handler.start_simple_ui()
    
