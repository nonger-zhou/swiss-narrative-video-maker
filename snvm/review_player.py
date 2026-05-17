import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .errors import SnvmError
from .jsonio import read_json, write_json
from .pipeline import initialize_project_output


def generate_review_player(
    video_path: Path,
    scene_plan_path: Path,
    timing_plan_path: Path | None,
    output_dir: Path,
) -> Path:
    if not video_path.exists():
        raise SnvmError(f"Video file does not exist: {video_path}")
    if not scene_plan_path.exists():
        raise SnvmError(f"Scene plan does not exist: {scene_plan_path}")

    initialize_project_output(output_dir)
    scene_plan = read_json(scene_plan_path)
    timing_plan = read_json(timing_plan_path) if timing_plan_path and timing_plan_path.exists() else None
    payload = {
        "generated_at": _now_iso(),
        "video": _browser_path(video_path, output_dir),
        "scene_plan": str(scene_plan_path),
        "timing_plan": str(timing_plan_path) if timing_plan_path else None,
        "scenes": _player_scenes(scene_plan, timing_plan),
    }

    payload_path = write_json(output_dir / "review_player_data.json", payload)
    html_path = output_dir / "review_player.html"
    html_path.write_text(_html(payload), encoding="utf-8")
    return html_path


def _player_scenes(scene_plan: Any, timing_plan: Any | None) -> list[dict[str, Any]]:
    scenes = _require_scenes(scene_plan)
    timing_by_scene = _timing_by_scene_id(timing_plan)
    player_scenes = []
    for scene in scenes:
        timing = timing_by_scene.get(str(scene.get("scene_id")), {})
        player_scenes.append(
            {
                "scene_id": scene.get("scene_id", ""),
                "source_segment_id": scene.get("source_segment_id"),
                "start_time": scene.get("start_time"),
                "end_time": scene.get("end_time"),
                "source_summary": scene.get("source_summary", ""),
                "narrative_role": scene.get("narrative_role", ""),
                "voiceover": _scene_text(scene),
                "translated_text": scene.get("translated_text", ""),
                "visual_action": scene.get("visual_action", ""),
                "timing_action": timing.get("timing_action", ""),
                "recommendation": timing.get("recommendation", ""),
                "source_duration": timing.get("source_duration"),
                "estimated_voiceover_duration": timing.get("estimated_voiceover_duration"),
            }
        )
    return player_scenes


def _require_scenes(data: Any) -> list[dict[str, Any]]:
    if not isinstance(data, dict) or not isinstance(data.get("scenes"), list):
        raise SnvmError("Scene plan must contain a 'scenes' list.")
    return data["scenes"]


def _timing_by_scene_id(timing_plan: Any | None) -> dict[str, dict[str, Any]]:
    if not isinstance(timing_plan, dict) or not isinstance(timing_plan.get("scenes"), list):
        return {}
    return {
        str(scene.get("scene_id")): scene
        for scene in timing_plan["scenes"]
        if isinstance(scene, dict)
    }


def _scene_text(scene: dict[str, Any]) -> str:
    return str(
        scene.get("reviewed_voiceover")
        or scene.get("final_voiceover")
        or scene.get("subtitle_text")
        or scene.get("rewritten_voiceover")
        or ""
    ).strip()


def _browser_path(video_path: Path, output_dir: Path) -> str:
    try:
        relative = os.path.relpath(video_path.resolve(), output_dir.resolve())
        if not relative.startswith(".."):
            return Path(relative).as_posix()
    except ValueError:
        pass
    return video_path.resolve().as_uri()


def _html(payload: dict[str, Any]) -> str:
    embedded_payload = json.dumps(payload, ensure_ascii=False)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Swiss Narrative Video Maker Review Player</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f6f3ee;
      --panel: #ffffff;
      --text: #1d2528;
      --muted: #667176;
      --line: #d8d1c5;
      --accent: #d04437;
      --accent-2: #0f766e;
      --warn: #a16207;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Segoe UI, Microsoft YaHei, Arial, sans-serif;
      color: var(--text);
      background: var(--bg);
    }}
    header {{
      padding: 14px 20px;
      border-bottom: 1px solid var(--line);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      background: #fffaf2;
    }}
    h1 {{
      font-size: 18px;
      margin: 0;
      font-weight: 650;
    }}
    main {{
      display: grid;
      grid-template-columns: minmax(520px, 1.2fr) minmax(420px, 0.8fr);
      min-height: calc(100vh - 58px);
    }}
    .player {{
      padding: 18px;
      border-right: 1px solid var(--line);
    }}
    video {{
      width: 100%;
      max-height: 68vh;
      background: #111;
      border: 1px solid var(--line);
    }}
    .transport {{
      display: flex;
      align-items: center;
      gap: 8px;
      margin-top: 12px;
      flex-wrap: wrap;
    }}
    button, select, input, textarea {{
      font: inherit;
    }}
    button {{
      border: 1px solid var(--line);
      background: var(--panel);
      color: var(--text);
      padding: 8px 10px;
      cursor: pointer;
    }}
    button.primary {{
      background: var(--accent-2);
      border-color: var(--accent-2);
      color: white;
    }}
    button.warn {{
      background: #fff7ed;
      border-color: #fdba74;
      color: #7c2d12;
    }}
    .side {{
      padding: 18px;
      overflow: auto;
      max-height: calc(100vh - 58px);
    }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      padding: 14px;
      margin-bottom: 14px;
    }}
    .label {{
      font-size: 12px;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0;
      margin-bottom: 4px;
    }}
    .scene-id {{
      font-size: 22px;
      font-weight: 700;
      margin-bottom: 4px;
    }}
    .meta {{
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
    }}
    .text-block {{
      line-height: 1.6;
      white-space: pre-wrap;
    }}
    .grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }}
    textarea {{
      width: 100%;
      min-height: 90px;
      resize: vertical;
      padding: 9px;
      border: 1px solid var(--line);
      background: white;
      color: var(--text);
    }}
    select, input {{
      width: 100%;
      padding: 8px;
      border: 1px solid var(--line);
      background: white;
    }}
    .notes-list {{
      display: flex;
      flex-direction: column;
      gap: 8px;
      max-height: 260px;
      overflow: auto;
    }}
    .note {{
      border: 1px solid var(--line);
      padding: 8px;
      background: #fffdf8;
      font-size: 13px;
    }}
    .note strong {{ color: var(--accent); }}
    .status {{
      color: var(--muted);
      font-size: 13px;
    }}
    @media (max-width: 980px) {{
      main {{ grid-template-columns: 1fr; }}
      .player {{ border-right: 0; border-bottom: 1px solid var(--line); }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>Swiss Narrative Video Maker · Alignment Review</h1>
    <div class="status" id="status">Loading…</div>
  </header>
  <main>
    <section class="player">
      <video id="video" controls></video>
      <div class="transport">
        <button id="backScene">上一段</button>
        <button id="replayScene">重播当前段</button>
        <button id="nextScene">下一段</button>
        <button id="markLate" class="warn">中文滞后</button>
        <button id="markEarly" class="warn">中文提前</button>
        <button id="markMismatch" class="warn">画面对不上</button>
        <button id="markMaterial" class="warn">需要补素材</button>
      </div>
    </section>
    <aside class="side">
      <section class="panel">
        <div class="scene-id" id="sceneId">—</div>
        <div class="meta" id="sceneMeta">—</div>
      </section>
      <section class="panel">
        <div class="label">中文配音</div>
        <div class="text-block" id="voiceover">—</div>
      </section>
      <section class="panel grid">
        <div>
          <div class="label">Timing Action</div>
          <div id="timingAction">—</div>
        </div>
        <div>
          <div class="label">Visual Action</div>
          <div id="visualAction">—</div>
        </div>
      </section>
      <section class="panel">
        <div class="label">Recommendation</div>
        <div class="text-block" id="recommendation">—</div>
      </section>
      <section class="panel">
        <div class="label">新增标记</div>
        <div class="grid">
          <label>问题类型
            <select id="issueType">
              <option value="voiceover_late">中文滞后</option>
              <option value="voiceover_early">中文提前</option>
              <option value="visual_mismatch">画面对不上</option>
              <option value="needs_material">需要补素材</option>
              <option value="copy_too_long">文案太长</option>
              <option value="duplicate_fact">重复事实</option>
              <option value="other">其他</option>
            </select>
          </label>
          <label>严重程度
            <select id="severity">
              <option value="medium">medium</option>
              <option value="low">low</option>
              <option value="high">high</option>
            </select>
          </label>
        </div>
        <label>备注
          <textarea id="noteText" placeholder="例如：中文已经讲到下一段，但画面还停在火车准点率。"></textarea>
        </label>
        <div class="transport">
          <button id="addNote" class="primary">记录当前时间点</button>
          <button id="exportNotes">导出 alignment_notes.json</button>
          <button id="clearNotes">清空</button>
        </div>
      </section>
      <section class="panel">
        <div class="label">已记录标记</div>
        <div class="notes-list" id="notesList"></div>
      </section>
    </aside>
  </main>
  <script>
    const embeddedData = {embedded_payload};
    const state = {{
      data: null,
      scenes: [],
      currentSceneIndex: 0,
      notes: []
    }};

    const video = document.getElementById("video");
    const statusEl = document.getElementById("status");
    const sceneIdEl = document.getElementById("sceneId");
    const sceneMetaEl = document.getElementById("sceneMeta");
    const voiceoverEl = document.getElementById("voiceover");
    const timingActionEl = document.getElementById("timingAction");
    const visualActionEl = document.getElementById("visualAction");
    const recommendationEl = document.getElementById("recommendation");
    const issueTypeEl = document.getElementById("issueType");
    const severityEl = document.getElementById("severity");
    const noteTextEl = document.getElementById("noteText");
    const notesListEl = document.getElementById("notesList");

    state.data = embeddedData;
    state.scenes = embeddedData.scenes || [];
    video.src = embeddedData.video;
    statusEl.textContent = `${{state.scenes.length}} scenes loaded`;
    updateScene();

    video.addEventListener("timeupdate", () => {{
      const nextIndex = sceneIndexAt(video.currentTime);
      if (nextIndex !== state.currentSceneIndex) {{
        state.currentSceneIndex = nextIndex;
        updateScene();
      }}
    }});

    document.getElementById("backScene").addEventListener("click", () => jumpScene(state.currentSceneIndex - 1));
    document.getElementById("nextScene").addEventListener("click", () => jumpScene(state.currentSceneIndex + 1));
    document.getElementById("replayScene").addEventListener("click", () => jumpScene(state.currentSceneIndex));
    document.getElementById("addNote").addEventListener("click", () => addNote());
    document.getElementById("exportNotes").addEventListener("click", () => exportNotes());
    document.getElementById("clearNotes").addEventListener("click", () => {{
      if (confirm("Clear all notes?")) {{
        state.notes = [];
        renderNotes();
      }}
    }});
    document.getElementById("markLate").addEventListener("click", () => quickNote("voiceover_late"));
    document.getElementById("markEarly").addEventListener("click", () => quickNote("voiceover_early"));
    document.getElementById("markMismatch").addEventListener("click", () => quickNote("visual_mismatch"));
    document.getElementById("markMaterial").addEventListener("click", () => quickNote("needs_material"));

    function sceneIndexAt(time) {{
      if (!state.scenes.length) return 0;
      const index = state.scenes.findIndex(scene => {{
        const start = Number(scene.start_time || 0);
        const end = Number(scene.end_time || start);
        return time >= start && time < end;
      }});
      if (index >= 0) return index;
      if (time >= Number(state.scenes[state.scenes.length - 1].end_time || 0)) return state.scenes.length - 1;
      return 0;
    }}

    function jumpScene(index) {{
      if (!state.scenes.length) return;
      state.currentSceneIndex = Math.max(0, Math.min(state.scenes.length - 1, index));
      const scene = state.scenes[state.currentSceneIndex];
      video.currentTime = Number(scene.start_time || 0);
      updateScene();
      video.play();
    }}

    function updateScene() {{
      const scene = state.scenes[state.currentSceneIndex];
      if (!scene) return;
      sceneIdEl.textContent = scene.scene_id || "—";
      sceneMetaEl.textContent = `${{fmt(scene.start_time)}} - ${{fmt(scene.end_time)}} · source segment ${{scene.source_segment_id ?? "—"}} · ${{scene.narrative_role || "no role"}}`;
      voiceoverEl.textContent = scene.voiceover || "—";
      timingActionEl.textContent = scene.timing_action || "—";
      visualActionEl.textContent = scene.visual_action || "—";
      recommendationEl.textContent = scene.recommendation || "—";
    }}

    function quickNote(type) {{
      issueTypeEl.value = type;
      addNote();
    }}

    function addNote() {{
      const scene = state.scenes[state.currentSceneIndex];
      if (!scene) return;
      const note = {{
        time: Number(video.currentTime.toFixed(3)),
        scene_id: scene.scene_id,
        source_segment_id: scene.source_segment_id,
        issue_type: issueTypeEl.value,
        severity: severityEl.value,
        note: noteTextEl.value.trim(),
        voiceover: scene.voiceover || "",
        timing_action: scene.timing_action || "",
        visual_action: scene.visual_action || ""
      }};
      state.notes.push(note);
      noteTextEl.value = "";
      renderNotes();
    }}

    function renderNotes() {{
      notesListEl.innerHTML = "";
      state.notes.forEach((note, index) => {{
        const item = document.createElement("div");
        item.className = "note";
        item.innerHTML = `<strong>${{index + 1}}. ${{note.scene_id}}</strong> · ${{fmt(note.time)}} · ${{note.issue_type}} · ${{note.severity}}<br>${{escapeHtml(note.note || "(no note)")}}`;
        item.addEventListener("click", () => {{
          video.currentTime = note.time;
          state.currentSceneIndex = sceneIndexAt(note.time);
          updateScene();
        }});
        notesListEl.appendChild(item);
      }});
    }}

    function exportNotes() {{
      const payload = {{
        generated_at: new Date().toISOString(),
        source_video: state.data?.video || "",
        scene_plan: state.data?.scene_plan || "",
        timing_plan: state.data?.timing_plan || "",
        notes: state.notes
      }};
      const blob = new Blob([JSON.stringify(payload, null, 2)], {{ type: "application/json" }});
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = "alignment_notes.json";
      link.click();
      URL.revokeObjectURL(link.href);
    }}

    function fmt(value) {{
      const seconds = Number(value || 0);
      const mins = Math.floor(seconds / 60);
      const secs = Math.floor(seconds % 60).toString().padStart(2, "0");
      return `${{mins}}:${{secs}}`;
    }}

    function escapeHtml(value) {{
      return String(value).replace(/[&<>"']/g, char => ({{
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;"
      }}[char]));
    }}
  </script>
</body>
</html>
"""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
