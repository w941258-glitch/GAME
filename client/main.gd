extends Control

const API = "http://127.0.0.1:8000"
const PLACES = {"home": "住所", "office": "辦公室", "cafe": "咖啡廳", "restaurant": "餐廳"}
var world: Dictionary = {}
var column: VBoxContainer
var status: Label
var content: VBoxContainer
var notice: Label
var request: HTTPRequest
var busy := false
var pending := ""
var character_fields: Dictionary = {}
var font_size := 19
var music: AudioStreamPlayer
var sounds: AudioStreamPlayer
var volume := 70.0
var mode := "C 場景"

func _ready() -> void:
	var skin := Theme.new()
	skin.default_font_size = 19
	var panel := StyleBoxFlat.new()
	panel.bg_color = Color("17283c")
	panel.border_color = Color("376879")
	panel.set_border_width_all(1)
	panel.set_corner_radius_all(10)
	panel.content_margin_left = 20
	panel.content_margin_right = 20
	panel.content_margin_top = 10
	panel.content_margin_bottom = 10
	skin.set_stylebox("normal", "Button", panel)
	var hover := panel.duplicate() as StyleBoxFlat
	hover.bg_color = Color("285566")
	skin.set_stylebox("hover", "Button", hover)
	skin.set_stylebox("focus", "Button", hover)
	skin.set_stylebox("pressed", "Button", hover)
	skin.set_color("font_color", "Label", Color("e0e8ed"))
	skin.set_color("font_color", "Button", Color("e4d5af"))
	theme = skin
	var skyline := Control.new()
	skyline.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(skyline)
	for i in range(14):
		var building := ColorRect.new()
		building.mouse_filter = Control.MOUSE_FILTER_IGNORE
		building.color = Color(0.07, 0.13, 0.20, 0.65)
		building.position = Vector2(i * 100, 420 + (i * 37) % 140)
		building.size = Vector2(76, 400)
		skyline.add_child(building)
	var margin := MarginContainer.new()
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	for side in ["left", "right", "top", "bottom"]:
		margin.add_theme_constant_override("margin_" + side, 32)
	add_child(margin)
	column = VBoxContainer.new()
	column.add_theme_constant_override("separation", 14)
	margin.add_child(column)
	var title := Label.new()
	title.text = "第二人生：慾望都市  /  CITY STORIES  /  0.4"
	title.add_theme_font_size_override("font_size", 30)
	column.add_child(title)
	status = Label.new()
	column.add_child(status)
	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	column.add_child(scroll)
	content = VBoxContainer.new()
	content.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	content.add_theme_constant_override("separation", 10)
	scroll.add_child(content)
	notice = Label.new()
	notice.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	column.add_child(notice)
	request = HTTPRequest.new()
	add_child(request)
	request.request_completed.connect(_completed)
	music = AudioStreamPlayer.new()
	var track := load("res://assets/audio/city_evening.wav") as AudioStreamWAV
	track.loop_mode = AudioStreamWAV.LOOP_FORWARD
	track.loop_end = int(track.get_length() * track.mix_rate)
	music.stream = track
	music.volume_db = -8
	add_child(music)
	sounds = AudioStreamPlayer.new()
	add_child(sounds)
	load_preferences()
	music.play()
	main_menu()

func clear() -> void:
	for child in content.get_children():
		content.remove_child(child)
		child.queue_free()

func text(value: String) -> void:
	var label := Label.new()
	label.text = value
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	content.add_child(label)

func button(label: String, callback: Callable) -> void:
	var item := Button.new()
	item.text = label
	item.custom_minimum_size.y = 44
	item.pressed.connect(func():
		if not busy:
			play_sound("click")
			callback.call())
	content.add_child(item)

func main_menu() -> void:
	clear()
	status.text = "離線核心 · 本機存檔 · 繁體中文"
	text("城市還醒著，你的人生正要開始。\n\n工作、相遇、創造。每個選擇，都會留下痕跡。")
	button("開始新遊戲", create_character)
	button("讀取存檔", func(): slots_menu(false))
	if not world.is_empty():
		button("繼續遊戲", game_menu)
	button("設定", settings)
	button("離開遊戲", func(): get_tree().quit())

func settings() -> void:
	clear()
	text("閱讀與聲音")
	var font_control := SpinBox.new()
	font_control.min_value = 16
	font_control.max_value = 30
	font_control.value = font_size
	content.add_child(font_control)
	font_control.value_changed.connect(func(value): font_size = int(value); theme.default_font_size = font_size; save_preferences())
	text("字體大小（16–30）／主音量")
	var sound := HSlider.new()
	sound.min_value = 0
	sound.max_value = 100
	sound.value = volume
	content.add_child(sound)
	sound.value_changed.connect(func(value): volume = value; AudioServer.set_bus_volume_db(0, linear_to_db(maxf(volume / 100.0, 0.0001))); save_preferences())
	text("顯示模式：" + mode + "\n切換文字、角色或完整場景顯示。\nAI 與圖片生成：未連接，核心玩法可離線運作。")
	for value in ["A 文字", "B 立繪", "C 場景"]:
		button(value, func(): mode = value; save_preferences(); settings())
	button("返回主選單", main_menu)

func game_menu() -> void:
	clear()
	var minutes := int(world.get("minutes", 540))
	status.text = "第 %d 天  %02d:%02d  |  現金 %d  |  精力 %d  |  %s" % [minutes / 1440 + 1, (minutes % 1440) / 60, minutes % 60, world.get("cash", 0), world.get("energy", 0), PLACES.get(world.get("location", "home"))]
	text("心情 %d  /  飢餓 %d（越低越好）  /  收藏 %d" % [world.mood, world.hunger, world.inventory.size()])
	if mode == "C 場景":
		art(PLACES.keys().find(world.location), 260)
	card(PLACES[world.location], {"home": "窗邊的光映著書桌，這裡是你的私人避風港。", "office": "螢幕亮起，新產品的構想正等著成形。", "cafe": "咖啡香穿過街角，人們在這裡交換故事。", "restaurant": "暖色燈光下，一頓飯也能成為值得記住的時刻。"}[world.location])
	text("%s 的城市日記\n" % world.player.name + "\n".join(world.get("events", []).slice(-4)))
	button("城市：選擇地點", city)
	button("公司：數位產品工作室", company)
	button("社交／戀愛", social)
	button("人物", profile)
	button("生活：用餐／購物／休息", life)
	button("城市故事", func(): call_api("/game/stories"))
	button("手機", func(): placeholder("手機", "\n".join(world.get("events", []))))
	button("時間：前進一小時", func(): action("wait"))
	button("儲存遊戲", func(): slots_menu(true))
	button("讀取存檔", func(): slots_menu(false))
	button("返回主選單", main_menu)

func city() -> void:
	clear()
	text("選擇目的地：交通耗時 30 分鐘、精力 5。")
	for key in PLACES:
		button(PLACES[key], func(): action("travel", key))
	button("返回", game_menu)

func company() -> void:
	clear()
	if world.get("company") == null:
		text("投入 10,000 元創辦數位產品工作室，資金轉入公司。")
		button("成立公司", func(): action("found_company"))
	else:
		text("%s\n公司資金：%d  /  員工：%d\n產品：%d  /  研發：%d%%\n每名員工日薪 300 元；收入依產品、市場與行銷變化。" % [world.company.name, world.company.capital, world.company.employees.size(), world.company.products, world.company.progress])
		text("市場需求：%d%% / 行銷加成：%d%%\n工具 %d 項 / 遊戲 %d 項 / 研發方向：%s" % [world.company.market, world.company.marketing, world.company.catalog.tool, world.company.catalog.game, world.company.product_type])
		button("產品：效率工具", func(): call_api("/game/action", {"kind": "select_product", "product_type": "tool"}))
		button("產品：休閒遊戲", func(): call_api("/game/action", {"kind": "select_product", "product_type": "game"}))
		button("行銷活動（800 元）", func(): action("market"))
		for npc in world.npcs:
			if npc.id in ["chen", "wu"] and not npc.id in world.company.employees:
				button("聘用 " + npc.name + "（1,000 元）", func(): npc_action("hire", npc.id))
		button("研發兩小時（工具 500／遊戲 800 元；精力 10）", func(): action("develop"))
		text("財務流水帳（最近 8 筆）")
		for record in world.ledger.slice(-8):
			text("%s  %s  %+d" % [record.account, record.reason, record.amount])
	button("返回", game_menu)

func create_character() -> void:
	clear()
	character_fields.clear()
	text("建立你的角色  /  每段人生從一個選擇開始")
	for field in [["name", "姓名", "新市民"], ["appearance", "外觀描述", "日常休閒風"]]:
		text(field[1])
		var input := LineEdit.new()
		input.text = field[2]
		input.max_length = 24 if field[0] == "name" else 120
		content.add_child(input)
		character_fields[field[0]] = input
	text("年齡（18 歲以上）")
	var age := SpinBox.new()
	age.min_value = 18
	age.max_value = 100
	age.value = 24
	content.add_child(age)
	character_fields.age = age
	for field in [["pronouns", "代稱", ["不指定", "她", "他", "TA"]], ["background", "背景", ["自由工作者", "上班族", "創業新手"]], ["interest", "興趣", ["閱讀", "科技", "美食", "藝術"]]]:
		text(field[1])
		var option := OptionButton.new()
		for value in field[2]:
			option.add_item(value)
		content.add_child(option)
		character_fields[field[0]] = option
	button("展開新人生", submit_character)
	button("返回主選單", main_menu)

func submit_character() -> void:
	var data := {}
	for key in character_fields:
		var field = character_fields[key]
		if field is LineEdit:
			data[key] = field.text.strip_edges()
		elif field is SpinBox:
			data[key] = int(field.value)
		else:
			data[key] = field.get_item_text(field.selected)
	if data.name.is_empty():
		notice.text = "請輸入角色姓名。"
		return
	call_api("/game/new", data)

func profile() -> void:
	var p: Dictionary = world.player
	placeholder("人物檔案", "%s · %d 歲 · %s\n%s / 興趣：%s\n外觀：%s" % [p.name, p.age, p.pronouns, p.background, p.interest, p.appearance])

func social() -> void:
	clear()
	text("城市人物  /  前往相同公共場所即可互動")
	for npc in world.npcs:
		if mode != "A 文字":
			art(4 + world.npcs.find(npc), 220)
		card(npc.name + " · " + npc.stage, "%s · %d 歲 · %s\n%s  |  目前：%s\n好感 %d / 信任 %d / 約會 %d" % [npc.name, npc.age, npc.job, npc.personality, PLACES[npc.location], npc.affinity, npc.trust, npc.dates])
		if npc.location == world.location and npc.location != "home":
			button("與 " + npc.name + " 聊天", func(): npc_action("chat", npc.id))
			if npc.romance:
				button("邀約 " + npc.name, func(): npc_action("invite", npc.id))
				button("向 " + npc.name + " 表白", func(): npc_action("confess", npc.id))
		if not npc.milestones.is_empty():
			text("共同回憶：" + "、".join(npc.milestones))
		if not npc.memories.is_empty():
			text("最近記憶：" + npc.memories[-1].text)
	button("返回", game_menu)

func npc_action(kind: String, npc_id: String) -> void:
	call_api("/game/action", {"kind": kind, "npc_id": npc_id})

func placeholder(title: String, body: String) -> void:
	clear()
	text(title + "\n\n" + body)
	button("返回", game_menu)

func action(kind: String, location: String = "") -> void:
	var body := {"kind": kind}
	if not location.is_empty():
		body.location = location
	call_api("/game/action", body)

func call_api(path: String, body: Dictionary = {}) -> void:
	if busy:
		return
	busy = true
	pending = path
	notice.text = "處理中…"
	var error := request.request(API + path, ["Content-Type: application/json"], HTTPClient.METHOD_GET if path in ["/game/saves", "/game/stories"] else HTTPClient.METHOD_POST, "" if path in ["/game/saves", "/game/stories"] else JSON.stringify(body))
	if error != OK:
		busy = false
		notice.text = "無法連線，請先啟動本機後端。"

func _completed(result: int, code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	busy = false
	if result != HTTPRequest.RESULT_SUCCESS:
		notice.text = "後端無法連線。請先執行 scripts/start.sh。"
		return
	var data = JSON.parse_string(body.get_string_from_utf8())
	if not data is Dictionary:
		notice.text = "伺服器回應格式錯誤。"
		return
	if code != 200:
		play_sound("error")
		notice.text = str(data.get("detail", "操作失敗"))
		return
	play_sound("success")
	if pending.begins_with("/game/save") and not pending.begins_with("/game/saves"):
		game_menu()
		notice.text = "已儲存至本機存檔。"
	elif pending == "/game/stories":
		clear()
		text("城市故事  /  每個選擇留下不同的回憶")
		if data.stories.is_empty():
			text("目前沒有新事件。探索地點、建立關係或開發產品後再看看。")
		for story in data.stories:
			card(story.title, story.body)
			for i in range(story.choices.size()):
				button(story.choices[i], func(): call_api("/game/story", {"story_id": story.id, "choice": i}))
		if not world.story_history.is_empty():
			text("已完成的故事\n" + "\n".join(world.story_history))
		button("返回", game_menu)
		notice.text = ""
	elif pending == "/game/saves":
		for item in data.slots:
			text("存檔 %d：%s / 第 %d 天" % [item.slot, item.name, int(item.minutes) / 1440 + 1])
		notice.text = ""
	else:
		world = data
		notice.text = ""
		game_menu()

func card(heading: String, body: String) -> void:
	var box := PanelContainer.new()
	var style := StyleBoxFlat.new()
	style.bg_color = Color("102234")
	style.border_color = Color("bda36e")
	style.border_width_left = 4
	style.set_corner_radius_all(8)
	style.content_margin_left = 18
	style.content_margin_top = 14
	style.content_margin_bottom = 14
	style.content_margin_right = 18
	box.add_theme_stylebox_override("panel", style)
	var label := Label.new()
	label.text = heading + "\n" + body
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(label)
	content.add_child(box)

func life() -> void:
	clear()
	card("生活補給", "心情 %d / 飢餓 %d / 精力 %d\n收藏：%s" % [world.mood, world.hunger, world.energy, "、".join(world.inventory)])
	button("用餐（150 元／30 分鐘，餐廳或咖啡廳）", func(): action("eat"))
	button("買明信片（200 元／30 分鐘，咖啡廳）", func(): action("shop"))
	button("享受閒暇（一小時）", func(): action("leisure"))
	button("在住所休息（兩小時）", func(): action("rest"))
	button("返回", game_menu)

func slots_menu(saving: bool) -> void:
	clear()
	text("選擇存檔槽" + ("；儲存會覆蓋該槽，請確認後操作。" if saving else ""))
	for slot in range(1, 4):
		button(("儲存至 " if saving else "讀取 ") + str(slot), func():
			if saving:
				confirm_save(slot)
			else:
				call_api("/game/load?slot=" + str(slot)))
	button("返回", main_menu if world.is_empty() else game_menu)
	call_api("/game/saves")

func confirm_save(slot: int) -> void:
	clear()
	text("確定儲存到槽 %d？此操作會取代該槽內容。" % slot)
	button("確認儲存", func(): call_api("/game/save?slot=" + str(slot)))
	button("取消", func(): slots_menu(true))

func save_preferences() -> void:
	var config := ConfigFile.new()
	config.set_value("ui", "font_size", font_size)
	config.set_value("ui", "volume", volume)
	config.set_value("ui", "mode", mode)
	if config.save("user://settings.cfg") != OK:
		notice.text = "設定無法儲存，請檢查資料目錄權限。"

func load_preferences() -> void:
	var config := ConfigFile.new()
	if config.load("user://settings.cfg") == OK:
		font_size = clampi(int(config.get_value("ui", "font_size", 19)), 16, 30)
		volume = clampf(float(config.get_value("ui", "volume", 70)), 0, 100)
		mode = str(config.get_value("ui", "mode", "C 場景")).replace("（佔位）", "")
	theme.default_font_size = font_size
	AudioServer.set_bus_volume_db(0, linear_to_db(maxf(volume / 100.0, 0.0001)))

func play_sound(cue: String) -> void:
	if is_instance_valid(sounds):
		sounds.stream = load("res://assets/audio/" + cue + ".wav")
		sounds.play()

func art(index: int, height: int) -> void:
	var atlas_source = load("res://assets/city_atlas.png") as Texture2D
	if atlas_source == null:
		return
	var atlas := AtlasTexture.new()
	atlas.atlas = atlas_source
	var cell := Vector2(atlas_source.get_width() / 4.0, atlas_source.get_height() / 3.0)
	atlas.region = Rect2(Vector2(index % 4, floori(index / 4.0)) * cell, cell)
	var view := TextureRect.new()
	view.texture = atlas
	view.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	view.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	view.custom_minimum_size.y = height
	content.add_child(view)
