from lib.command_manager.command_interface import ICommand
from typing import List
# History Contents defined as Queue / Stack

# stack and queue implementation python
class CommandStack:
    
    def __init__(self):
        self._command_stack: List[ICommand] = []
        
    def push_cmd(self, item):
        self._command_stack.append(item)
        
    def pop_cmd(self, item):
        if len(self._command_stack) > 0:
            return self._command_stack.pop(item)
        else:
            return None
        
    def undo(self):
        cmd = self.pop_cmd()
        cmd.undo()