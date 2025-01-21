class ManifestError(Exception):
    """Raised when a manifest is invalid"""

    def __init__(self, message):
        super(ManifestError, self).__init__(message)
