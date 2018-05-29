from msm import MsmException


class MskException(MsmException):
    pass


class AlreadyUpdated(MskException):
    pass


class GithubRepoExists(MskException):
    pass


class NotUploaded(MskException):
    pass


class PRModified(MskException):
    pass
