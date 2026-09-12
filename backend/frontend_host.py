from pathlib import Path
import sys

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).resolve().parent
    return base_path / relative_path


def mount_frontend(app):
    web_directory = resource_path("web")
    index_file = web_directory / "index.html"
    assets_directory = web_directory / "assets"

    if assets_directory.exists():
        app.mount(
            "/assets",
            StaticFiles(directory=str(assets_directory)),
            name="frontend-assets",
        )

    # main.py historically exposed an API information route at "/".
    # In the packaged consumer app, the browser root must always open
    # the React dashboard. This middleware handles only the exact root
    # path and leaves every /api/* endpoint untouched.
    @app.middleware("http")
    async def privacyguard_frontend_root(request, call_next):
        if request.url.path == "/":
            return FileResponse(index_file)
        return await call_next(request)

    @app.get("/", include_in_schema=False)
    async def privacyguard_frontend():
        return FileResponse(index_file)

    @app.get("/{full_path:path}", include_in_schema=False)
    async def privacyguard_spa(full_path: str):
        requested_file = web_directory / full_path
        if requested_file.exists() and requested_file.is_file():
            return FileResponse(requested_file)
        return FileResponse(index_file)
