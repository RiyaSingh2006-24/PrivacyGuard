import os
import platform
from pathlib import Path


def get_app_data_directory():

    system = platform.system().lower()

    if system == "windows":

        base = os.getenv("LOCALAPPDATA")

        if base:
            base_directory = Path(base)
        else:
            base_directory = (
                Path.home()
                / "AppData"
                / "Local"
            )

    elif system == "darwin":

        base_directory = (
            Path.home()
            / "Library"
            / "Application Support"
        )

    else:

        xdg_directory = os.getenv(
            "XDG_DATA_HOME"
        )

        if xdg_directory:
            base_directory = Path(
                xdg_directory
            )
        else:
            base_directory = (
                Path.home()
                / ".local"
                / "share"
            )


    app_directory = (
        base_directory
        / "PrivacyGuard"
    )

    app_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    return app_directory


APP_DATA_DIR = (
    get_app_data_directory()
)

DB_PATH = (
    APP_DATA_DIR
    / "privacyguard.db"
)
