from contextlib import suppress
from git import Git, GitCommandError
from github import Github
from github.Repository import Repository
from msm import SkillRepo, SkillEntry
from os.path import join
from subprocess import call
from typing import Callable

from msk.exceptions import AlreadyUpdated, NotUploaded
from msk.util import skill_repo_name


class RepoData:
    def __init__(self, msm: SkillRepo, get_github: Callable):
        self.msm = msm
        self.git = Git(msm.path)
        self.__get_github = get_github
        self.__root_github = self.__github = self.__user = None

    def __check_github(self):
        if not self.__root_github:
            self.__root_github = self.__get_github()
            self.__github = self.__root_github.get_repo(skill_repo_name(self.msm.url))

    @property
    def github(self) -> Repository:
        self.__check_github()
        return self.__github

    @property
    def root_github(self) -> Github:
        self.__check_github()
        return self.__root_github

    def setup_fork(self):
        fork = self.root_github.get_user().create_fork(self.github)  # type: Repository
        remotes = self.git.remote().split('\n')
        command = 'set-url' if 'fork' in remotes else 'add'
        self.git.remote(command, 'fork', fork.html_url)

    def push_to_fork(self, branch: str):
        # Use call to ensure the environment variable GIT_ASKPASS is used
        call(['git', 'push', '-u', 'fork', branch, '--force'], cwd=self.msm.path)

    def get_submodule_name(self, skill: SkillEntry) -> str:
        name_to_path = {name: path for name, path, url, sha in self.msm.get_skill_data()}
        if skill.name not in name_to_path:
            raise NotUploaded('The skill {} has not yet been uploaded to the skill store'.format(
                skill.name
            ))
        return name_to_path[skill.name]

    def get_skill_git(self, skill: SkillEntry):
        return Git(join(self.msm.path, self.get_submodule_name(skill)))

    def get_skill_github(self, skill: SkillEntry):
        return self.root_github.get_repo(skill_repo_name(skill.url))

    def add_skill(self, skill: SkillEntry):
        self.git.reset('origin/' + self.msm.branch, hard=True)

        elements = [i.split() for i in self.git.ls_tree('HEAD').split('\n')]
        existing_mods = [folder for size, typ, sha, folder in elements]
        if skill.name not in existing_mods:
            self.git.submodule('add', skill.url, skill.name)
        branch_name = 'add/' + skill.name
        self.checkout_branch(branch_name)
        self.git.add(skill.name)
        self.git.commit(message='Add ' + skill.name)
        return branch_name

    def init_existing_skill(self, skill: SkillEntry):
        self.git.submodule('update', '--init', self.get_submodule_name(skill))

    def checkout_branch(self, branch):
        with suppress(GitCommandError):
            self.git.branch('-D', branch)
        try:
            self.git.checkout(b=branch)
        except GitCommandError:
            self.git.checkout(branch)

    def upgrade_skill(self, skill: SkillEntry, name: str = 'upgrade') -> \
            str:
        skill_module = self.get_submodule_name(skill)
        skill_git = Git(join(self.git.working_dir, skill_module))
        self.msm.update()
        skill_git.fetch()
        default_branch = skill_git.symbolic_ref('refs/remotes/origin/HEAD')
        skill_git.reset(default_branch, hard=True)
        upgrade_branch = name.lower() + '/' + skill.name
        self.checkout_branch(upgrade_branch)

        if not self.git.diff(skill_module) and self.git.ls_files(skill_module):
            raise AlreadyUpdated(
                'The latest version of {} is already uploaded to the skill repo'.format(skill.name)
            )
        self.git.add(skill_module)
        self.git.commit(message=name.title() + ' ' + skill.name)
        return upgrade_branch
