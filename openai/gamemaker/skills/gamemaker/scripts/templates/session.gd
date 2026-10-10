# Scripted headless session for a Godot 4 game — the gamemaker SESSION capture.
#
# Copy into the project as tools/session.gd, then adapt the three marked
# sections (main scene, input schedule, metrics conventions).
#
#   godot --headless --path . --script res://tools/session.gd -- --seed 7 --out capture-out --duration 30
#
# Emits into --out:  frames/NNN.png  and  metrics.json
# Exits non-zero when the session did not complete, so it works as a free gate.
# Tile the frames into a filmstrip afterwards (ImageMagick `montage`, or reuse
# the canvas tiler from capture_web.mjs on a file:// page).
#
# Conventions the game must honour (references/harness.md):
#   - all gameplay randomness goes through one RNG the session can seed
#   - an autoload named `Metrics` with:  completed: bool, events: Array
#     (adapt REQUIRED below if yours differs)
#
# Determinism: fix Engine.physics_ticks_per_second in project settings and do
# gameplay in _physics_process; a headless run then plays the same every time.

extends SceneTree

const MAIN_SCENE := "res://scenes/Main.tscn"     # ADAPT

# --------------------------------------------- ADAPT: the input schedule
# t = seconds from session start. One action per line; the same moves every
# round, or improvement is indistinguishable from luck.
const SCHEDULE := [
	{ "t": 1.0,  "action": "ui_accept",   "pressed": true  },
	{ "t": 1.1,  "action": "ui_accept",   "pressed": false },
	{ "t": 2.0,  "action": "accelerate",  "pressed": true  },
	{ "t": 6.0,  "action": "steer_left",  "pressed": true  },
	{ "t": 7.0,  "action": "steer_left",  "pressed": false },
	{ "t": 12.0, "action": "handbrake",   "pressed": true  },
	{ "t": 12.4, "action": "handbrake",   "pressed": false },
]

const FRAME_EVERY := 2.0     # seconds between captured frames
var duration := 30.0
var out_dir := "capture-out"
var seed_value := 7

var _elapsed := 0.0
var _next_frame := 0.0
var _frame_n := 0
var _due: Array = []
var _fps_samples: Array = []
var _fps_accum := 0.0


func _initialize() -> void:
	for i in OS.get_cmdline_user_args().size():
		var a: String = OS.get_cmdline_user_args()[i]
		var nxt := OS.get_cmdline_user_args()[i + 1] if i + 1 < OS.get_cmdline_user_args().size() else ""
		match a:
			"--seed": seed_value = int(nxt)
			"--out": out_dir = nxt
			"--duration": duration = float(nxt)

	DirAccess.make_dir_recursive_absolute(out_dir + "/frames")
	seed(seed_value)                       # ADAPT: also seed the game's own RNG singleton here
	_due = SCHEDULE.duplicate(true)

	var err := change_scene_to_file(MAIN_SCENE)
	if err != OK:
		push_error("could not load %s" % MAIN_SCENE)
		quit(1)


func _process(delta: float) -> bool:
	if super._process(delta):
		return true                        # scene tree asked to quit
	_elapsed += delta

	# fps sampling, once per second
	_fps_accum += delta
	if _fps_accum >= 1.0:
		_fps_samples.append(Engine.get_frames_per_second())
		_fps_accum = 0.0

	# scheduled input
	while not _due.is_empty() and _due[0]["t"] <= _elapsed:
		var ev := InputEventAction.new()
		ev.action = _due[0]["action"]
		ev.pressed = _due[0]["pressed"]
		Input.parse_input_event(ev)
		_due.pop_front()

	# frames
	if _elapsed >= _next_frame:
		var img := root.get_viewport().get_texture().get_image()
		img.save_png("%s/frames/%03d.png" % [out_dir, _frame_n])
		_frame_n += 1
		_next_frame += FRAME_EVERY

	if _elapsed >= duration:
		_finish()
		return true
	return false


func _finish() -> void:
	# ADAPT: read your game's metrics autoload; `Metrics` with .completed/.events assumed.
	var m := root.get_node_or_null("/root/Metrics")
	var completed: bool = m.completed if m else false
	var events: Array = m.events if m else []

	_fps_samples = _fps_samples.slice(1) if _fps_samples.size() > 1 else _fps_samples
	var fps_mean := 0.0
	for s in _fps_samples: fps_mean += s
	fps_mean = fps_mean / _fps_samples.size() if _fps_samples.size() else 0.0

	var metrics := {
		"seed": seed_value,
		"duration": duration,
		"fps_mean": snappedf(fps_mean, 0.1),
		"fps_min": _fps_samples.min() if _fps_samples.size() else 0,
		"completed": completed,
		"events": events,
	}
	var f := FileAccess.open(out_dir + "/metrics.json", FileAccess.WRITE)
	f.store_string(JSON.stringify(metrics, "  ") + "\n")
	f.close()

	if not completed:
		push_error("session did not complete (Metrics.completed != true)")
		quit(1)
	else:
		print("ok: %d frames, metrics.json -> %s" % [_frame_n, out_dir])
		quit(0)
