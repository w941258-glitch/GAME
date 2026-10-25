"""One-shot, choice-driven stories. All effects pass through game rules."""
from backend.world import entry, advance

STORIES = {
    "neighbor": {"title": "生活｜走廊裡的紙箱", "body": "鄰居抱著紙箱，在電梯前停了下來。你有一點空檔，要幫忙嗎？", "choices": ["幫忙搬運（30 分鐘，心情 +8）", "禮貌致意，繼續行程"]},
    "postcard": {"title": "生活｜寄給未來的自己", "body": "你翻出買下的明信片，想起剛搬來城市時的期待。", "choices": ["寫下願望（20 分鐘，心情 +10）", "把它好好收藏"]},
    "book": {"title": "社交｜書頁間的邀請", "body": "林予晴提起街角的閱讀會，想知道你是否願意分享喜歡的一本書。", "choices": ["認真分享（30 分鐘，信任 +5）", "坦白今天想獨處"]},
    "prototype": {"title": "社交｜尚未完成的作品", "body": "周以辰對自己的小作品沒什麼信心，問你願不願意試用。", "choices": ["給出具體回饋（30 分鐘，信任 +5）", "說明現在沒有時間"]},
    "rain": {"title": "戀愛｜雨停之前", "body": "林予晴在窗邊看著雨，輕聲問你願不願意再坐一會兒。", "choices": ["留下來聊天（30 分鐘，信任 +5）", "溫柔道別，下次再見"]},
    "promise": {"title": "戀愛｜週末的約定", "body": "周以辰翻開行事曆，想和你一起安排一段兩人都自在的時間。", "choices": ["一起討論行程（30 分鐘，信任 +5）", "保留自己的週末"]},
    "client": {"title": "公司｜第一份客戶回饋", "body": "一位客戶喜歡你的產品，但希望你為他調整細節。團隊可以接下這張小訂單。", "choices": ["交付調整（120 分鐘、精力 10，公司收入 2,000）", "專注既有產品"]},
    "team": {"title": "公司｜團隊的小小慶祝", "body": "員工提議一起吃點東西，慶祝工作室的第一段旅程。", "choices": ["請客（公司支出 500，心情 +15）", "先向大家表達感謝"]},
}


def available(w):
    c = w.get("company")
    ids = []
    if w["location"] == "home": ids.append("neighbor")
    if w["inventory"]: ids.append("postcard")
    for key, npc_id in [("book", "lin"), ("prototype", "zhou")]:
        npc = next(n for n in w["npcs"] if n["id"] == npc_id)
        if npc["trust"] >= 10 and npc["location"] == w["location"] != "home": ids.append(key)
    for key, npc_id in [("rain", "lin"), ("promise", "zhou")]:
        npc = next(n for n in w["npcs"] if n["id"] == npc_id)
        if npc["dates"] >= 1 and npc["location"] == w["location"] != "home": ids.append(key)
    if c and w["location"] == "office":
        if c["products"]: ids.append("client")
        if c["employees"]: ids.append("team")
    return [{"id": key, **STORIES[key]} for key in ids if key not in w["story_done"]]


def resolve(w, story_id, choice):
    if story_id not in {s["id"] for s in available(w)}:
        raise ValueError("事件尚未觸發或已完成。")
    if choice == 0:
        if story_id in ("neighbor", "postcard"):
            advance(w, 30 if story_id == "neighbor" else 20)
            w["mood"] = min(100, w["mood"] + (8 if story_id == "neighbor" else 10))
        elif story_id in ("book", "prototype", "rain", "promise"):
            npc = next(n for n in w["npcs"] if n["id"] == ("lin" if story_id in ("book", "rain") else "zhou"))
            npc["trust"] = min(100, npc["trust"] + 5)
            npc["memories"].append({"minutes": w["minutes"], "text": STORIES[story_id]["title"] + "：你願意花時間傾聽。"})
            advance(w, 30)
        elif story_id == "client":
            if w["energy"] < 10: raise ValueError("交付調整需要精力 10。")
            w["energy"] -= 10
            advance(w, 120)
            w["company"]["capital"] += 2000
            entry(w, "company", 2000, "客戶調整訂單")
        elif story_id == "team":
            if w["company"]["capital"] < 500: raise ValueError("公司需要 500 元。")
            w["company"]["capital"] -= 500
            entry(w, "company", -500, "團隊慶祝")
            w["mood"] = min(100, w["mood"] + 15)
    w["story_done"].append(story_id)
    event = STORIES[story_id]["title"] + "：" + STORIES[story_id]["choices"][choice]
    w["story_history"].append(event)
    return event
