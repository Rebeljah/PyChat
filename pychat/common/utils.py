from secrets import choice
import string

UID_LENGTH = 10
INVITE_LENGTH = 6


def make_uid():
    chars = string.ascii_letters + string.digits
    return ''.join(choice(chars) for _ in range(UID_LENGTH))


def make_invite_code():
    chars = string.ascii_letters + '23456789'
    return ''.join(choice(chars) for _ in range(INVITE_LENGTH))
