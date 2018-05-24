from argparse import ArgumentParser
from genericpath import samefile
from git import Git
from github.NamedUser import NamedUser
from github.Repository import Repository
from msm import MycroftSkillsManager, SkillRepo

from msk import __version__
from msk.console_action import ConsoleAction
from msk.exceptions import NotUploaded, PRModified
from msk.repo_action import RepoData
from msk.util import ask_for_github_credentials, skills_kit_footer

body_template = '''
'This upgrades {skill_name} to include the following new commits:

{commits}

''' + skills_kit_footer


class UpgradeAction(ConsoleAction):
    def __init__(self, args):
        ConsoleAction.__init__(self, args)
        msm = MycroftSkillsManager()
        skill_matches = [
            skill
            for skill in msm.list()
            if skill.is_local and samefile(skill.path, args.skill_folder)
        ]
        if not skill_matches:
            raise NotUploaded('Skill at folder not uploaded to store: {}'.format(args.skill_folder))

        self.skill = skill_matches[0]

    @staticmethod
    def register(parser: ArgumentParser):
        parser.add_argument('skill_folder')

    def create_pr_message(self, skill_git: Git, skill_repo: Repository) -> tuple:
        """Reads git commits from skill repo to create a list of changes as the PR content"""
        title = 'Upgrade ' + self.skill.name
        body = body_template.format(
            skill_name=self.skill.name,
            commits='\n'.join(
                ' - [{}]({})'.format(
                    skill_git.show('-s', sha, format='%s'),
                    skill_repo.get_commit(sha).html_url
                )
                for sha in skill_git.rev_list(
                    '--ancestry-path', '{}..{}'.format(self.skill.sha, 'HEAD')
                ).split('\n')
            )
        )
        return title, body

    def perform(self):
        github = None
        repo = RepoData(SkillRepo(), lambda: github)
        repo.init_existing_skill(self.skill)
        github = ask_for_github_credentials()
        upgrade_branch = repo.upgrade_skill(self.skill)

        repo.setup_fork()
        repo.push_to_fork(upgrade_branch)

        title, body = self.create_pr_message(repo.get_skill_git(self.skill),
                                             repo.get_skill_github(self.skill))
        print()
        print('===', title, '===')
        print(body)
        print()
        pull = self.create_or_edit_pr(title, body, repo.github, github.get_user(), upgrade_branch)
        print('Created PR at:', pull.html_url)
