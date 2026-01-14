from threading import local

_thread_locals = local()


def set_current_client_id(client_id):
    """
    Sets the current client's ID in thread-local storage.
    """
    _thread_locals.client_id = client_id


def get_current_client_id():
    """
    Returns the current client's ID from thread-local storage.
    Returns None if the client ID has not been set.
    """
    return getattr(_thread_locals, 'client_id', None)
