from __future__ import annotations

from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self) -> None:  # pragma: no cover
        # import signal handlers here when they are created
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass
