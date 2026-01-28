from __future__ import annotations

import os
import sys
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


# src 디렉터리를 sys.path에 추가 (controllers/models/utils import 호환)
SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# 웹/테스트 환경에서는 GUI 백엔드 대신 Agg를 사용(차트 생성 안정화)
os.environ.setdefault("MPLBACKEND", "Agg")
try:
    import matplotlib

    matplotlib.use("Agg")
except Exception:
    pass

from webapp.api.router import api_router
from webapp.services.project_store import ProjectStore


BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def create_app() -> FastAPI:
    app = FastAPI(
        title="DOE Tool Web API",
        description="데스크톱 DOE Tool의 계산/설계 기능을 웹 API로 제공",
        version="0.1.0",
    )
    app.state.project_store = ProjectStore()
    app.include_router(api_router)

    static_dir = BASE_DIR / "static"
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/", response_class=HTMLResponse)
    def home(request: Request):
        return templates.TemplateResponse("index.html", {"request": request, "title": "DOE Tool (Web)"})

    @app.get("/favicon.ico")
    def favicon():
        return Response(status_code=204)

    @app.get("/project", response_class=HTMLResponse)
    def project_page(request: Request):
        return templates.TemplateResponse("project.html", {"request": request, "title": "프로젝트"})

    @app.get("/data", response_class=HTMLResponse)
    def data_page(request: Request):
        return templates.TemplateResponse("data.html", {"request": request, "title": "데이터"})

    @app.get("/design", response_class=HTMLResponse)
    def design_page(request: Request):
        return templates.TemplateResponse("design.html", {"request": request, "title": "실험설계"})

    @app.get("/analysis", response_class=HTMLResponse)
    def analysis_page(request: Request):
        return templates.TemplateResponse("analysis.html", {"request": request, "title": "분석"})

    @app.get("/charts", response_class=HTMLResponse)
    def charts_page(request: Request):
        return templates.TemplateResponse("charts.html", {"request": request, "title": "차트"})

    @app.get("/history", response_class=HTMLResponse)
    def history_page(request: Request):
        return templates.TemplateResponse("history.html", {"request": request, "title": "히스토리"})

    return app


app = create_app()


if __name__ == "__main__":
    import argparse

    import uvicorn

    parser = argparse.ArgumentParser(description="Run DOE Tool Web API (FastAPI)")
    parser.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")))
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Auto-reload on code changes (useful in development)",
    )
    args = parser.parse_args()

    print(f"\nWeb UI:  http://{args.host}:{args.port}/")
    print(f"API docs: http://{args.host}:{args.port}/docs\n")

    # Note: reload works best when starting via `python -m uvicorn webapp.app:app --app-dir src --reload`.
    uvicorn.run(app, host=args.host, port=args.port, reload=args.reload)
