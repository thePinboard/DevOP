from fastapi import FastAPI, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from core.database import engine, Base, AsyncSessionLocal
from models import User, Progress
from schemas import (
    UserCreate, UserResponse,
    ProgressCreate, ProgressUpdate, ProgressResponse,
    CertificateResponse
)

app = FastAPI(title="Learn to Cloud API", version="1.0.0")

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# ── USERS ──────────────────────────────────────────────

@app.get("/users", response_model=list[UserResponse])
async def get_users():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        return result.scalars().all()

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    async with AsyncSessionLocal() as session:
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User nicht gefunden")
        return user

@app.post("/users", response_model=UserResponse, status_code=201)
async def create_user(user_data: UserCreate):
    async with AsyncSessionLocal() as session:
        try:
            user = User(
                username=user_data.username,
                email=user_data.email,
                is_active=True
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user
        except IntegrityError:
            await session.rollback()
            raise HTTPException(
                status_code=409,
                detail=f"User '{user_data.username}' existiert bereits."
            )

# ── PROGRESS ───────────────────────────────────────────

@app.get("/progress/{user_id}", response_model=list[ProgressResponse])
async def get_progress(user_id: int):
    async with AsyncSessionLocal() as session:
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User nicht gefunden")
        result = await session.execute(
            select(Progress).where(Progress.user_id == user_id)
        )
        return result.scalars().all()

@app.post("/progress/{user_id}", response_model=ProgressResponse, status_code=201)
async def create_progress(user_id: int, data: ProgressCreate):
    async with AsyncSessionLocal() as session:
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User nicht gefunden")
        progress = Progress(
            user_id=user_id,
            phase=data.phase,
            completed=data.completed
        )
        session.add(progress)
        await session.commit()
        await session.refresh(progress)
        return progress

@app.patch("/progress/{progress_id}", response_model=ProgressResponse)
async def update_progress(progress_id: int, data: ProgressUpdate):
    async with AsyncSessionLocal() as session:
        progress = await session.get(Progress, progress_id)
        if not progress:
            raise HTTPException(status_code=404, detail="Progress nicht gefunden")
        if data.phase is not None:
            progress.phase = data.phase
        if data.step is not None:
            progress.step = data.step
        if data.completed is not None:
            progress.completed = data.completed
        await session.commit()
        await session.refresh(progress)
        return progress

@app.delete("/progress/{progress_id}", status_code=204)
async def delete_progress(progress_id: int):
    async with AsyncSessionLocal() as session:
        progress = await session.get(Progress, progress_id)
        if not progress:
            raise HTTPException(status_code=404, detail="Progress nicht gefunden")
        await session.delete(progress)
        await session.commit()

# ── CERTIFICATE ────────────────────────────────────────

TOTAL_PHASES = 7

@app.get("/certificate/{user_id}", response_model=CertificateResponse)
async def get_certificate(user_id: int):
    async with AsyncSessionLocal() as session:
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User nicht gefunden")
        result = await session.execute(
            select(Progress).where(
                Progress.user_id == user_id,
                Progress.completed == True
            )
        )
        completed = result.scalars().all()
        completed_phases = len(set(p.phase for p in completed))
        eligible = completed_phases >= TOTAL_PHASES
        return CertificateResponse(
            user_id=user_id,
            eligible=eligible,
            completed_phases=completed_phases,
            message="Zertifikat verfügbar!" if eligible else f"{completed_phases}/{TOTAL_PHASES} Phasen abgeschlossen."
        )

# ── HTML ROUTEN ────────────────────────────────────────
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import Request

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/dashboard/{user_id}")
async def dashboard(request: Request, user_id: int):
    async with AsyncSessionLocal() as session:
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User nicht gefunden")
        result = await session.execute(
            select(Progress).where(Progress.user_id == user_id)
        )
        phases = result.scalars().all()
        completed_phases = len(set(p.phase for p in phases if p.completed))
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "user": user,
            "phases": phases,
            "completed_phases": completed_phases
        })

@app.get("/certificate-page/{user_id}")
async def certificate_page(request: Request, user_id: int):
    async with AsyncSessionLocal() as session:
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User nicht gefunden")
        result = await session.execute(
            select(Progress).where(
                Progress.user_id == user_id,
                Progress.completed == True
            )
        )
        completed = result.scalars().all()
        completed_phases = len(set(p.phase for p in completed))
        eligible = completed_phases >= TOTAL_PHASES
        certificate = CertificateResponse(
            user_id=user_id,
            eligible=eligible,
            completed_phases=completed_phases,
            message=f"{completed_phases}/{TOTAL_PHASES} Phasen abgeschlossen."
        )
        return templates.TemplateResponse("certificate.html", {
            "request": request,
            "user": user,
            "certificate": certificate
        })


@app.get("/toggle/{progress_id}/{completed}")
async def toggle_progress(request: Request, progress_id: int, completed: str):
    async with AsyncSessionLocal() as session:
        progress = await session.get(Progress, progress_id)
        if not progress:
            raise HTTPException(status_code=404, detail="Progress nicht gefunden")
        progress.completed = completed.lower() == "true"
        await session.commit()
        # Redirect zurück zum Dashboard
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"/dashboard/{progress.user_id}", status_code=302)


# ── GITHUB OAUTH ───────────────────────────────────────
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
import os

load_dotenv()

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY")
)

oauth = OAuth()
oauth.register(
    name="github",
    client_id=os.getenv("GITHUB_CLIENT_ID"),
    client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
    access_token_url="https://github.com/login/oauth/access_token",
    authorize_url="https://github.com/login/oauth/authorize",
    api_base_url="https://api.github.com/",
    client_kwargs={"scope": "user:email"},
)

@app.get("/login")
async def login(request: Request):
    redirect_uri = "http://192.168.2.146:8000/auth/callback"
    return await oauth.github.authorize_redirect(request, redirect_uri)

@app.get("/auth/callback")
async def auth_callback(request: Request):
    token = await oauth.github.authorize_access_token(request)
    resp = await oauth.github.get("user", token=token)
    github_user = resp.json()

    username = github_user.get("login")
    email = github_user.get("email") or f"{username}@github.com"

    async with AsyncSessionLocal() as session:
        # User suchen oder anlegen
        result = await session.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()

        if not user:
            user = User(username=username, email=email, is_active=True)
            session.add(user)
            await session.commit()
            await session.refresh(user)

        # Session speichern
        request.session["user_id"] = user.id
        request.session["username"] = user.username

    return RedirectResponse(url=f"/dashboard/{user.id}")

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")
