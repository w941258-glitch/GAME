"""Deterministic rules; no network or AI credentials required."""
from copy import deepcopy

NPC_DATA = [
    ("lin", "林予晴", 26, "設計師", "溫和、喜歡閱讀", True),
    ("zhou", "周以辰", 29, "工程師", "內斂、喜歡科技", True),
    ("chen", "陳可欣", 25, "程式開發", "踏實", False),
    ("wu", "吳柏宇", 28, "產品設計", "細心", False),
    ("xu", "許嘉文", 34, "競爭者", "積極", False),
    ("huang", "黃思穎", 31, "客戶", "務實", False),
    ("li", "李明哲", 30, "咖啡師", "開朗", False),
    ("wang", "王雅婷", 27, "自由工作者", "好奇", False),
]


def npcs():
    return [{"id": i, "name": n, "age": a, "job": j, "personality": p,
             "romance": r, "affinity": 0, "trust": 0, "memories": [], "last_chat": -1440,
             "last_invite": -1440, "dates": 0, "location": "cafe"} for i, n, a, j, p, r in NPC_DATA]


def migrate(value):
    w = deepcopy(value)
    if w.get("version") not in (1, 2, 3):
        raise ValueError("不支援的存檔版本。")
    w["version"] = 3
    w.setdefault("player", {"name": "新市民", "age": 24, "pronouns": "不指定", "background": "自由工作者", "appearance": "日常休閒風", "interest": "閱讀"})
    w.setdefault("npcs", npcs())
    w.setdefault("ledger", [])
    w.setdefault("mood", 60)
    w.setdefault("hunger", 20)
    w.setdefault("inventory", [])
    w.setdefault("story_done", [])
    w.setdefault("story_history", [])
    w.setdefault("hunger_clock", 0)
    for npc in w["npcs"]:
        npc.setdefault("stage", "初識")
        npc.setdefault("milestones", [])
        npc.setdefault("last_confess", -1440)
    if w.get("company"):
        c = w["company"]
        for key, default in {"employees": [], "products": 0, "progress": 0, "last_settled": w["minutes"] // 1440, "product_type": "tool", "marketing": 0, "catalog": {"tool": c.get("products", 0), "game": 0}, "market": 100}.items():
            c.setdefault(key, default)
    schedule(w)
    return w


def schedule(w):
    hour = (w["minutes"] % 1440) // 60
    for index, npc in enumerate(w["npcs"]):
        npc["location"] = "home" if hour < 8 or hour >= 22 else ("office" if 9 <= hour < 17 else ("cafe" if index % 2 == 0 else "restaurant"))


def entry(w, account, amount, reason):
    w["ledger"].append({"minutes": w["minutes"], "account": account, "amount": amount, "reason": reason})


def advance(w, minutes):
    old_day = w["minutes"] // 1440
    w["minutes"] += minutes
    w["hunger_clock"] += minutes
    hunger_steps, w["hunger_clock"] = divmod(w["hunger_clock"], 60)
    w["hunger"] = min(100, w["hunger"] + hunger_steps * 4)
    if w["hunger"] >= 80:
        w["mood"] = max(0, w["mood"] - hunger_steps * 2)
    c = w.get("company")
    if c:
        for day in range(old_day + 1, w["minutes"] // 1440 + 1):
            demand = [100, 80, 120, 110, 90][(day - 1) % 5]
            c["market"] = demand
            base = c["catalog"]["tool"] * 1200 + c["catalog"]["game"] * 1800
            revenue = base * (demand + c["marketing"]) // 100
            c["marketing"] = max(0, c["marketing"] - 10)
            wages = len(c["employees"]) * 300
            c["capital"] += revenue - wages
            entry(w, "company", revenue, "第 %d 天產品收入" % day)
            entry(w, "company", -wages, "第 %d 天薪資" % day)
            c["last_settled"] = day
            w["events"].append("營業結算：收入 %d，薪資 %d。" % (revenue, wages))
    schedule(w)


def apply(w, body):
    """Mutates a candidate world. Caller commits only on success."""
    kind = body.kind
    c = w.get("company")
    if kind in ("eat", "shop", "leisure"):
        if kind == "eat":
            if w["location"] not in ("cafe", "restaurant") or w["cash"] < 150:
                raise ValueError("請到咖啡廳或餐廳，並準備 150 元。")
            w["cash"] -= 150
            entry(w, "player", -150, "用餐")
            advance(w, 30)
            w["hunger"] = max(0, w["hunger"] - 50)
            w["energy"] = min(100, w["energy"] + 10)
            w["mood"] = min(100, w["mood"] + 5)
            return "享用一餐，飢餓下降、心情與精力恢復。"
        if kind == "shop":
            if w["location"] != "cafe" or w["cash"] < 200:
                raise ValueError("請到咖啡廳旁的小店，並準備 200 元。")
            if len(w["inventory"]) >= 10:
                raise ValueError("收藏已滿（10 件）。")
            w["cash"] -= 200
            entry(w, "player", -200, "購買城市明信片")
            w["inventory"].append("城市明信片")
            advance(w, 30)
            w["mood"] = min(100, w["mood"] + 10)
            return "買了一張城市明信片，收藏與心情增加。"
        advance(w, 60)
        w["mood"] = min(100, w["mood"] + 15)
        return "放慢步調，享受一小時的閒暇。"
    if kind in ("chat", "invite", "confess"):
        npc = next((n for n in w["npcs"] if n["id"] == body.npc_id), None)
        if npc is None:
            raise ValueError("找不到角色。")
        if npc["location"] != w["location"] or npc["location"] == "home":
            raise ValueError("請在角色所在的公共場所互動。")
        if kind == "confess":
            if npc["stage"] == "交往":
                raise ValueError("你們已經在交往。")
            if w["minutes"] - npc["last_confess"] < 1440:
                raise ValueError("請尊重對方的回應，明天再談。")
            npc["last_confess"] = w["minutes"]
            if not npc["romance"] or npc["dates"] < 2 or npc["trust"] < 30:
                event = npc["name"] + "：我還沒準備好確定關係，希望你能理解。"
                npc["memories"].append({"minutes": w["minutes"], "text": event})
                return event
            npc["stage"] = "交往"
            npc["milestones"].append("確認關係")
            advance(w, 20)
            event = npc["name"] + "：我也想和你一起走下去。你們確認了關係。"
            npc["memories"].append({"minutes": w["minutes"], "text": event})
            return event
        if kind == "chat":
            if w["minutes"] - npc["last_chat"] < 60:
                raise ValueError("對方想先忙自己的事，請一小時後再聊。")
            npc["last_chat"] = w["minutes"]
            gain = 8 if (npc["id"] == "lin" and w["player"]["interest"] == "閱讀") or (npc["id"] == "zhou" and w["player"]["interest"] == "科技") else 5
            npc["affinity"] = min(100, npc["affinity"] + gain)
            npc["trust"] = min(100, npc["trust"] + 5)
            event = npc["name"] + ("：最近讀到一本很有意思的書，謝謝你願意聽我分享。" if npc["id"] == "lin" else "：今天的工作有些挑戰，聊完後感覺好多了。")
            if npc["id"] not in ("lin", "zhou"):
                event = npc["name"] + "：" + {"chen": "新專案可以先拆成小任務。", "wu": "好的設計應該讓使用者感到自在。", "xu": "市場變化很快，可別鬆懈。", "huang": "比起宣傳，我更在意交付品質。", "li": "今天的咖啡香氣特別好。", "wang": "想給自己安排一趟城市漫遊。"}[npc["id"]]
            if npc["trust"] >= 15 and npc["stage"] == "初識":
                npc["stage"] = "朋友"
                npc["milestones"].append("成為朋友")
                event += " 你們成為了朋友。"
            advance(w, 20)
        else:
            if w["minutes"] - npc["last_invite"] < 1440:
                raise ValueError("今天已邀約，請尊重對方並等待明天。")
            npc["last_invite"] = w["minutes"]
            if not npc["romance"] or npc["trust"] < 15 or npc["affinity"] < (20 if npc["id"] == "zhou" else 15):
                event = npc["name"] + "：謝謝邀請，我現在不想約會。"
            else:
                if w["cash"] < 300:
                    raise ValueError("約會需預留 300 元。")
                w["cash"] -= 300
                entry(w, "player", -300, "約會餐費")
                npc["dates"] += 1
                if npc["stage"] != "交往":
                    npc["stage"] = "曖昧"
                if npc["dates"] == 1:
                    npc["milestones"].append("初次約會")
                npc["affinity"] = min(100, npc["affinity"] + 10)
                event = npc["name"] + "接受邀請，一起度過愉快的時光。"
                advance(w, 60)
        npc["memories"].append({"minutes": w["minutes"], "text": event})
        return event
    if not c:
        raise ValueError("請先成立公司。")
    if w["location"] != "office":
        raise ValueError("請前往辦公室處理公司業務。")
    if kind == "select_product":
        if c["progress"]:
            raise ValueError("請先完成目前研發，再切換產品。")
        c["product_type"] = body.product_type
        return "產品方向已切換：" + ("效率工具" if body.product_type == "tool" else "休閒遊戲")
    if kind == "market":
        if c["capital"] < 800 or c["products"] == 0 or c["marketing"] >= 50:
            raise ValueError("行銷需要已上市產品、800 元，且加成未達 50%。")
        c["capital"] -= 800
        entry(w, "company", -800, "行銷活動")
        c["marketing"] = min(50, c["marketing"] + 20)
        advance(w, 60)
        return "行銷加成增加 20%，每天結算後衰減 10%。"
    if kind == "hire":
        if body.npc_id not in ("chen", "wu") or body.npc_id in c["employees"]:
            raise ValueError("請選擇尚未聘用的應徵者。")
        if c["capital"] < 1000:
            raise ValueError("公司招聘需 1,000 元。")
        c["capital"] -= 1000
        c["employees"].append(body.npc_id)
        entry(w, "company", -1000, "招聘費")
        advance(w, 30)
        return "成功聘用一名員工；每日薪資 300 元。"
    if kind == "develop":
        cost = 500 if c["product_type"] == "tool" else 800
        if not c["employees"] or c["capital"] < cost or w["energy"] < 10:
            raise ValueError("研發需要至少一名員工、足夠研發資金（工具 500／遊戲 800 元）與精力 10。")
        c["capital"] -= cost
        entry(w, "company", -cost, "研發費")
        w["energy"] -= 10
        c["progress"] += 50
        if c["progress"] >= 100:
            c["progress"] -= 100
            c["products"] += 1
            c["catalog"][c["product_type"]] += 1
        advance(w, 120)
        return "研發進度增加 50%；完成的產品將於每天午夜產生收入。"
    raise ValueError("未知操作。")
