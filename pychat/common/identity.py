from secrets import token_urlsafe

ID_LENGTH = 10


def make_id(length=ID_LENGTH):
    return token_urlsafe(length)
