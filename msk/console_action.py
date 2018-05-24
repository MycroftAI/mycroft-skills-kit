from abc import ABCMeta, abstractmethod
from argparse import ArgumentParser


class ConsoleAction(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, args):
        pass

    @staticmethod
    @abstractmethod
    def register(parser: ArgumentParser):
        pass

    @abstractmethod
    def perform(self):
        pass
