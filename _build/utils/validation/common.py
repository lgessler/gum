
def print_header(message):
    print()
    print("=" * (len(message) + 44))
    print("|" + (" " * 20) + " " + message + " " + (" " * 20) + "|")
    print("=" * (len(message) + 44))


def check(message):
    """
    Use on every function that implements a check for consistent printing
    """
    if not message:
        raise Exception("Please describe your check by handing the `check` decorator a `message` kwarg")

    def wrapper(f):
        def inner(*args, **kwargs):
            print("💭 " + message)
            rval = f(*args, **kwargs)
            print()
            return rval
        return inner
    return wrapper


def warning(slug, message):
    print(f'⚠ {slug}: {message}️')
    
    
def error(slug, message):
    print(f'• {slug}: {message}️')
