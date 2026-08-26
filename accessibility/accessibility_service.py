"""
JULIE AI OS Accessibility Controller.

Build 59.
"""

from __future__ import annotations

import logging


LOGGER = logging.getLogger(
    "julie.accessibility"
)


class AccessibilityController:

    def __init__(self) -> None:
        self._enabled = False
        self._connected = False

    def set_enabled(
        self,
        enabled: bool
    ) -> None:

        self._enabled = bool(enabled)

        LOGGER.info(
            "Accessibility enabled=%s",
            self._enabled
        )

    def set_connected(
        self,
        connected: bool
    ) -> None:

        self._connected = bool(connected)

        LOGGER.info(
            "Accessibility connected=%s",
            self._connected
        )

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def connected(self) -> bool:
        return self._connected

    def status(self) -> dict[str, bool]:
        return {
            "enabled": self._enabled,
            "connected": self._connected,
        }


_controller = None


def get_controller() -> AccessibilityController:

    global _controller

    if _controller is None:
        _controller = AccessibilityController()

    return _controller
