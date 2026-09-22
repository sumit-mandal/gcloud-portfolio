"""Portfolio FastAPI app with JSON-backed admin CMS."""

from __future__ import annotations

import os
import secrets
import sys
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from content_store import (
    SECTION_THEMES,
    enabled_sections,
    get_section,
    load_content,
    save_content,
    unique_section_id,
)

load_dotenv(BASE_DIR.parent / ".env")

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "change-me")
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_hex(32))

app = FastAPI(title="Sumit Mandal Portfolio")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, max_age=60 * 60 * 12)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

IMAGES_DIR = BASE_DIR / "static" / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


def is_authenticated(request: Request) -> bool:
    return bool(request.session.get("authenticated"))


def require_admin(request: Request) -> bool:
    if not is_authenticated(request):
        raise HTTPException(
            status_code=303,
            detail="Login required",
            headers={"Location": "/admin/login"},
        )
    return True


def parse_lines(raw: str) -> list[str]:
    return [line.strip() for line in raw.splitlines() if line.strip()]


def redirect_admin(anchor: str = "") -> RedirectResponse:
    url = "/admin"
    if anchor:
        url = f"/admin#{anchor}"
    return RedirectResponse(url=url, status_code=303)


# ---------- Public ----------


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    content = load_content()
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "content": content,
            "sections": enabled_sections(content),
        },
    )


# ---------- Auth ----------


@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    if is_authenticated(request):
        return RedirectResponse(url="/admin", status_code=303)
    return templates.TemplateResponse(
        request,
        "admin/login.html",
        {"error": None},
    )


@app.post("/admin/login")
async def admin_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    if secrets.compare_digest(username, ADMIN_USERNAME) and secrets.compare_digest(
        password, ADMIN_PASSWORD
    ):
        request.session["authenticated"] = True
        return RedirectResponse(url="/admin", status_code=303)
    return templates.TemplateResponse(
        request,
        "admin/login.html",
        {"error": "Invalid username or password."},
        status_code=401,
    )


@app.post("/admin/logout")
async def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/admin/login", status_code=303)


# ---------- Admin UI ----------


@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    if not is_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=303)
    content = load_content()
    return templates.TemplateResponse(
        request,
        "admin/dashboard.html",
        {
            "content": content,
            "section_themes": SECTION_THEMES,
            "flash": request.session.pop("flash", None),
        },
    )


def flash(request: Request, message: str) -> None:
    request.session["flash"] = message


# ---------- Home / site ----------


@app.post("/admin/home")
async def update_home(
    request: Request,
    name_line_1: str = Form(...),
    name_line_2: str = Form(...),
    role_sticker: str = Form(...),
    tagline: str = Form(...),
    email: str = Form(...),
    cta_text: str = Form(...),
    linkedin: str = Form(""),
    github: str = Form(""),
    whatsapp: str = Form(""),
    badge_1: str = Form(""),
    badge_2: str = Form(""),
    marquee: str = Form(""),
    site_title: str = Form(...),
    footer: str = Form(...),
    _: None = Depends(require_admin),
):
    content = load_content()
    content["home"].update(
        {
            "name_line_1": name_line_1.strip(),
            "name_line_2": name_line_2.strip(),
            "role_sticker": role_sticker.strip(),
            "tagline": tagline.strip(),
            "email": email.strip(),
            "cta_text": cta_text.strip(),
            "linkedin": linkedin.strip(),
            "github": github.strip(),
            "whatsapp": whatsapp.strip(),
            "badge_1": badge_1.strip(),
            "badge_2": badge_2.strip(),
            "marquee": marquee.strip(),
        }
    )
    content["site"]["title"] = site_title.strip()
    content["site"]["footer"] = footer.strip()
    save_content(content)
    flash(request, "Home & site settings saved.")
    return redirect_admin("home")


@app.post("/admin/photo")
async def update_photo(
    request: Request,
    photo: UploadFile = File(...),
    _: None = Depends(require_admin),
):
    content_type = photo.content_type or ""
    ext = ALLOWED_IMAGE_TYPES.get(content_type)
    if not ext:
        flash(request, "Unsupported image type. Use JPG, PNG, WEBP, or GIF.")
        return redirect_admin("home")

    data = await photo.read()
    if not data:
        flash(request, "Empty upload.")
        return redirect_admin("home")

    filename = f"profile{ext}"
    destination = IMAGES_DIR / filename
    destination.write_bytes(data)

    # Remove other profile.* variants so the active file is clear
    for old in IMAGES_DIR.glob("profile.*"):
        if old.name != filename:
            old.unlink(missing_ok=True)

    content = load_content()
    content["home"]["profile_image"] = f"/static/images/{filename}?v={secrets.token_hex(4)}"
    save_content(content)
    flash(request, "Profile photo updated.")
    return redirect_admin("home")


# ---------- Sections meta / create / delete / reorder ----------


@app.post("/admin/sections/create")
async def create_section(
    request: Request,
    title: str = Form(...),
    nav_label: str = Form(...),
    label: str = Form(""),
    section_type: str = Form("custom"),
    theme: str = Form(""),
    body: str = Form(""),
    _: None = Depends(require_admin),
):
    content = load_content()
    section_type = section_type if section_type in SECTION_THEMES else "custom"
    section_id = unique_section_id(content, nav_label or title)
    theme_class = theme.strip() or SECTION_THEMES[section_type]

    new_section: dict[str, Any] = {
        "id": section_id,
        "type": section_type,
        "enabled": True,
        "nav_label": nav_label.strip() or title.strip(),
        "label": label.strip() or f"{len(content['sections']) + 1:02d} // NEW",
        "title": title.strip(),
        "theme": theme_class,
        "entries": [],
    }

    if section_type == "custom":
        new_section["body"] = body.strip()
    elif section_type == "skills":
        new_section["entries"] = parse_lines(body) if body.strip() else []
    elif section_type == "achievements" and body.strip():
        new_section["entries"] = [{"badge": "NEW", "text": body.strip()}]

    content["sections"].append(new_section)
    save_content(content)
    flash(request, f"Section “{new_section['title']}” created.")
    return redirect_admin(f"section-{section_id}")


@app.post("/admin/sections/{section_id}/meta")
async def update_section_meta(
    request: Request,
    section_id: str,
    title: str = Form(...),
    nav_label: str = Form(...),
    label: str = Form(""),
    theme: str = Form(""),
    enabled: str = Form("off"),
    body: str = Form(""),
    _: None = Depends(require_admin),
):
    content = load_content()
    section = get_section(content, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    section["title"] = title.strip()
    section["nav_label"] = nav_label.strip()
    section["label"] = label.strip()
    if theme.strip():
        section["theme"] = theme.strip()
    section["enabled"] = enabled == "on"
    if section.get("type") == "custom":
        section["body"] = body

    save_content(content)
    flash(request, f"Section “{section['title']}” updated.")
    return redirect_admin(f"section-{section_id}")


@app.post("/admin/sections/{section_id}/delete")
async def delete_section(
    request: Request,
    section_id: str,
    _: None = Depends(require_admin),
):
    content = load_content()
    before = len(content["sections"])
    content["sections"] = [s for s in content["sections"] if s.get("id") != section_id]
    if len(content["sections"]) == before:
        raise HTTPException(status_code=404, detail="Section not found")
    save_content(content)
    flash(request, "Section deleted.")
    return redirect_admin("sections")


@app.post("/admin/sections/reorder")
async def reorder_sections(
    request: Request,
    order: str = Form(...),
    _: None = Depends(require_admin),
):
    content = load_content()
    ids = [part.strip() for part in order.split(",") if part.strip()]
    by_id = {s["id"]: s for s in content["sections"]}
    reordered = [by_id[i] for i in ids if i in by_id]
    leftover = [s for s in content["sections"] if s["id"] not in ids]
    content["sections"] = reordered + leftover
    save_content(content)
    flash(request, "Section order saved.")
    return redirect_admin("sections")


# ---------- Skills ----------


@app.post("/admin/sections/{section_id}/skills")
async def update_skills(
    request: Request,
    section_id: str,
    skills: str = Form(""),
    _: None = Depends(require_admin),
):
    content = load_content()
    section = get_section(content, section_id)
    if not section or section.get("type") != "skills":
        raise HTTPException(status_code=404, detail="Skills section not found")
    section["entries"] = parse_lines(skills)
    save_content(content)
    flash(request, "Skills updated.")
    return redirect_admin(f"section-{section_id}")


# ---------- Experience ----------


@app.post("/admin/sections/{section_id}/experience/add")
async def add_experience(
    request: Request,
    section_id: str,
    date: str = Form(...),
    tag: str = Form(""),
    title: str = Form(...),
    bullets: str = Form(""),
    _: None = Depends(require_admin),
):
    content = load_content()
    section = get_section(content, section_id)
    if not section or section.get("type") != "experience":
        raise HTTPException(status_code=404, detail="Experience section not found")
    section.setdefault("entries", []).insert(
        0,
        {
            "date": date.strip(),
            "tag": tag.strip(),
            "title": title.strip(),
            "bullets": parse_lines(bullets),
        },
    )
    save_content(content)
    flash(request, "Experience entry added.")
    return redirect_admin(f"section-{section_id}")


@app.post("/admin/sections/{section_id}/experience/{index}/update")
async def update_experience(
    request: Request,
    section_id: str,
    index: int,
    date: str = Form(...),
    tag: str = Form(""),
    title: str = Form(...),
    bullets: str = Form(""),
    _: None = Depends(require_admin),
):
    content = load_content()
    section = get_section(content, section_id)
    if not section or section.get("type") != "experience":
        raise HTTPException(status_code=404, detail="Experience section not found")
    items = section.get("entries", [])
    if index < 0 or index >= len(items):
        raise HTTPException(status_code=404, detail="Entry not found")
    items[index] = {
        "date": date.strip(),
        "tag": tag.strip(),
        "title": title.strip(),
        "bullets": parse_lines(bullets),
    }
    save_content(content)
    flash(request, "Experience entry updated.")
    return redirect_admin(f"section-{section_id}")


@app.post("/admin/sections/{section_id}/experience/{index}/delete")
async def delete_experience(
    request: Request,
    section_id: str,
    index: int,
    _: None = Depends(require_admin),
):
    content = load_content()
    section = get_section(content, section_id)
    if not section or section.get("type") != "experience":
        raise HTTPException(status_code=404, detail="Experience section not found")
    items = section.get("entries", [])
    if index < 0 or index >= len(items):
        raise HTTPException(status_code=404, detail="Entry not found")
    items.pop(index)
    save_content(content)
    flash(request, "Experience entry deleted.")
    return redirect_admin(f"section-{section_id}")


# ---------- Education ----------


@app.post("/admin/sections/{section_id}/education/add")
async def add_education(
    request: Request,
    section_id: str,
    year: str = Form(...),
    title: str = Form(...),
    subtitle: str = Form(""),
    alt: str = Form("off"),
    _: None = Depends(require_admin),
):
    content = load_content()
    section = get_section(content, section_id)
    if not section or section.get("type") != "education":
        raise HTTPException(status_code=404, detail="Education section not found")
    section.setdefault("entries", []).append(
        {
            "year": year.strip(),
            "title": title.strip(),
            "subtitle": subtitle.strip(),
            "alt": alt == "on",
        }
    )
    save_content(content)
    flash(request, "Education entry added.")
    return redirect_admin(f"section-{section_id}")


@app.post("/admin/sections/{section_id}/education/{index}/update")
async def update_education(
    request: Request,
    section_id: str,
    index: int,
    year: str = Form(...),
    title: str = Form(...),
    subtitle: str = Form(""),
    alt: str = Form("off"),
    _: None = Depends(require_admin),
):
    content = load_content()
    section = get_section(content, section_id)
    if not section or section.get("type") != "education":
        raise HTTPException(status_code=404, detail="Education section not found")
    items = section.get("entries", [])
    if index < 0 or index >= len(items):
        raise HTTPException(status_code=404, detail="Entry not found")
    items[index] = {
        "year": year.strip(),
        "title": title.strip(),
        "subtitle": subtitle.strip(),
        "alt": alt == "on",
    }
    save_content(content)
    flash(request, "Education entry updated.")
    return redirect_admin(f"section-{section_id}")


@app.post("/admin/sections/{section_id}/education/{index}/delete")
async def delete_education(
    request: Request,
    section_id: str,
    index: int,
    _: None = Depends(require_admin),
):
    content = load_content()
    section = get_section(content, section_id)
    if not section or section.get("type") != "education":
        raise HTTPException(status_code=404, detail="Education section not found")
    items = section.get("entries", [])
    if index < 0 or index >= len(items):
        raise HTTPException(status_code=404, detail="Entry not found")
    items.pop(index)
    save_content(content)
    flash(request, "Education entry deleted.")
    return redirect_admin(f"section-{section_id}")


# ---------- Achievements ----------


@app.post("/admin/sections/{section_id}/achievements/add")
async def add_achievement(
    request: Request,
    section_id: str,
    badge: str = Form(...),
    text: str = Form(...),
    _: None = Depends(require_admin),
):
    content = load_content()
    section = get_section(content, section_id)
    if not section or section.get("type") != "achievements":
        raise HTTPException(status_code=404, detail="Achievements section not found")
    section.setdefault("entries", []).append(
        {"badge": badge.strip(), "text": text.strip()}
    )
    save_content(content)
    flash(request, "Achievement added.")
    return redirect_admin(f"section-{section_id}")


@app.post("/admin/sections/{section_id}/achievements/{index}/update")
async def update_achievement(
    request: Request,
    section_id: str,
    index: int,
    badge: str = Form(...),
    text: str = Form(...),
    _: None = Depends(require_admin),
):
    content = load_content()
    section = get_section(content, section_id)
    if not section or section.get("type") != "achievements":
        raise HTTPException(status_code=404, detail="Achievements section not found")
    items = section.get("entries", [])
    if index < 0 or index >= len(items):
        raise HTTPException(status_code=404, detail="Entry not found")
    items[index] = {"badge": badge.strip(), "text": text.strip()}
    save_content(content)
    flash(request, "Achievement updated.")
    return redirect_admin(f"section-{section_id}")


@app.post("/admin/sections/{section_id}/achievements/{index}/delete")
async def delete_achievement(
    request: Request,
    section_id: str,
    index: int,
    _: None = Depends(require_admin),
):
    content = load_content()
    section = get_section(content, section_id)
    if not section or section.get("type") != "achievements":
        raise HTTPException(status_code=404, detail="Achievements section not found")
    items = section.get("entries", [])
    if index < 0 or index >= len(items):
        raise HTTPException(status_code=404, detail="Entry not found")
    items.pop(index)
    save_content(content)
    flash(request, "Achievement deleted.")
    return redirect_admin(f"section-{section_id}")


@app.get("/api/content")
async def api_content():
    """Public read of content JSON (useful for debugging / future frontends)."""
    return JSONResponse(load_content())
