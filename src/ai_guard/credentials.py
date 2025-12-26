"""
Centralized definitions for AI-Guard's default application credentials.

Keeping all default credentials in one place ensures that helper scripts,
the web UI, database seeders, and documentation stay aligned.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Callable, Dict


CredentialMap = Dict[str, Dict[str, str]]


DEFAULT_CREDENTIALS: CredentialMap = {
    "admin": {
        "password": "Kc@12345",
        "role": "admin",
        "name": "Administrator",
        "email": "admin@ai-guard.com",
    },
    "dev1": {
        "password": "Kc@123456",
        "role": "developer",
        "name": "Developer 1",
        "email": "dev1@ai-guard.com",
    },
    "dev2": {
        "password": "Kc@123456",
        "role": "developer",
        "name": "Developer 2",
        "email": "dev2@ai-guard.com",
    },
    "manager": {
        "password": "Kc@123456",
        "role": "manager",
        "name": "Project Manager",
        "email": "manager@ai-guard.com",
    },
    "viewer": {
        "password": "Kc@1234567",
        "role": "viewer",
        "name": "Viewer",
        "email": "viewer@ai-guard.com",
    },
}


def get_plain_credentials() -> CredentialMap:
    """
    Return a deepcopy of the default credentials suitable for display,
    scripting, or any workflow that requires clear-text passwords.
    """

    return deepcopy(DEFAULT_CREDENTIALS)


def get_hashed_credentials(password_hasher: Callable[[str], str]) -> CredentialMap:
    """
    Return credentials with passwords transformed by the provided hasher.

    Parameters
    ----------
    password_hasher:
        A callable (e.g. werkzeug.security.generate_password_hash) used to hash
        the clear-text passwords.
    """

    hashed_credentials: CredentialMap = {}
    for username, details in DEFAULT_CREDENTIALS.items():
        hashed_credentials[username] = {
            **details,
            "password": password_hasher(details["password"]),
        }
    return hashed_credentials


def get_display_credentials() -> Dict[str, Dict[str, str]]:
    """
    Provide a sanitized view of credentials emphasising role/username/password.
    """

    return {
        username: {
            "role": details["role"].title(),
            "username": username,
            "password": details["password"],
        }
        for username, details in DEFAULT_CREDENTIALS.items()
    }
