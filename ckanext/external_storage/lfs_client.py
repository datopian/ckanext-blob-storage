"""Storage API
"""
from typing import Any, Dict, List, Optional

import requests


class LfsClient(object):

    LFS_MIME_TYPE = 'application/vnd.git-lfs+json'

    def __init__(self, server_url, authz_token):
        self.server_url = server_url
        self.authz_token = authz_token

    def batch(self, prefix, operation, objects, ref=None, transfers=None):
        # type: (str, str, List[Dict[str, Any]], Optional[str], Optional[List[str]]) -> Dict[str, Any]
        """Send a batch request to the LFS server
        """
        url = '{}/{}/objects/batch'.format(self.server_url, prefix)
        if transfers is None:
            transfers = ['basic']

        payload = {'transfers': transfers,
                   'operation': operation,
                   'objects': objects}
        if ref:
            payload['ref'] = ref

        response = requests.post(url, json=payload, headers={
            'Authorization': 'Bearer {}'.format(self.authz_token),
            'Content-type': self.LFS_MIME_TYPE,
            'Accept': self.LFS_MIME_TYPE
        })

        if response.status_code != 200:
            raise LfsError("Unexpected response from LFS server: {}".format(response.status_code),
                           status_code=response.status_code)

        return response.json()


class LfsError(RuntimeError):

    status_code = None

    def __init__(self, *args, **kwargs):
        if 'status_code' in kwargs:
            self.status_code = kwargs.pop('status_code')
        super(LfsError, self).__init__(*args, **kwargs)
