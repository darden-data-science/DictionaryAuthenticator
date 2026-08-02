"""Tests for DictionaryAuthenticator.

Run against a real JupyterHub rather than the sys.modules-stubbed pattern used
in the sibling ExternalAuthenticator repo — same reasoning as NullAuthenticator:
the behaviour that matters here involves real traitlets config and JupyterHub's
own allow-gate, neither of which a stub would exercise honestly. `jupyterhub` is
a declared dependency, so it is always installed.
"""

import logging
import unittest

from traitlets.config import Config

from jupyterhub.auth import Authenticator

from DictionaryAuthenticator import DictionaryAuthenticator, __version__


def build(passwords=None, **traits):
    config = Config()
    if passwords is not None:
        config.DictionaryAuthenticator.passwords = passwords
    for name, value in traits.items():
        setattr(config.Authenticator, name, value)
    return DictionaryAuthenticator(config=config)


class AuthenticateTest(unittest.IsolatedAsyncioTestCase):
    async def test_correct_password_returns_username(self):
        auth = build({"alice": "hunter2"})
        result = await auth.authenticate(
            None, {"username": "alice", "password": "hunter2"}
        )
        self.assertEqual(result, "alice")

    async def test_wrong_password_returns_none(self):
        auth = build({"alice": "hunter2"})
        self.assertIsNone(
            await auth.authenticate(None, {"username": "alice", "password": "nope"})
        )

    async def test_unknown_user_returns_none(self):
        auth = build({"alice": "hunter2"})
        self.assertIsNone(
            await auth.authenticate(None, {"username": "mallory", "password": "hunter2"})
        )

    async def test_empty_passwords_dict_denies_everyone(self):
        auth = build({})
        self.assertIsNone(
            await auth.authenticate(None, {"username": "alice", "password": ""})
        )

    async def test_missing_form_keys_do_not_raise(self):
        """Previously indexed data['username'] directly, so any caller other
        than the built-in login form raised a bare KeyError -> HTTP 500."""
        auth = build({"alice": "hunter2"})
        for data in ({}, {"username": "alice"}, {"password": "hunter2"}):
            with self.subTest(data=data):
                self.assertIsNone(await auth.authenticate(None, data))

    async def test_non_ascii_password_matches_rather_than_raising(self):
        """secrets.compare_digest rejects non-ASCII str, so both sides are
        encoded first. Without that this raises TypeError instead of logging in."""
        auth = build({"alice": "pässwörd"})
        self.assertEqual(
            await auth.authenticate(None, {"username": "alice", "password": "pässwörd"}),
            "alice",
        )
        self.assertIsNone(
            await auth.authenticate(None, {"username": "alice", "password": "password"})
        )

    async def test_non_string_stored_password_does_not_authenticate(self):
        """YAML happily turns 1234 into an int. That must fail closed, not crash."""
        auth = build({"alice": 1234})
        self.assertIsNone(
            await auth.authenticate(None, {"username": "alice", "password": "1234"})
        )


class AllowGateTest(unittest.IsolatedAsyncioTestCase):
    """Authenticating is necessary but not sufficient under JupyterHub 5."""

    async def test_allowed_users_lets_an_authenticated_user_through(self):
        auth = build({"alice": "hunter2"}, allowed_users={"alice"})
        result = await auth.get_authenticated_user(
            None, {"username": "alice", "password": "hunter2"}
        )
        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "alice")

    async def test_authenticated_but_not_allowed_is_denied(self):
        """The failure mode that looks like a broken password but is not."""
        auth = build({"alice": "hunter2"}, allowed_users={"someone-else"})
        self.assertIsNone(
            await auth.get_authenticated_user(
                None, {"username": "alice", "password": "hunter2"}
            )
        )

    async def test_allow_all_admits_anyone_with_a_password(self):
        auth = build({"alice": "hunter2"}, allow_all=True)
        result = await auth.get_authenticated_user(
            None, {"username": "alice", "password": "hunter2"}
        )
        self.assertEqual(result["name"], "alice")


class RosterDriftWarningTest(unittest.TestCase):
    """The two rosters are maintained by hand in separate config blocks."""

    # traitlets' LoggingConfigurable.log defaults to the logger named
    # "traitlets", not one named after the class. Asserting on the class name
    # silently never matches.
    LOGGER = "traitlets"

    def warnings_from(self, **kwargs):
        with self.assertLogs(self.LOGGER, level=logging.WARNING) as caught:
            build(**kwargs)
        return "\n".join(caught.output)

    def test_warns_when_allowed_user_has_no_password(self):
        text = self.warnings_from(
            passwords={"alice": "a"}, allowed_users={"alice", "bob"}
        )
        self.assertIn("cannot log in", text)
        self.assertIn("bob", text)

    def test_warns_when_password_holder_is_not_allowed(self):
        text = self.warnings_from(
            passwords={"alice": "a", "bob": "b"}, allowed_users={"alice"}
        )
        self.assertIn("denied after authenticating", text)
        self.assertIn("bob", text)

    def test_silent_when_the_rosters_agree(self):
        with self.assertNoLogs(self.LOGGER, level=logging.WARNING):
            build(passwords={"alice": "a"}, allowed_users={"alice"})

    def test_silent_when_allow_all_makes_the_comparison_moot(self):
        with self.assertNoLogs(self.LOGGER, level=logging.WARNING):
            build(passwords={"alice": "a"}, allow_all=True, allowed_users={"bob"})

    def test_silent_when_no_allowed_users_configured(self):
        with self.assertNoLogs(self.LOGGER, level=logging.WARNING):
            build(passwords={"alice": "a"})


class PackagingTest(unittest.TestCase):
    def test_version_is_a_release_string(self):
        self.assertRegex(__version__, r"^\d+\.\d+\.\d+")

    def test_subclasses_jupyterhub_authenticator(self):
        self.assertTrue(issubclass(DictionaryAuthenticator, Authenticator))

    def test_passwords_is_configurable(self):
        self.assertIn("passwords", DictionaryAuthenticator.class_traits(config=True))


if __name__ == "__main__":
    unittest.main()
