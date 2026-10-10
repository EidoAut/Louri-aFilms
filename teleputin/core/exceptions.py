class ServiceError(Exception):
    """A safe, user-facing service failure; never includes credentials."""
