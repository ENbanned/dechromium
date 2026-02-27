from __future__ import annotations


class DechromiumError(Exception):
    """Base exception for all dechromium errors."""


class ProfileNotFoundError(DechromiumError):
    """Raised when a profile does not exist on disk."""


class ProfileExistsError(DechromiumError):
    """Raised when attempting to create a profile that already exists."""


class BrowserError(DechromiumError):
    """Base exception for browser-related errors."""


class BrowserNotRunningError(BrowserError):
    """Raised when an operation requires a running browser but none is found."""


class BrowserTimeoutError(BrowserError):
    """Raised when a browser fails to become ready within the timeout."""


class DisplayError(DechromiumError):
    """Raised when the virtual display (Xvfb) fails to start."""
