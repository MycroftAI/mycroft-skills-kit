from abc import ABCMeta, abstractmethod
from argparse import ArgumentParser

from msk.global_context import GlobalContext
from msk.lazy import Lazy
from msk.repo_action import RepoData


class ConsoleAction(GlobalContext, metaclass=ABCMeta):
    @staticmethod
    @abstractmethod
    def register(parser: ArgumentParser):
        pass

    @abstractmethod
    def perform(self):
        pass

    repo = Lazy(lambda s: RepoData())  # type: RepoData
