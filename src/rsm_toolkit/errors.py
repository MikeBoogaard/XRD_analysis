"""Public exceptions separate input failures from unresolved science."""


class RSMError(ValueError):
    """Base error for invalid input or configuration."""


class FormatError(RSMError):
    """Malformed supported file."""


class UnsupportedFormatError(FormatError):
    """A recognized but unsupported format/schema."""


class MissingMetadataError(RSMError):
    """Essential experimental information must be supplied explicitly."""
