"""Example JupyterHub config using DictionaryAuthenticator.

Run with:  jupyterhub --config jupyterhub_config.example.py
"""

c = get_config()  # noqa: F821  (injected by traitlets)

# Either form works. The dotted path is what Zero-to-JupyterHub deployments tend
# to use, since it needs no entry-point resolution inside the hub image.
c.JupyterHub.authenticator_class = "dictionary_authenticator"
# c.JupyterHub.authenticator_class = "DictionaryAuthenticator.DictionaryAuthenticator"

# The credential store. In a real deployment this comes from encrypted config —
# anything here is plaintext to whoever can read the file.
c.DictionaryAuthenticator.passwords = {
    "team1": "correct-horse",
    "team2": "battery-staple",
}

# REQUIRED on JupyterHub 5+, and the single easiest thing to get wrong.
#
# allow_all defaults to False, so authenticating successfully is not enough —
# JupyterHub checks this list afterwards. Keeping it in step with `passwords`
# above is manual, so the authenticator logs a warning at startup if the two
# disagree. Watch for it after any roster change.
c.Authenticator.allowed_users = set(c.DictionaryAuthenticator.passwords)

# The alternative: skip allowed_users entirely and admit anyone with a valid
# password. Fine for a throwaway hub, and it disables the drift warning since
# there is no second list to disagree with.
# c.Authenticator.allow_all = True

# Admins do not get an implicit password — an admin still needs an entry in
# `passwords`, or they cannot log in at all.
# c.Authenticator.admin_users = {"team1"}
