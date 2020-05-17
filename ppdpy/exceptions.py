class PpdPyError(Exception):
    pass

class DirectiveSyntaxError(PpdPyError):
    def __init__(self, message:str='invalid directive syntax'):
        self.message = message


class ExpressionSyntaxError(PpdPyError):
    def __init__(self, message:str='invalid expression syntax'):
        self.message = message
