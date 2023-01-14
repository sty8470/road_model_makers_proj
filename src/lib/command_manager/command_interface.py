import os
import sys

from abc import ABCMeta, abstractmethod

# TODO: Do we need multiple interface for each action commands(Load, delete, add, edit(trimming))
class ICommand(metaclass=ABCMeta):
    '''
    The Command Interface declares methods.
    
    1. execute
    2. undo
    3. redo
    ## Option ##
    4. clear
    5. get_string
    '''
    @abstractmethod
    def execute():
        pass
    
    @abstractmethod
    def undo():
        pass
    
    @abstractmethod
    def redo():
        pass
    
    