from jupyterhub.auth import Authenticator


from traitlets import Dict


class DictionaryAuthenticator(Authenticator):
    """Dictionary authenticator ripped straight out of the documentation."""

    passwords = Dict(config=True,
        help="""dict of username:password for authentication"""
    )

    async def authenticate(self, handler, data):
        if self.passwords.get(data['username']) == data['password']:
            return data['username']
        else:
            return None