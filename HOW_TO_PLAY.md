# 瀏覽器試玩版

此套件沒有公開遊戲網址，請在自己的電腦啟動。

## Windows

1. 安裝 Python 3.12（python.org）。
2. 完整解壓縮套件。
3. 雙擊 START_GAME.bat。第一次啟動需連網下載依賴。
4. 等到視窗顯示服務啟動完成，在 Chrome、Edge 或 Firefox 網址列輸入 127.0.0.1:8000。
5. 按「開始新遊戲」，建立角色。右上角可開啟音樂。

遊玩期間請保留啟動視窗；按 Ctrl+C 可關閉服務。批次檔尚未在 Windows 實機測試。

## Linux / macOS

安裝 Python 3.12，在解壓縮目錄執行：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
bash scripts/start_web.sh
```

接著在瀏覽器網址列輸入 127.0.0.1:8000。

## 遊玩提示

- 探索「辦公室」可進行公司業務，餐廳或咖啡廳可用餐。
- 前往 NPC 所在公共場所，才能聊天與邀約。
- 「故事」會依所在地、關係與公司進度出現新事件。
- 離開前手動儲存至三個存檔槽之一。存檔保存在 .local/game.sqlite3，請保留此檔案。
- 字體、音量與顯示模式保存在當前瀏覽器，預設顯示完整場景。
- 這是單人本機版本，多個分頁共用同一個世界。不要直接開放到公開網路。
