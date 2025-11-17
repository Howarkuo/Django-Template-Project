from imghdr import tests


def get_image_type(buffer: bytes):
    """Get image type from buffer."""
    try:
        for tf in tests:
            res = tf(buffer, None)
            if res:
                return res
    except Exception:
        # TODO: add exception handling #noqa: TD002 FIX002
        return None


def sentry_test():
    """Test sentry integration."""
    division_by_zero = 1 / 0  # type: ignore # noqa: F841
