import os
from argparse import ArgumentParser
from git import Git
from msm import SkillEntry, SkillRepo
from os.path import isdir, join, isfile
from subprocess import call

from msk.console_action import ConsoleAction
from msk.exceptions import MissingReadme
from msk.repo_action import RepoData
from msk.util import ask_for_github_credentials, skill_repo_name, ask_input, skills_kit_footer, \
    create_or_edit_pr

body_template = '''
## Info

This PR adds the new skill, [{skill_name}]({skill_url}), to the skills repo.

## Description

{description}

''' + skills_kit_footer


class UploadAction(ConsoleAction):
    def __init__(self, args):
        ConsoleAction.__init__(self, args)
        self.folder = args.skill_folder
        self.skill = SkillEntry.from_folder(self.folder)

    @staticmethod
    def register(parser: ArgumentParser):
        parser.add_argument('skill_folder')

    def perform(self):
        github = ask_for_github_credentials()
        user = github.get_user()
        repo = RepoData(SkillRepo(), lambda: github)

        git = Git(self.skill.path)
        if not self.skill.url:
            print('No GitHub repository found. Creating new one.')
            repo_name = input('Repo Name: ')
            repo_desc = input('Repo Description: ')
            skill_repo = user.create_repo(repo_name, repo_desc)
            self.skill.url = skill_repo.html_url
            self.skill.author = user.login

            if not isdir(join(self.skill.path, '.git')):
                git.init()

            if not git.rev_parse('HEAD'):  # No commits
                if not isfile('.gitignore'):
                    with open(join(self.skill.path, '.gitignore'), 'w') as f:
                        f.write('\n'.join(['*.pyc', 'settings.json']))
                git.add('.')
                git.commit(message='Initial Commit')

            git.remote('add', 'origin', skill_repo.html_url)
            call(['git', 'push', '-u', 'origin', 'master'], cwd=git.working_dir)
        else:
            skill_repo = github.get_repo(skill_repo_name(self.skill.url))

        if not skill_repo.permissions.push:
            print('Warning: You do not have write permissions to the provided skill repo.')
            resp = ask_input('Create a fork and use that instead? (Y/n)',
                             lambda x: not x or x in 'yYnN')
            if resp.lower() != 'n':
                skill_repo = user.create_fork(skill_repo.full_name)
                print('Created fork:', skill_repo.html_url)
                git.remote('rename', 'origin', 'upstream')
                git.remote('add', 'origin', skill_repo.html_url)

        self.skill.name = input('Enter a unique skill name (ie. npr-news or grocery-list): ')
        branch = repo.add_skill(self.skill)
        repo.setup_fork()
        repo.push_to_fork(branch)

        readme_files = [i for i in os.listdir(self.skill.path) if i.lower() == 'readme.md']
        if not readme_files:
            raise MissingReadme('Please create a readme using the readme creator')

        with open(join(self.skill.path, readme_files[0])) as f:
            readme = f.read()

        last_section = None
        sections = {last_section: ''}
        for line in readme.split('\n'):
            line = line.strip()
            if line.startswith('#'):
                last_section = line.strip('# ').lower()
                sections[last_section] = ''
            else:
                sections[last_section] += '\n' + line
        del sections[None]

        if 'description' in sections:
            description = sections['description']
        else:
            section_list = list(sections)
            resp = ask_input('Which section contains the description?\n{}\n> '.format(
                '\n'.join('{}. {}'.format(i, section) for i, section in enumerate(section_list, 1))
            ), lambda x: 0 < int(x) <= len(sections))
            description = section_list[int(resp) - 1]

        pull = create_or_edit_pr(
            title='Add {}'.format(self.skill.name), body=body_template.format(
                description=description, skill_name=self.skill.name, skill_url=skill_repo.html_url
            ), user=user, branch=branch, skills_repo=repo.github
        )

        print('Created pull request: ', pull.html_url)
