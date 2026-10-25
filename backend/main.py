"""Offline-first prototype: validated actions and versioned SQLite save slot."""
import json
import os
import sqlite3
from copy import deepcopy
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from backend.world import migrate, apply, advance, entry
from backend.story import available, resolve

LOCATIONS = {"home": "住所", "office": "辦公室", "cafe": "咖啡廳", "restaurant": "餐廳"}
INITIAL = {"version": 1, "minutes": 540, "cash": 100000, "energy": 100,
           "location": "home", "company": None, "events": ["歡迎來到你的第二人生。"]}

class Character(BaseModel):
    name: str = Field(default="新市民", min_length=1, max_length=24, pattern=r".*\S.*")
    age: int = Field(default=24, ge=18, le=100)
    pronouns: Literal["不指定", "她", "他", "TA"] = "不指定"
    background: Literal["自由工作者", "上班族", "創業新手"] = "自由工作者"
    appearance: str = Field(default="日常休閒風", max_length=120)
    interest: Literal["閱讀", "科技", "美食", "藝術"] = "閱讀"

class StoryChoice(BaseModel):
    story_id: str
    choice: int = Field(ge=0, le=1)

class Action(BaseModel):
    kind: Literal["travel", "rest", "wait", "found_company", "chat", "invite", "hire", "develop", "eat", "shop", "leisure", "confess", "market", "select_product"]
    product_type: Literal["tool", "game"] = "tool"
    npc_id: str | None = None
    location: Literal["home", "office", "cafe", "restaurant"] | None = None


def create_app(db_path=None):
    app = FastAPI(title="第二人生 Prototype", version="0.1.0")
    path = Path(db_path or os.getenv("GAME_DB_PATH", ".local/game.sqlite3"))
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE IF NOT EXISTS saves (slot INTEGER PRIMARY KEY, data TEXT NOT NULL)")
    app.state.world = None

    def world():
        if app.state.world is None:
            raise HTTPException(409, "請先開始新遊戲或讀取存檔。")
        return app.state.world

    @app.get("/health")
    def health():
        return {"status": "ok", "offline": True}

    @app.post("/game/new")
    def new(character: Character = Character()):
        app.state.world = migrate(INITIAL)
        app.state.world["player"] = character.model_dump()
        return world()

    @app.get("/game")
    def state():
        return world()

    @app.post("/game/action")
    def action(body: Action):
        w = deepcopy(world())
        if body.kind == "travel":
            if body.location is None:
                raise HTTPException(422, "請選擇地點。")
            if w["energy"] < 5:
                raise HTTPException(409, "精力不足，請先休息。")
            w["location"] = body.location
            advance(w, 30)
            w["energy"] -= 5
            event = "抵達" + LOCATIONS[body.location]
        elif body.kind == "rest":
            if w["location"] != "home":
                raise HTTPException(409, "請回住所休息。")
            advance(w, 120)
            w["energy"] = min(100, w["energy"] + 30)
            event = "休息兩小時，恢復精力。"
        elif body.kind == "found_company":
            if w["company"] or w["cash"] < 10000:
                raise HTTPException(409, "已成立公司或資金不足。")
            w["cash"] -= 10000
            w["company"] = {"name": "新生數位工作室", "capital": 10000, "employees": [], "products": 0, "progress": 0, "last_settled": w["minutes"] // 1440}
            entry(w, "player", -10000, "創業投資")
            entry(w, "company", 10000, "創業資本")
            w = migrate(w)
            event = "投入 10,000 元成立數位工作室。"
        elif body.kind == "wait":
            advance(w, 60)
            event = "時間前進一小時。"
        else:
            try:
                event = apply(w, body)
            except ValueError as exc:
                raise HTTPException(409, str(exc)) from exc
        w["events"] = (w["events"] + [event])[-50:]
        app.state.world = w
        return w

    @app.get("/game/stories")
    def stories():
        return {"stories": available(world())}

    @app.post("/game/story")
    def story(body: StoryChoice):
        candidate = deepcopy(world())
        try:
            event = resolve(candidate, body.story_id, body.choice)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        candidate["events"] = (candidate["events"] + [event])[-50:]
        app.state.world = candidate
        return candidate

    @app.post("/game/save")
    def save(slot: int = Query(default=1, ge=1, le=3)):
        data = json.dumps(world(), ensure_ascii=False)
        with sqlite3.connect(path) as db:
            db.execute("INSERT OR REPLACE INTO saves VALUES (?, ?)", (slot, data))
        return {"saved": True}

    @app.get("/game/saves")
    def saves():
        with sqlite3.connect(path) as db:
            rows = db.execute("SELECT slot, data FROM saves ORDER BY slot").fetchall()
        return {"slots": [{"slot": slot, "name": json.loads(data).get("player", {}).get("name", "舊存檔"), "minutes": json.loads(data)["minutes"]} for slot, data in rows]}

    @app.post("/game/load")
    def load(slot: int = Query(default=1, ge=1, le=3)):
        with sqlite3.connect(path) as db:
            row = db.execute("SELECT data FROM saves WHERE slot=?", (slot,)).fetchone()
        if not row:
            raise HTTPException(404, "尚無存檔，請先開始新遊戲。")
        value = json.loads(row[0])
        try:
            app.state.world = migrate(value)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        return world()

    root = Path(__file__).resolve().parents[1]
    app.mount("/web", StaticFiles(directory=root / "web"), name="web")
    app.mount("/assets", StaticFiles(directory=root / "client/assets"), name="assets")

    @app.get("/", include_in_schema=False)
    def browser_game():
        return FileResponse(root / "web/index.html")

    return app

app = create_app()
