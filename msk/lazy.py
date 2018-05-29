from functools import wraps


class Lazy:
    """Lazy attribute across all instances"""
    def __init__(self, func):
        wraps(func)(self)
        self.func = func
        self.return_val = None

    def __get__(self, inst, inst_cls):
        self.return_val = self.return_val or self.func(inst)
        return self.return_val
