import json
import os
from pathlib import Path
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
DATA_FILE = BASE_DIR.parent / "data" / "users.json"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Mount static files if directory exists
static_dir = BASE_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


def load_users():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []


def save_users(users):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(users, f, indent=2)


# ─── Routes ──────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def root():
    return RedirectResponse(url="/login")


@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login", response_class=HTMLResponse)
async def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    # No real auth — accept any credentials
    return RedirectResponse(url="/users", status_code=303)


@app.get("/users", response_class=HTMLResponse)
async def users_list(request: Request, message: str = ""):
    users = load_users()
    return templates.TemplateResponse(
        "users.html", {"request": request, "users": users, "message": message}
    )


@app.get("/create-user", response_class=HTMLResponse)
async def create_user_get(request: Request):
    return templates.TemplateResponse("create_user.html", {"request": request, "message": ""})


@app.post("/create-user", response_class=HTMLResponse)
async def create_user_post(
    request: Request,
    email: str = Form(...),
    full_name: str = Form(...),
):
    users = load_users()
    # Check for duplicate
    for u in users:
        if u["email"] == email:
            return templates.TemplateResponse(
                "create_user.html",
                {"request": request, "message": f"User {email} already exists."},
            )
    users.append({"email": email, "full_name": full_name, "password": "Welcome@123"})
    save_users(users)
    return templates.TemplateResponse(
        "create_user.html",
        {"request": request, "message": f"User {email} created successfully."},
    )


@app.post("/reset-password", response_class=HTMLResponse)
async def reset_password(
    request: Request,
    email: str = Form(...),
):
    users = load_users()
    found = False
    for u in users:
        if u["email"] == email:
            u["password"] = "Reset@123"
            found = True
            break
    if found:
        save_users(users)
        message = f"Password reset for {email}. New password: Reset@123"
    else:
        message = f"User {email} not found."
    users = load_users()
    return templates.TemplateResponse(
        "users.html", {"request": request, "users": users, "message": message}
    )
