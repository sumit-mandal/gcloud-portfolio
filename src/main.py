"""Travel diary FastAPI app with SQLite-backed admin CMS."""

from __future__ import annotations

import hashlib
import os
import secrets
import sqlite3
import uuid
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
load_dotenv(ROOT_DIR / ".env")

UPLOAD_FOLDER = BASE_DIR / "static" / "uploads"
DB_PATH = BASE_DIR / "portfolio.db"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

SECRET_KEY = os.environ.get("SECRET_KEY", secrets.token_hex(32))
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS_HASH = hashlib.sha256(
    os.environ.get("ADMIN_PASS", "admin123").encode()
).hexdigest()

app = FastAPI(title="Rerouted")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, max_age=60 * 60 * 12)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def seed_data(conn):
    entries = [
        ("Kashmir", "Kashmir was one of the best places I've been into. I went there in mid decembers witnessed snowfall over there. Phalgam, gulmarg, doodhpathri and srinagar were one of the few places where I paid visit.", ["photo1.jpg"]),
        ("Jodhpur", "Jodhpur also known as blue city was really mesmerizing, visited there during monsoon. The sunset was really amazing at jodhpur. The place is really peacefull. The place has rich history.", ["photo2.jpg"]),
        ("Amritsar", "Amritsar was an incredible experience, offering rich history and beautiful sights. The Golden Temple and local culture left a lasting impression.", ["photo3.jpg", "photo4.jpg"]),
        ("Snowy, Milo and Buki", "Three stray cats came into our lives, filling our home with immense joy and love. Though their time with us was heartbreakingly short, they brought us more happiness than we ever imagined. Sadly, illness took them before they could even reach one year, despite our best efforts to save them. Their love will remain in our hearts forever.", ["photo5.jpg"]),
        ("DIU", "The trip to Diu was a refreshing getaway, filled with scenic views and tranquil beaches. The blend of culture and nature made for a memorable experience.", ["photo6.jpg"]),
        ("Mumbai", "The city of dreams has a lot to offer. The place is a perfect combination of Hustle-Bustle and peace.", ["photo7.jpg"]),
        ("Goa", "Goa's beaches and vibrant nightlife made for an unforgettable trip. The mix of relaxation and adventure was perfect.", ["photo8.jpg", "photo9.jpg"]),
        ("Mussoorie", "The queen of hills Mussoorie is not just beautiful but the air is really serene, witnessed amazing rainbow at george everest peak. Did 2 hours of hiking to reach the hill top, and it was really worth it.", ["photo10.jpg"]),
        ("Jaisalmer", "Got a chance to stay at the fort in Jaisalmer, this place is one of my favorites, serene breeze, warm deserts, delicious foods and most importantly great hospitality by the people. I did spend one night under open stars in the sand dunes, and the Place was no less than comfort.", ["photo12.jpg"]),
        ("Jaipur", "The pink city has a lots of amazing places with lots and lots of forts and amazing food. The place is a perfect mix of rich heritage, preserved culture and modern lifestyle. Visited nargarh fort, amer fort and jaigarh fort. Hawa mahal and pink city are must go place for any one who comes here and I was no exception.", ["photo13.jpg"]),
    ]
    for i, (title, desc, photos) in enumerate(entries):
        cursor = conn.execute(
            "INSERT INTO sections (title, description, display_order) VALUES (?, ?, ?)",
            (title, desc, i),
        )
        section_id = cursor.lastrowid
        for photo in photos:
            conn.execute(
                "INSERT INTO images (section_id, filename) VALUES (?, ?)",
                (section_id, photo),
            )
    conn.commit()


def init_db():
    conn = get_db()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            display_order INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            section_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            FOREIGN KEY (section_id) REFERENCES sections(id) ON DELETE CASCADE
        );
        """
    )
    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM sections").fetchone()[0]
    if count == 0:
        seed_data(conn)
    conn.close()


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_image_url(filename: str) -> str:
    if (UPLOAD_FOLDER / filename).exists():
        return f"/static/uploads/{filename}"
    return f"/static/images/{filename}"


def load_sections():
    conn = get_db()
    sections = conn.execute(
        "SELECT * FROM sections ORDER BY display_order DESC, id DESC"
    ).fetchall()
    result = []
    for section in sections:
        images = conn.execute(
            "SELECT * FROM images WHERE section_id = ?", (section["id"],)
        ).fetchall()
        result.append(
            {
                "id": section["id"],
                "title": section["title"],
                "description": section["description"],
                "images": [
                    {
                        "id": img["id"],
                        "url": get_image_url(img["filename"]),
                        "filename": img["filename"],
                    }
                    for img in images
                ],
            }
        )
    conn.close()
    return result


def is_admin(request: Request) -> bool:
    return bool(request.session.get("admin"))


def require_admin_api(request: Request) -> bool:
    if not is_admin(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True


async def save_uploads(files: list[UploadFile], conn, section_id: int) -> list[dict]:
    uploaded = []
    for file in files:
        if not file or not file.filename or not allowed_file(file.filename):
            continue
        ext = file.filename.rsplit(".", 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        dest = UPLOAD_FOLDER / filename
        content = await file.read()
        dest.write_bytes(content)
        conn.execute(
            "INSERT INTO images (section_id, filename) VALUES (?, ?)",
            (section_id, filename),
        )
        img_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        uploaded.append(
            {"id": img_id, "url": f"/static/uploads/{filename}", "filename": filename}
        )
    return uploaded


# ── Public ──


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {"sections": load_sections()},
    )


# ── Admin auth ──


@app.api_route("/admin/login", methods=["GET", "POST"], response_class=HTMLResponse)
async def admin_login(request: Request):
    if is_admin(request):
        return RedirectResponse(url="/admin", status_code=303)

    error = None
    if request.method == "POST":
        form = await request.form()
        username = str(form.get("username", ""))
        password = str(form.get("password", ""))
        pass_hash = hashlib.sha256(password.encode()).hexdigest()
        if username == ADMIN_USER and pass_hash == ADMIN_PASS_HASH:
            request.session["admin"] = True
            return RedirectResponse(url="/admin", status_code=303)
        error = "Invalid credentials"

    return templates.TemplateResponse(
        request,
        "admin_login.html",
        {"error": error},
    )


@app.get("/admin/logout")
def admin_logout(request: Request):
    request.session.pop("admin", None)
    return RedirectResponse(url="/", status_code=303)


@app.get("/admin", response_class=HTMLResponse)
def admin_panel(request: Request):
    if not is_admin(request):
        return RedirectResponse(url="/admin/login", status_code=303)
    return templates.TemplateResponse(
        request,
        "admin.html",
        {"sections": load_sections()},
    )


# ── API ──


@app.post("/api/sections")
async def create_section(
    request: Request,
    _: Annotated[bool, Depends(require_admin_api)],
    title: Annotated[str, Form()] = "",
    description: Annotated[str, Form()] = "",
    images: Annotated[list[UploadFile] | None, File()] = None,
):
    title = title.strip()
    description = description.strip()
    if not title or not description:
        return JSONResponse(
            {"error": "Title and description are required"}, status_code=400
        )

    conn = get_db()
    max_order = conn.execute(
        "SELECT COALESCE(MAX(display_order), -1) FROM sections"
    ).fetchone()[0]
    cursor = conn.execute(
        "INSERT INTO sections (title, description, display_order) VALUES (?, ?, ?)",
        (title, description, max_order + 1),
    )
    section_id = cursor.lastrowid
    uploaded_images = await save_uploads(images or [], conn, section_id)
    conn.commit()
    conn.close()
    return JSONResponse(
        {
            "id": section_id,
            "title": title,
            "description": description,
            "images": uploaded_images,
        },
        status_code=201,
    )


@app.put("/api/sections/{section_id}")
async def update_section(
    section_id: int,
    request: Request,
    _: Annotated[bool, Depends(require_admin_api)],
    title: Annotated[str, Form()] = "",
    description: Annotated[str, Form()] = "",
    images: Annotated[list[UploadFile] | None, File()] = None,
):
    title = title.strip()
    description = description.strip()
    if not title or not description:
        return JSONResponse(
            {"error": "Title and description are required"}, status_code=400
        )

    conn = get_db()
    section = conn.execute(
        "SELECT * FROM sections WHERE id = ?", (section_id,)
    ).fetchone()
    if not section:
        conn.close()
        return JSONResponse({"error": "Section not found"}, status_code=404)

    conn.execute(
        "UPDATE sections SET title = ?, description = ? WHERE id = ?",
        (title, description, section_id),
    )
    await save_uploads(images or [], conn, section_id)
    conn.commit()
    all_images = conn.execute(
        "SELECT * FROM images WHERE section_id = ?", (section_id,)
    ).fetchall()
    conn.close()

    return {
        "id": section_id,
        "title": title,
        "description": description,
        "images": [
            {
                "id": img["id"],
                "url": get_image_url(img["filename"]),
                "filename": img["filename"],
            }
            for img in all_images
        ],
    }


@app.delete("/api/sections/{section_id}")
def delete_section(
    section_id: int,
    request: Request,
    _: Annotated[bool, Depends(require_admin_api)],
):
    conn = get_db()
    section = conn.execute(
        "SELECT * FROM sections WHERE id = ?", (section_id,)
    ).fetchone()
    if not section:
        conn.close()
        return JSONResponse({"error": "Section not found"}, status_code=404)

    images = conn.execute(
        "SELECT * FROM images WHERE section_id = ?", (section_id,)
    ).fetchall()
    for img in images:
        filepath = UPLOAD_FOLDER / img["filename"]
        if filepath.exists():
            filepath.unlink()

    conn.execute("DELETE FROM sections WHERE id = ?", (section_id,))
    conn.commit()
    conn.close()
    return {"message": "Section deleted"}


@app.delete("/api/images/{image_id}")
def delete_image(
    image_id: int,
    request: Request,
    _: Annotated[bool, Depends(require_admin_api)],
):
    conn = get_db()
    image = conn.execute("SELECT * FROM images WHERE id = ?", (image_id,)).fetchone()
    if not image:
        conn.close()
        return JSONResponse({"error": "Image not found"}, status_code=404)

    filepath = UPLOAD_FOLDER / image["filename"]
    if filepath.exists():
        filepath.unlink()

    conn.execute("DELETE FROM images WHERE id = ?", (image_id,))
    conn.commit()
    conn.close()
    return {"message": "Image deleted"}


init_db()
