class CCError(Exception):
    def __init__(self, err):
        self.err = err

    def __str__(self):
        return repr(self.err)