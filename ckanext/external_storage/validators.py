from ckan.plugins.toolkit import Invalid


def upload_has_sha256(key, flattened_data, errors, context):
    if flattened_data[key] == 'upload':
        if (key[0], key[1], 'sha256') not in flattened_data:
            raise Invalid("Resource's sha256 field cannot be missing for uploads.")


def valid_sha256(value):
    if not _is_hex_str(value, 64):
        raise Invalid("Resource's sha256 is not a valid hex-only string.")
    return value


def upload_has_size(key, flattened_data, errors, context):
    if flattened_data[key] == 'upload':
        if (key[0], key[1], 'size') not in flattened_data:
            raise Invalid("Resource's size field cannot be missing for uploads.")


def upload_has_lfs_prefix(key, flattened_data, errors, context):
    if flattened_data[key] == 'upload':
        if (key[0], key[1], 'lfs_prefix') not in flattened_data:
            raise Invalid("Resource's lfs_prefix field cannot be missing for uploads.")


def valid_lfs_prefix(value):
    if value == "":
        raise Invalid("Resource's lfs_prefix field cannot be empty.")
    return value


def _is_hex_str(value, chars=40):
    # type: (str, int) -> bool
    """Check if a string is a hex-only string of exactly :param:`chars` characters length.
    This is useful to verify that a string contains a valid SHA, MD5 or UUID-like value.
    >>> _is_hex_str('0f1128046248f83dc9b9ab187e16fad0ff596128f1524d05a9a77c4ad932f10a', 64)
    True
    >>> _is_hex_str('0f1128046248f83dc9b9ab187e16fad0ff596128f1524d05a9a77c4ad932f10a', 32)
    False
    >>> _is_hex_str('0f1128046248f83dc9b9ab187e1xfad0ff596128f1524d05a9a77c4ad932f10a', 64)
    False
    >>> _is_hex_str('ef42bab1191da272f13935f78c401e3de0c11afb')
    True
    >>> _is_hex_str('ef42bab1191da272f13935f78c401e3de0c11afb'.upper())
    True
    >>> _is_hex_str('ef42bab1191da272f13935f78c401e3de0c11afb', 64)
    False
    >>> _is_hex_str('ef42bab1191da272f13935.78c401e3de0c11afb')
    False
    """
    if len(value) != chars:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True
