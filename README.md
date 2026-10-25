# 第二人生：慾望都市

依 GDD v0.1 建立的 P0 原型：Godot 4 + FastAPI + SQLite，繁體中文、單人離線核心。

## 開發環境

Python 3.12、Godot 4.6（相容渲染器）、curl。從專案根目錄執行：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
./scripts/start.sh
```

啟動腳本會啟動本機 API、確認健康檢查，再開啟 Godot；關閉遊戲後停止它啟動的後端。
Windows 開發可在兩個終端分別執行 `python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000` 與 `godot --path client`（先啟用已安裝依賴的虛擬環境）。目前尚未製作 Windows 發行包。

## 已實作（0.4）

- 主選單：新遊戲、讀檔、繼續、設定與離開。
- 遊戲選單：城市、公司、社交／戀愛、人物、生活、手機、時間、存讀檔及返回。
- 深藍城市剪影、金色文字與圓角按鈕，支援鍵盤焦點與捲動選單。
- 角色建立：姓名、成年年齡、代稱、背景、外觀描述與興趣。
- 四地點移動、時間與精力、飢餓與心情、用餐、明信片收藏、閒暇與住所休息。
- 場景描述卡、人物關係卡、共同回憶與事件日記。
- 8 位成年 NPC、日程、聊天與記憶；兩位可邀約角色，依信任與好感接受或拒絕，每 24 遊戲小時限邀約一次。關係可由初識發展至朋友、曖昧及交往；表白需要至少兩次約會與信任 30，拒絕後不能立即重試。
- 公司創業、兩名可聘用員工、研發產品；工具與休閒遊戲兩種產品；每次研發花費 500／800 元，兩次研發完成。基礎日收入 1,200／1,800 元，再乘上市場與行銷加成；員工日薪 300 元，記錄流水帳。
- 每日需求依 100%、80%、120%、110%、90% 循環；行銷每次 800 元增加 20%，上限 50%，每日結算後衰減 10%。
- 公司業務需在辦公室處理；資金不足時不可招聘／研發。薪資仍會扣除，原型允許公司負債，尚無破產流程。
- SQLite 三存檔槽，列出角色與日期，覆蓋前確認；新遊戲不覆蓋已有存檔。
- 字體大小、主音量與顯示模式保存至 Godot `user://settings.cfg`，重啟後載入。音量控制背景音樂與操作音效。
- API 驗證錯誤和離線服務提示；無需模型 API 金鑰。

採規則式離線對話，尚未串接 LLM 或照片匯入。新增 AI 生成的 4 場景與 8 人物圖集，A 為文字、B 加入角色圖、C 加入場景圖；人物外觀自訂目前仍以文字保存。

- 背景音樂為 16 秒原創合成循環，另有按鈕、成功與錯誤音效，主音量可調；生成器在 `scripts/generate_audio.py`。
- 「城市故事」提供 8 個一次性選擇事件：鄰里、明信片、閱讀會、作品試用、兩段約會後事件、客戶訂單與團隊慶祝。依地點、收藏、關係與公司進度出現，可接受或婉拒，結果與完成狀態可存檔。
- 美術與音訊來源詳見 `client/assets/ASSETS.md`。

公司尚無完整競爭與市場供需模擬。存檔 v1/v2 可遷移至 v3，原有時間、資金與公司保留。尚未完成整份 GDD 的 MVP。

## 驗證

```bash
.venv/bin/python -m pytest -q
XDG_DATA_HOME="$PWD/.local/share" XDG_CONFIG_HOME="$PWD/.local/config" XDG_CACHE_HOME="$PWD/.local/cache" godot --headless --path client --editor --import --quit
test_dir=$(mktemp -d /tmp/second-life-test-XXXXXX)
GAME_USER_DIR="$test_dir/user" GAME_DB_PATH="$test_dir/game.sqlite3" ./scripts/start.sh --headless --script ../tests/ui_smoke.gd
```

API：`GET /health`、`POST /game/new`、`GET /game`、`POST /game/action`、`POST /game/save`、`POST /game/load`、`GET /game/saves`、`GET /game/stories`、`POST /game/story`。存讀檔接受 `?slot=1` 至 `?slot=3`，省略時使用槽 1。存檔預設 `.local/game.sqlite3`；可用 `GAME_DB_PATH` 指定測試資料庫。
