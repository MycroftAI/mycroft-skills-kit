from github import Github
from github.AuthenticatedUser import AuthenticatedUser
from msm import MycroftSkillsManager

from msk.lazy import Lazy
from msk.util import ask_for_github_credentials


class GlobalContext:
    msm = Lazy(lambda s: MycroftSkillsManager())  # type: MycroftSkillsManager
    github = Lazy(lambda s: ask_for_github_credentials())  # type: Github
    user = Lazy(lambda s: s.github.get_user())  # type: AuthenticatedUser
