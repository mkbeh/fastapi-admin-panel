import os
import string
import random
import hashlib


_population = string.ascii_letters + string.digits + string.punctuation


def get_random_string(length: int = 16) -> str:
    """ Получение рандомной строки. """
    return ''.join(random.choices(_population, k=length))


def create_secret(bytes_length=1024):
    return hashlib.sha256(os.urandom(bytes_length)).hexdigest()
