from __future__ import annotations

import uvicorn

from src.shared.config.settings import get_settings


def run() -> None:
    """Run the application locally."""
    settings = get_settings()
    uvicorn.run(
        "src.api.app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload_enabled,
        log_level=settings.log_level.lower(),
        factory=False,
    )


if __name__ == "__main__":
    run()
