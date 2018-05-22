from abc import ABCMeta, abstractmethod


class ConsoleAction(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, args):
        pass

    @abstractmethod
    def perform(self):
        pass
