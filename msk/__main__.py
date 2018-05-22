import sys
from argparse import ArgumentParser

from msk.actions.upgrade import UpgradeAction

from msk.exceptions import MshException


def main():
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(dest='action')
    subparsers.required = True
    subparsers.add_parser('upgrade').add_argument('skill_folder')
    args = parser.parse_args(sys.argv[1:])
    action_to_cls = {
        'upgrade': UpgradeAction
    }
    try:
        return action_to_cls[args.action](args).perform()
    except MshException as e:
        print('{}: {}'.format(e.__class__.__name__, str(e)))
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
