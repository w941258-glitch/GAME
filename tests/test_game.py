from fastapi.testclient import TestClient
from backend.main import create_app


def test_roundtrip_and_restart(tmp_path):
    path = tmp_path / "game.sqlite3"
    client = TestClient(create_app(path))
    assert client.get("/health").json()["offline"]
    assert client.get("/game").status_code == 409
    assert client.post("/game/load").status_code == 404
    state = client.post("/game/new").json()
    assert state["cash"] == 100000
    for location in ["office", "cafe", "restaurant", "home"]:
        response = client.post("/game/action", json={"kind": "travel", "location": location})
        assert response.status_code == 200
        assert response.json()["location"] == location
    assert response.json()["energy"] == 80
    assert response.json()["minutes"] == 660
    assert client.post("/game/action", json={"kind": "rest"}).json()["energy"] == 100
    company = client.post("/game/action", json={"kind": "found_company"}).json()
    assert company["cash"] + company["company"]["capital"] == 100000
    assert client.post("/game/action", json={"kind": "found_company"}).status_code == 409
    assert client.post("/game/save").json()["saved"]
    restored = TestClient(create_app(path)).post("/game/load").json()
    assert restored == company


def test_rejected_actions_do_not_change_world(tmp_path):
    client = TestClient(create_app(tmp_path / "save.sqlite3"))
    client.post("/game/new")
    for payload in [{"kind": "unknown"}, {"kind": "travel"}, {"kind": "travel", "location": "invalid"}]:
        before = client.get("/game").json()
        assert client.post("/game/action", json=payload).status_code == 422
        assert client.get("/game").json() == before
    client.post("/game/action", json={"kind": "travel", "location": "office"})
    assert client.post("/game/action", json={"kind": "rest"}).status_code == 409
    for _ in range(19):
        assert client.post("/game/action", json={"kind": "travel", "location": "home"}).status_code == 200
    before = client.get("/game").json()
    assert client.post("/game/action", json={"kind": "travel", "location": "cafe"}).status_code == 409
    assert client.get("/game").json() == before


def test_character_validation(tmp_path):
    client = TestClient(create_app(tmp_path / "game.db"))
    for body in [{"age": 17}, {"name": "  "}, {"interest": "invalid"}]:
        assert client.post("/game/new", json=body).status_code == 422
    state = client.post("/game/new", json={"name": "小雨", "age": 28, "interest": "科技"}).json()
    assert state["player"]["name"] == "小雨"
    assert len(state["npcs"]) == 8
    assert all(n["age"] >= 18 for n in state["npcs"])


def test_social_memories_boundaries_and_schedule(tmp_path):
    client = TestClient(create_app(tmp_path / "game.db"))
    client.post("/game/new")
    def act(kind, **kwargs):
        return client.post("/game/action", json={"kind": kind, **kwargs})
    assert act("chat", npc_id="lin").status_code == 409
    act("travel", location="office")
    refused = act("invite", npc_id="lin").json()
    assert "不想約會" in refused["events"][-1]
    before = client.get("/game").json()
    assert act("invite", npc_id="lin").status_code == 409
    assert client.get("/game").json() == before
    for _ in range(3):
        assert act("chat", npc_id="lin").status_code == 200
        assert act("chat", npc_id="lin").status_code == 409
        act("wait")
    npc = client.get("/game").json()["npcs"][0]
    assert npc["trust"] == 15 and len(npc["memories"]) == 4
    for _ in range(24):
        act("wait")
    # Wait to a public location shared with the target, respecting the schedule.
    state = client.get("/game").json()
    act("travel", location=state["npcs"][0]["location"])
    accepted = act("invite", npc_id="lin")
    assert accepted.status_code == 200
    assert accepted.json()["npcs"][0]["dates"] == 1
    assert accepted.json()["cash"] == 99700
    client.post("/game/save")
    restored = TestClient(create_app(tmp_path / "game.db")).post("/game/load").json()
    assert restored == accepted.json()


def test_company_day_and_ledger(tmp_path):
    client = TestClient(create_app(tmp_path / "game.db"))
    client.post("/game/new")
    def act(kind, **kwargs):
        return client.post("/game/action", json={"kind": kind, **kwargs})
    act("found_company")
    before = client.get("/game").json()
    assert act("hire", npc_id="chen").status_code == 409
    assert client.get("/game").json() == before
    act("travel", location="office")
    assert act("develop").status_code == 409
    assert act("hire", npc_id="chen").status_code == 200
    assert act("hire", npc_id="chen").status_code == 409
    for _ in range(2):
        assert act("develop").status_code == 200
    assert client.get("/game").json()["company"]["products"] == 1
    while client.get("/game").json()["minutes"] < 1440:
        act("wait")
    state = client.get("/game").json()
    assert state["company"]["capital"] == 8900
    assert state["cash"] == 90000
    assert sum(r["amount"] for r in state["ledger"] if r["account"] == "company") == 8900
    assert 100000 + sum(r["amount"] for r in state["ledger"] if r["account"] == "player") == state["cash"]
    assert any("營業結算" in event for event in state["events"])


def test_v1_save_migration(tmp_path):
    import json
    import sqlite3
    from backend.main import INITIAL
    path = tmp_path / "old.db"
    client = TestClient(create_app(path))
    old = dict(INITIAL, company={"name": "舊公司", "capital": 10000})
    with sqlite3.connect(path) as db:
        db.execute("INSERT INTO saves VALUES (1, ?)", (json.dumps(old),))
    state = client.post("/game/load").json()
    assert state["version"] == 3
    assert state["company"]["employees"] == []
    assert len(state["npcs"]) == 8
    assert state["cash"] == old["cash"]


def test_life_and_three_slots(tmp_path):
    path = tmp_path / "game.db"
    client = TestClient(create_app(path))
    client.post("/game/new", json={"name": "第一人生"})
    def act(kind, **args):
        return client.post("/game/action", json={"kind": kind, **args})
    assert act("eat").status_code == 409
    act("travel", location="cafe")
    assert act("eat").json()["hunger"] == 0
    assert act("shop").json()["inventory"] == ["城市明信片"]
    state = act("leisure").json()
    assert state["mood"] == 90
    for slot in [1, 2, 3]:
        assert client.post(f"/game/save?slot={slot}").status_code == 200
    assert len(client.get("/game/saves").json()["slots"]) == 3
    client.post("/game/new", json={"name": "第二人生"})
    client.post("/game/save?slot=2")
    restarted = TestClient(create_app(path))
    assert restarted.post("/game/load?slot=1").json() == state
    assert restarted.post("/game/load?slot=2").json()["player"]["name"] == "第二人生"
    for slot in [0, 4, -1]:
        assert client.post(f"/game/save?slot={slot}").status_code == 422
        assert client.post(f"/game/load?slot={slot}").status_code == 422


def test_market_products_and_atomic_failure(tmp_path):
    client = TestClient(create_app(tmp_path / "market.db"))
    client.post("/game/new")
    def act(kind, **args):
        return client.post("/game/action", json={"kind": kind, **args})
    act("found_company")
    act("travel", location="office")
    act("hire", npc_id="chen")
    assert act("market").status_code == 409
    act("select_product", product_type="game")
    act("develop")
    before = client.get("/game").json()
    assert act("select_product", product_type="tool").status_code == 409
    assert client.get("/game").json() == before
    act("develop")
    assert act("market").json()["company"]["marketing"] == 20
    while client.get("/game").json()["minutes"] < 1440:
        act("wait")
    state = client.get("/game").json()
    assert state["company"]["catalog"] == {"tool": 0, "game": 1}
    assert state["company"]["capital"] == 8460  # 10000 - 1000 - 1600 - 800 + 2160 - 300
    assert state["company"]["marketing"] == 10
    assert sum(r["amount"] for r in state["ledger"] if r["account"] == "company") == 8460


def test_relationship_milestones_and_refusal(tmp_path):
    from backend.world import migrate, apply
    from backend.main import INITIAL, Action
    state = migrate(INITIAL)
    state["location"] = "office"
    npc = state["npcs"][0]
    assert "還沒準備好" in apply(state, Action(kind="confess", npc_id="lin"))
    assert npc["stage"] == "初識"
    state["minutes"] += 1440
    npc["trust"] = 30
    npc["dates"] = 2
    assert "確認了關係" in apply(state, Action(kind="confess", npc_id="lin"))
    assert npc["stage"] == "交往"
    assert npc["milestones"] == ["確認關係"]
    assert len(npc["memories"]) == 2


def test_story_choices_persistence_and_repeat_protection(tmp_path):
    path = tmp_path / "stories.db"
    client = TestClient(create_app(path))
    client.post("/game/new")
    stories = client.get("/game/stories").json()["stories"]
    assert [s["id"] for s in stories] == ["neighbor"]
    before = client.get("/game").json()
    assert client.post("/game/story", json={"story_id": "client", "choice": 0}).status_code == 409
    assert client.post("/game/story", json={"story_id": "neighbor", "choice": 2}).status_code == 422
    assert client.get("/game").json() == before
    result = client.post("/game/story", json={"story_id": "neighbor", "choice": 0}).json()
    assert result["mood"] == before["mood"] + 8
    assert result["minutes"] == before["minutes"] + 30
    assert client.post("/game/story", json={"story_id": "neighbor", "choice": 0}).status_code == 409
    client.post("/game/save?slot=3")
    loaded = TestClient(create_app(path)).post("/game/load?slot=3").json()
    assert loaded == result
    assert loaded["story_done"] == ["neighbor"]


def test_company_story_accounts_and_decline(tmp_path):
    client = TestClient(create_app(tmp_path / "stories.db"))
    client.post("/game/new")
    def act(kind, **args):
        return client.post("/game/action", json={"kind": kind, **args})
    act("found_company")
    act("travel", location="office")
    act("hire", npc_id="chen")
    act("develop")
    before = act("develop").json()
    result = client.post("/game/story", json={"story_id": "client", "choice": 0}).json()
    assert result["company"]["capital"] == before["company"]["capital"] + 2000
    assert result["ledger"][-1]["amount"] == 2000
    declined = client.post("/game/story", json={"story_id": "team", "choice": 1}).json()
    assert declined["cash"] == result["cash"]
    assert declined["company"]["capital"] == result["company"]["capital"]
    assert declined["story_done"] == ["client", "team"]
