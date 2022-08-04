from secrets import token_urlsafe

ID_LENGTH = 16


def make_uid(length=ID_LENGTH):
    return token_urlsafe(length)
