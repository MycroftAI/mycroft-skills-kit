from functools import wraps


class Lazy:
    """Lazy attribute across all instances"""
    initial_val = []

    def __init__(self, func):
        wraps(func)(self)
        self.func = func
        self.return_val = self.initial_val

    def __get__(self, inst, inst_cls):
        if self.return_val is self.initial_val:
            self.return_val = self.func(inst)
        return self.return_val
