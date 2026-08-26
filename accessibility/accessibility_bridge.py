"""
JULIE AI OS Accessibility JNI Bridge.

Build 59.
"""

from __future__ import annotations

import logging
from typing import Any, Optional


LOGGER = logging.getLogger(
    "julie.accessibility.bridge"
)


class AccessibilityBridge:

    def __init__(self) -> None:
        self._service: Optional[Any] = None

    def initialize(self) -> bool:

        try:

            from jnius import autoclass

            service_class = autoclass(
                "org.julie.ai.JulieAccessibilityService"
            )

            service = service_class.getInstance()

            if service is None:
                self._service = None
                return False

            self._service = service
            return True

        except Exception as exc:

            LOGGER.debug(
                "Accessibility service unavailable: %s",
                exc
            )

            self._service = None
            return False

    def is_available(self) -> bool:
        return self._service is not None

    def is_service_running(self) -> bool:

        if self._service is None:
            return False

        try:
            return bool(
                self._service.isServiceRunning()
            )
        except Exception:
            return False

    def get_service(self) -> Optional[Any]:
        return self._service
