from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

if TYPE_CHECKING:
    from . import Dechromium


class CreateRequest(BaseModel):
    name: str = "default"
    platform: str | None = None
    proxy: str | None = None
    timezone: str | None = None
    locale: str | None = None
    languages: list[str] | None = None
    identity: dict | None = None
    hardware: dict | None = None
    webgl: dict | None = None
    noise: dict | None = None
    network: dict | None = None
    fonts: dict | None = None
    notes: str = ""


class UpdateRequest(BaseModel):
    name: str | None = None
    notes: str | None = None
    identity: dict | None = None
    hardware: dict | None = None
    webgl: dict | None = None
    noise: dict | None = None
    network: dict | None = None
    fonts: dict | None = None


class StartRequest(BaseModel):
    headless: bool = True
    extra_args: list[str] | None = None
    timeout: float = 15.0


class CookieImportRequest(BaseModel):
    path: str | None = None
    cookies: list[dict] | None = None


def create_app(dc: Dechromium) -> FastAPI:
    app = FastAPI(title="dechromium", version="0.1.0")

    @app.post("/profiles")
    def create_profile(req: CreateRequest):
        kwargs = req.model_dump(exclude_none=True)
        name = kwargs.pop("name", "default")
        profile = dc.create(name, **kwargs)
        return profile.model_dump()

    @app.get("/profiles")
    def list_profiles():
        return [p.model_dump() for p in dc.list()]

    @app.get("/profiles/{profile_id}")
    def get_profile(profile_id: str):
        try:
            return dc.get(profile_id).model_dump()
        except FileNotFoundError:
            raise HTTPException(404, "Profile not found")

    @app.put("/profiles/{profile_id}")
    def update_profile(profile_id: str, req: UpdateRequest):
        kwargs = req.model_dump(exclude_none=True)
        try:
            profile = dc.update(profile_id, **kwargs)
        except FileNotFoundError:
            raise HTTPException(404, "Profile not found")
        return profile.model_dump()

    @app.delete("/profiles/{profile_id}")
    def delete_profile(profile_id: str):
        if not dc.delete(profile_id):
            raise HTTPException(404, "Profile not found")
        return {"deleted": True}

    @app.post("/profiles/{profile_id}/start")
    def start_browser(profile_id: str, req: StartRequest = StartRequest()):
        try:
            info = dc.start(
                profile_id,
                headless=req.headless,
                extra_args=req.extra_args,
                timeout=req.timeout,
            )
        except FileNotFoundError:
            raise HTTPException(404, "Profile not found")
        except TimeoutError as e:
            raise HTTPException(504, str(e))
        except RuntimeError as e:
            raise HTTPException(500, str(e))
        return {
            "profile_id": info.profile_id,
            "pid": info.pid,
            "debug_port": info.debug_port,
            "ws_endpoint": info.ws_endpoint,
            "cdp_url": info.cdp_url,
        }

    @app.post("/profiles/{profile_id}/stop")
    def stop_browser(profile_id: str):
        return {"stopped": dc.stop(profile_id)}

    @app.get("/profiles/{profile_id}/status")
    def browser_status(profile_id: str):
        return dc.status(profile_id)

    @app.get("/running")
    def list_running():
        return [
            {
                "profile_id": i.profile_id,
                "pid": i.pid,
                "debug_port": i.debug_port,
                "ws_endpoint": i.ws_endpoint,
                "cdp_url": i.cdp_url,
            }
            for i in dc.running()
        ]

    @app.post("/profiles/{profile_id}/cookies/import")
    def do_import_cookies(profile_id: str, req: CookieImportRequest):
        try:
            dc.get(profile_id)
        except FileNotFoundError:
            raise HTTPException(404, "Profile not found")
        if req.cookies:
            count = dc.import_cookies(profile_id, req.cookies)
        elif req.path:
            count = dc.import_cookies(profile_id, req.path)
        else:
            raise HTTPException(400, "Provide 'path' or 'cookies'")
        return {"imported": count}

    @app.get("/profiles/{profile_id}/cookies/export")
    def do_export_cookies(profile_id: str):
        try:
            dc.get(profile_id)
        except FileNotFoundError:
            raise HTTPException(404, "Profile not found")
        return dc.export_cookies(profile_id)

    @app.post("/stop-all")
    def stop_all():
        dc.stop_all()
        return {"stopped": True}

    @app.get("/health")
    def health():
        return {
            "status": "ok",
            "profiles": len(dc.list()),
            "running": len(dc.running()),
        }

    return app
