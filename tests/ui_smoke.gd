extends SceneTree

func _initialize() -> void:
	call_deferred("run")

func check(value: bool, message: String) -> bool:
	if not value:
		push_error(message)
		quit(1)
	return value

func click(ui: Node, label: String) -> bool:
	for child in ui.content.get_children():
		if child is Button and child.text == label:
			child.pressed.emit()
			return true
	return check(false, "Missing button: " + label)

func wait_request(ui: Node) -> bool:
	for i in range(300):
		if not ui.busy:
			return true
		await create_timer(0.02).timeout
	return check(false, "API request timeout")

func run() -> void:
	var ui = load("res://main.tscn").instantiate()
	root.add_child(ui)
	if not click(ui, "開始新遊戲"): return
	ui.character_fields.name.text = "測試市民"
	if not click(ui, "展開新人生"): return
	if not await wait_request(ui): return
	if not check(ui.world.get("cash") == 100000, "New game failed"): return
	if not check(ui.world.player.name == "測試市民", "Character creation failed"): return
	if not click(ui, "城市：選擇地點"): return
	if not click(ui, "咖啡廳"): return
	if not await wait_request(ui): return
	if not check(ui.world.get("location") == "cafe", "Travel failed"): return
	if not click(ui, "儲存遊戲"): return
	if not await wait_request(ui): return
	if not click(ui, "儲存至 1"): return
	if not click(ui, "確認儲存"): return
	if not await wait_request(ui): return
	if not check(ui.notice.text == "已儲存至本機存檔。", "Save failed"): return
	if not click(ui, "返回主選單"): return
	if not click(ui, "開始新遊戲"): return
	ui.character_fields.name.text = "測試市民"
	if not click(ui, "展開新人生"): return
	if not await wait_request(ui): return
	ui.main_menu()
	if not click(ui, "讀取存檔"): return
	if not await wait_request(ui): return
	if not click(ui, "讀取 1"): return
	if not await wait_request(ui): return
	if not check(ui.world.get("location") == "cafe", "Load failed"): return
	for label in ["社交／戀愛", "人物", "手機", "公司：數位產品工作室"]:
		if not click(ui, label): return
		if not click(ui, "返回"): return
	# Exercise actual social and company controls through HTTP.
	ui.city()
	if not click(ui, "辦公室"): return
	if not await wait_request(ui): return
	if not click(ui, "社交／戀愛"): return
	if not click(ui, "與 林予晴 聊天"): return
	if not await wait_request(ui): return
	if not check(ui.world.npcs[0].trust == 5, "Chat failed"): return
	ui.company()
	if not click(ui, "成立公司"): return
	if not await wait_request(ui): return
	ui.company()
	if not click(ui, "聘用 陳可欣（1,000 元）"): return
	if not await wait_request(ui): return
	for i in range(2):
		ui.company()
		if not click(ui, "研發兩小時（工具 500／遊戲 800 元；精力 10）"): return
		if not await wait_request(ui): return
	if not check(ui.world.company.products == 1, "Product development failed"): return
	ui.city()
	if not click(ui, "咖啡廳"): return
	if not await wait_request(ui): return
	ui.life()
	if not click(ui, "用餐（150 元／30 分鐘，餐廳或咖啡廳）"): return
	if not await wait_request(ui): return
	ui.life()
	if not click(ui, "買明信片（200 元／30 分鐘，咖啡廳）"): return
	if not await wait_request(ui): return
	if not check(ui.world.inventory.size() == 1, "Shopping failed"): return
	ui.font_size = 25
	ui.volume = 35
	ui.save_preferences()
	ui.font_size = 19
	ui.load_preferences()
	if not check(ui.font_size == 25 and ui.volume == 35, "Preferences persistence failed"): return
	ui.main_menu()
	if not click(ui, "設定"): return
	if not click(ui, "B 立繪"): return
	if not check(ui.mode == "B 立繪", "Settings failed"): return
	ui.game_menu()
	ui.city()
	if not click(ui, "住所"): return
	if not await wait_request(ui): return
	if not click(ui, "城市故事"): return
	if not await wait_request(ui): return
	if not click(ui, "幫忙搬運（30 分鐘，心情 +8）"): return
	if not await wait_request(ui): return
	if not check("neighbor" in ui.world.story_done, "Story resolution failed"): return
	ui.mode = "C 場景"
	ui.game_menu()
	ui.social()
	var portraits := 0
	for child in ui.content.get_children():
		if child is TextureRect:
			portraits += 1
	if not check(portraits == 8, "Portrait atlas failed"): return
	if not check(ui.music.playing, "Music failed to play"): return
	print("UI_SMOKE_PASS: character, social, hiring, product, menus, travel, save/load, settings")
	ui.music.stop()
	ui.sounds.stop()
	ui.queue_free()
	await process_frame
	await process_frame
	quit(0)
