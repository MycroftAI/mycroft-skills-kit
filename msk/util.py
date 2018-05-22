import atexit

from getpass import getpass
from github import Github, BadCredentialsException
from os import chmod

import os
from tempfile import mkstemp

ASKPASS = '''#!/usr/bin/env python3
import sys
print(
    "{password}"
    if sys.argv[1] == "Password for 'https://{username}@github.com': " else
    "{username}"
)'''


def register_git_injector(username, password):
    """Generate a script that writes the password to the git command line tool"""
    fd, tmp_path = mkstemp()
    atexit.register(lambda: os.remove(tmp_path))

    with os.fdopen(fd, 'w') as f:
        f.write(ASKPASS.format(username=username, password=password))

    chmod(tmp_path, 0o700)
    os.environ['GIT_ASKPASS'] = tmp_path


def ask_for_github_credentials() -> Github:
    print('=== GitHub Credentials ===')
    while True:
        username = input('Username: ')
        password = getpass('Password: ')
        github = Github(username, password)
        try:
            _ = github.get_user().login
            register_git_injector(username, password)
            return github
        except BadCredentialsException:
            print('Login incorrect. Retry:')