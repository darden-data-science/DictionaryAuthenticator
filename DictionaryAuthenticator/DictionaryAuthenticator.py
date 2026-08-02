"""A JupyterHub Authenticator backed by a dict of username -> password.

Adapted from the example in the JupyterHub documentation, packaged for pip.
Intended for small shared-login cohorts (team accounts on a short course), not
for anything resembling real identity management.
"""

import secrets

from jupyterhub.auth import Authenticator
from traitlets import Dict


def _constant_time_equal(expected, provided):
    """Compare two passwords without an early exit on the first differing byte.

    `secrets.compare_digest` rejects `str` containing non-ASCII, so both sides
    are encoded first — otherwise a non-ASCII password would raise TypeError
    rather than simply failing to match.

    This does NOT hide whether a username exists: a miss in `passwords` returns
    before reaching here. That is deliberate. These deployments keep passwords
    in plaintext in the config file anyway, so padding the timing of a username
    probe would be ceremony rather than security.
    """
    if not isinstance(expected, str) or not isinstance(provided, str):
        return False
    return secrets.compare_digest(expected.encode("utf-8"), provided.encode("utf-8"))


class DictionaryAuthenticator(Authenticator):
    """Authenticate against a configured dict of username -> password."""

    passwords = Dict(
        config=True,
        help="""dict of username:password for authentication""",
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._warn_on_roster_drift()

    def _warn_on_roster_drift(self):
        """Warn when `passwords` and `allowed_users` disagree.

        JupyterHub 5 defaults `allow_all` to False, so deployments using this
        authenticator generally also set `allowed_users`. The two lists are
        maintained by hand, in separate blocks of the same config file, and
        drift between them fails confusingly:

          - in `allowed_users` but not `passwords`: no password can ever match,
            so the form rejects the user with no explanation.
          - in `passwords` but not `allowed_users`: the password is accepted and
            JupyterHub then denies them at the allow gate.

        Neither says "your two rosters disagree", hence this warning. It stays a
        warning rather than an error: `allowed_users` legitimately contains
        admins who authenticate some other way, and `allow_all` makes the
        comparison moot entirely.
        """
        if not self.passwords or self.allow_all or not self.allowed_users:
            return

        missing_password = set(self.allowed_users) - set(self.passwords)
        missing_allow = set(self.passwords) - set(self.allowed_users)

        if missing_password:
            self.log.warning(
                "DictionaryAuthenticator: %d user(s) in allowed_users have no "
                "entry in passwords and cannot log in: %s",
                len(missing_password),
                ", ".join(sorted(missing_password)),
            )
        if missing_allow:
            self.log.warning(
                "DictionaryAuthenticator: %d user(s) in passwords are absent "
                "from allowed_users and will be denied after authenticating: %s",
                len(missing_allow),
                ", ".join(sorted(missing_allow)),
            )

    async def authenticate(self, handler, data):
        # .get rather than [] — the built-in login form always supplies both
        # keys, but any other caller reaching this raised a bare KeyError, which
        # surfaces as an unhelpful 500 rather than a failed login.
        username = data.get("username")
        password = data.get("password")
        if not username or password is None:
            return None

        expected = self.passwords.get(username)
        if expected is None:
            return None

        if _constant_time_equal(expected, password):
            return username
        return None
