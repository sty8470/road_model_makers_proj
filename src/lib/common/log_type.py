#!/usr/bin/env python
# -*- coding: utf-8 -*-

from enum import Enum

class LogType(Enum):
    DEBUG = 10
    TRACE = 20
    INFO = 30
    WARNING = 40
    ERROR = 50