from msm import MsmException


class MshException(MsmException):
    pass


class AlreadyUpdated(MshException):
    pass


class NotUploaded(MshException):
    pass


class PRModified(MshException):
    pass
