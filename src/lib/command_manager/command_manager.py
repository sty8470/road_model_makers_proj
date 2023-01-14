from PyQt5.QtCore import QMutex
from lib.command_manager.command_interface import ICommand
from lib.command_manager.concrete_commands import *
from lib.common.logger import Logger

class CommandManager(ICommand):
    """
    The Invoker is associated with one or several commands. It sends a request to the command
    """   
    def __init__(self):
        self._history_limit = 10
        self.cmd_mutex = QMutex()
        self.clear()

    def execute(self, command):
        lock = self.cmd_mutex.tryLock(10)
        if not lock :
            return
        try:
            #check max size
            if (len(self._history) >= self._history_limit) and (self._history_position >= self._history_limit):
                self._history.pop(0)
                self._history_position -= 1

            # If the new event occurs
            if len(self._history) > self._history_position:
                self._history = self._history[:self._history_position]

            result = command.execute()
            if result :
                self._history.append(command)
                self._history_position += 1
        except BaseException as e:
            raise BaseException(e.args[0])
            #Logger.log_error('[ERROR]: Error Occured when execute command was used')
        finally :
            self.cmd_mutex.unlock()
    
    def undo(self):
        lock = self.cmd_mutex.tryLock(10)
        if not lock :
            return
        try:
            if self._history_position > 0:
                self._history_position -= 1
                self._history[self._history_position].undo()
            else:
                Logger.log_info('Nothing to do undo')
                
        except BaseException as e:
            Logger.log_error('[ERROR]: Error Occured when undo command was used')
        finally :
            self.cmd_mutex.unlock()
            
            
    def redo(self):
        lock = self.cmd_mutex.tryLock(10)
        if not lock :
            return
        try:
            if self._history_position < len(self._history):
                self._history[self._history_position].redo()
                self._history_position += 1
            else:
                Logger.log_info('Nothing to do redo')
        
        except BaseException as e:
            Logger.log_error('[ERROR]: Error Occured when redo command was used')
        finally :
            self.cmd_mutex.unlock()

    def clear(self) :
        self._history = []
        self._history_position = 0