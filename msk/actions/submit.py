from argparse import ArgumentParser

from msk.actions.upgrade import UpgradeAction
from msk.actions.upload import UploadAction
from msk.console_action import ConsoleAction
from msk.exceptions import NotUploaded


class SubmitAction(ConsoleAction):
    def __init__(self, args):
        try:
            self.action = UpgradeAction(args)
        except NotUploaded:
            self.action = UploadAction(args)

    @staticmethod
    def register(parser: ArgumentParser):
        parser.add_argument('skill_folder')

    def perform(self):
        self.action.perform()
