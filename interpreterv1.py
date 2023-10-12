# exports Interpreter class
from intbase import InterpreterBase

class Interpreter(InterpreterBase):
    def __init__(self, console_output=True, inp=None):
        super().__init__(console_output, inp)