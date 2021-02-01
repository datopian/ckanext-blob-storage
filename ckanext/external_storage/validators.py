from ckan.plugins.toolkit import Invalid


def upload_has_sha256(key, flattened_data, errors, context):
    __extras_key = (key[0], key[1], '__extras')
    if flattened_data[key] == 'upload':
        if __extras_key not in flattened_data:
            raise Invalid("Resource's sha256 field cannot be missing for uploads.")
        elif 'sha256' not in flattened_data[__extras_key]:
            raise Invalid("Resource's sha256 field cannot be missing for uploads.")


def upload_has_size(key, flattened_data, errors, context):
    if flattened_data[key] == 'upload':
        if (key[0], key[1], 'size') not in flattened_data:
            raise Invalid("Resource's size field cannot be missing for uploads.")
