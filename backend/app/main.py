from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.dashboard import router as dashboard_router
from app.api.agents import router as agents_router
from app.api.approvals import router as approvals_router
from app.api.security import router as security_router
from app.api.claims import router as claims_router
from app.api.agent_runner import router as agent_runner_router
from fastapi.openapi.docs import (
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="AgentShield",
    version="0.1.0",
    docs_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://agentshield-kappa.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static",
)


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui():
    response = get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title="AgentShield — Runtime Security API",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
    )

    html = response.body.decode("utf-8")

    html = html.replace(
        "</head>",
        """
        <link
            rel="stylesheet"
            type="text/css"
            href="/static/agentshield-swagger.css"
        >
        </head>
        """,
    )

    return HTMLResponse(content=html)


@app.get(
    app.swagger_ui_oauth2_redirect_url,
    include_in_schema=False,
)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()

@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(security_router)
app.include_router(approvals_router)
app.include_router(agents_router)
app.include_router(claims_router)
app.include_router(agent_runner_router)
app.include_router(dashboard_router)