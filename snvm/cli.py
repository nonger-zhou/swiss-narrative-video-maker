import argparse
import shutil
import sys
from pathlib import Path

from .analysis import analyze_transcript
from .composer import compose_draft_video, compose_scene_based_draft, is_ffmpeg_available
from .config import Settings, load_settings
from .errors import SnvmError
from .fact_check import generate_fact_check_summary
from .pipeline import initialize_project_output
from .review import apply_scene_review, generate_scene_review
from .review_player import generate_review_player
from .revision_plan import generate_revision_plan
from .scene_plan import generate_scene_plan
from .script_edits import apply_script_edits
from .source import prepare_source, save_source_metadata
from .timing import generate_timing_plan
from .transcription import is_faster_whisper_available, transcribe_source
from .voiceover import generate_voiceover, is_edge_tts_available
from .visual_replacements import generate_visual_replacement_manifest


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "init":
        return run_init(args.output)

    if args.command == "doctor":
        return run_doctor(args.source)

    if args.command == "prepare-source":
        return run_prepare_source(args.input, args.output)

    if args.command == "transcribe":
        return run_transcribe(
            args.source,
            args.output,
            args.model,
            args.device,
            args.compute_type,
            args.language,
        )

    if args.command == "analyze":
        return run_analyze(args.transcript, args.output)

    if args.command == "scene-plan":
        return run_scene_plan(args.translation, args.structure, args.output)

    if args.command == "review":
        return run_review(args.transcript, args.translation, args.scene_plan, args.output)

    if args.command == "apply-review":
        return run_apply_review(args.scene_plan, args.review, args.output)

    if args.command == "timing-plan":
        return run_timing_plan(args.scene_plan, args.output)

    if args.command == "visual-replacements":
        return run_visual_replacements(args.scene_plan, args.output)

    if args.command == "voiceover":
        return run_voiceover(args.scene_plan, args.output, args.voice)

    if args.command == "compose":
        return run_compose(args.source, args.scene_plan, args.voiceover, args.output)

    if args.command == "compose-scenes":
        return run_compose_scenes(
            args.source,
            args.scene_plan,
            args.timing_plan,
            args.voiceover,
            args.visual_replacements,
            args.output,
        )

    if args.command == "review-player":
        return run_review_player(
            args.video,
            args.scene_plan,
            args.timing_plan,
            args.review,
            args.output,
        )

    if args.command == "revision-plan":
        return run_revision_plan(
            args.notes,
            args.scene_plan,
            args.timing_plan,
            args.output,
        )

    if args.command == "fact-check-summary":
        return run_fact_check_summary(
            args.fact_checks,
            args.scene_plan,
            args.output,
        )

    if args.command == "apply-script-edits":
        return run_apply_script_edits(
            args.scene_plan,
            args.edits,
            args.output,
        )

    if args.command == "refresh-draft":
        return run_refresh_draft(
            args.source,
            args.scene_plan,
            args.script_edits,
            args.visual_replacements,
            args.output,
            args.voice,
            args.skip_script_edits,
            args.skip_compose,
            args.skip_review_player,
            args.dry_run,
        )

    if args.command == "make-draft":
        return run_make_draft(args.input, args.output)

    parser.print_help()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="snvm",
        description="Swiss Narrative Video Maker local command-line pipeline.",
    )
    subparsers = parser.add_subparsers(dest="command")

    init_parser = subparsers.add_parser("init", help="Create the local output folder structure.")
    init_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("output"),
        help="Directory for generated intermediate files and videos.",
    )

    doctor_parser = subparsers.add_parser("doctor", help="Check local configuration.")
    doctor_parser.add_argument(
        "-s",
        "--source",
        help="Optional YouTube URL or local mp4 path to validate.",
    )

    source_parser = subparsers.add_parser(
        "prepare-source",
        help="Prepare a YouTube URL or local mp4 as output/source.mp4.",
    )
    source_parser.add_argument(
        "input",
        help="YouTube URL or local mp4 path.",
    )
    source_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("output"),
        help="Directory for generated files.",
    )

    transcribe_parser = subparsers.add_parser(
        "transcribe",
        help="Transcribe output/source.mp4 and write output/transcript.json.",
    )
    transcribe_parser.add_argument(
        "-s",
        "--source",
        type=Path,
        default=None,
        help="Video file to transcribe. Defaults to <output>/source.mp4.",
    )
    transcribe_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("output"),
        help="Directory for generated files.",
    )
    transcribe_parser.add_argument(
        "-m",
        "--model",
        default=None,
        help="faster-whisper model name. Defaults to WHISPER_MODEL from .env or 'small'.",
    )
    transcribe_parser.add_argument(
        "--device",
        default="cpu",
        help="Device passed to faster-whisper, for example 'cpu' or 'cuda'.",
    )
    transcribe_parser.add_argument(
        "--compute-type",
        default="int8",
        help="Compute type passed to faster-whisper, for example 'int8' or 'float16'.",
    )
    transcribe_parser.add_argument(
        "--language",
        default=None,
        help="Optional source language code. Omit to let faster-whisper detect it.",
    )

    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Translate transcript and analyze narrative structure with OpenAI.",
    )
    analyze_parser.add_argument(
        "-t",
        "--transcript",
        type=Path,
        default=None,
        help="Transcript JSON. Defaults to <output>/transcript.json.",
    )
    analyze_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("output"),
        help="Directory for generated files.",
    )

    scene_plan_parser = subparsers.add_parser(
        "scene-plan",
        help="Generate output/scene_plan.json from translation and structure analysis.",
    )
    scene_plan_parser.add_argument(
        "--translation",
        type=Path,
        default=None,
        help="Translation JSON. Defaults to <output>/translation.json.",
    )
    scene_plan_parser.add_argument(
        "--structure",
        type=Path,
        default=None,
        help="Structure analysis JSON. Defaults to <output>/structure_analysis.json.",
    )
    scene_plan_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("output"),
        help="Directory for generated files.",
    )

    review_parser = subparsers.add_parser(
        "review",
        help="Generate human-editable scene review files.",
    )
    review_parser.add_argument(
        "--transcript",
        type=Path,
        default=None,
        help="Transcript JSON. Defaults to <output>/transcript.json.",
    )
    review_parser.add_argument(
        "--translation",
        type=Path,
        default=None,
        help="Translation JSON. Defaults to <output>/translation.json.",
    )
    review_parser.add_argument(
        "--scene-plan",
        type=Path,
        default=None,
        help="Scene plan JSON. Defaults to <output>/scene_plan.json.",
    )
    review_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("output"),
        help="Directory for generated files.",
    )

    apply_review_parser = subparsers.add_parser(
        "apply-review",
        help="Apply edited scene_review.json to create scene_plan.reviewed.json.",
    )
    apply_review_parser.add_argument(
        "--scene-plan",
        type=Path,
        default=None,
        help="Scene plan JSON. Defaults to <output>/scene_plan.json.",
    )
    apply_review_parser.add_argument(
        "--review",
        type=Path,
        default=None,
        help="Scene review JSON. Defaults to <output>/scene_review.json.",
    )
    apply_review_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("output"),
        help="Directory for generated files.",
    )

    timing_parser = subparsers.add_parser(
        "timing-plan",
        help="Generate per-scene timing recommendations before composition.",
    )
    timing_parser.add_argument(
        "--scene-plan",
        type=Path,
        default=None,
        help="Scene plan JSON. Defaults to <output>/scene_plan.reviewed.json if present, else <output>/scene_plan.json.",
    )
    timing_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("output"),
        help="Directory for generated files.",
    )

    voiceover_parser = subparsers.add_parser(
        "voiceover",
        help="Generate Chinese voiceover audio from output/scene_plan.json.",
    )
    voiceover_parser.add_argument(
        "--scene-plan",
        type=Path,
        default=None,
        help="Scene plan JSON. Defaults to <output>/scene_plan.json.",
    )
    voiceover_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("output"),
        help="Directory for generated files.",
    )
    voiceover_parser.add_argument(
        "--voice",
        default=None,
        help="Edge TTS voice. Defaults to EDGE_TTS_VOICE from .env.",
    )

    replacements_parser = subparsers.add_parser(
        "visual-replacements",
        help="Generate output/visual_replacements.json for scene-level visual swaps.",
    )
    replacements_parser.add_argument(
        "--scene-plan",
        type=Path,
        default=None,
        help="Scene plan JSON. Defaults to <output>/scene_plan.reviewed.json if present, else <output>/scene_plan.json.",
    )
    replacements_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("output"),
        help="Directory for generated files.",
    )

    compose_parser = subparsers.add_parser(
        "compose",
        help="Compose source video, voiceover, and subtitles into output/final.mp4.",
    )
    compose_parser.add_argument(
        "--source",
        type=Path,
        default=None,
        help="Source video. Defaults to <output>/source.mp4.",
    )
    compose_parser.add_argument(
        "--scene-plan",
        type=Path,
        default=None,
        help="Scene plan JSON. Defaults to <output>/scene_plan.json.",
    )
    compose_parser.add_argument(
        "--voiceover",
        type=Path,
        default=None,
        help="Voiceover mp3. Defaults to <output>/voiceover.mp3.",
    )
    compose_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("output"),
        help="Directory for generated files.",
    )

    scene_compose_parser = subparsers.add_parser(
        "compose-scenes",
        help="Compose a scene-based draft using scene_plan and timing_plan.",
    )
    scene_compose_parser.add_argument(
        "--source",
        type=Path,
        default=None,
        help="Source video. Defaults to <output>/source.mp4.",
    )
    scene_compose_parser.add_argument(
        "--scene-plan",
        type=Path,
        default=None,
        help="Scene plan JSON. Defaults to <output>/scene_plan.reviewed.json if present, else <output>/scene_plan.json.",
    )
    scene_compose_parser.add_argument(
        "--timing-plan",
        type=Path,
        default=None,
        help="Timing plan JSON. Defaults to <output>/timing_plan.json.",
    )
    scene_compose_parser.add_argument(
        "--voiceover",
        type=Path,
        default=None,
        help="Voiceover mp3. Defaults to <output>/voiceover.mp3.",
    )
    scene_compose_parser.add_argument(
        "--visual-replacements",
        type=Path,
        default=None,
        help="Optional visual replacement manifest. Defaults to <output>/visual_replacements.json if present.",
    )
    scene_compose_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("output"),
        help="Directory for generated files.",
    )

    review_player_parser = subparsers.add_parser(
        "review-player",
        help="Generate a local HTML video player for alignment issue marking.",
    )
    review_player_parser.add_argument(
        "--video",
        type=Path,
        default=None,
        help="Video to review. Defaults to <output>/final_scenes.mp4 if present, else <output>/final.mp4.",
    )
    review_player_parser.add_argument(
        "--scene-plan",
        type=Path,
        default=None,
        help="Scene plan JSON. Defaults to <output>/scene_plan.reviewed.json if present, else <output>/scene_plan.json.",
    )
    review_player_parser.add_argument(
        "--timing-plan",
        type=Path,
        default=None,
        help="Timing plan JSON. Defaults to <output>/timing_plan.json if present.",
    )
    review_player_parser.add_argument(
        "--review",
        type=Path,
        default=None,
        help="Scene review JSON. Defaults to <output>/scene_review.json if present.",
    )
    review_player_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("output"),
        help="Directory for generated files.",
    )

    revision_parser = subparsers.add_parser(
        "revision-plan",
        help="Summarize exported alignment_notes.json into a scene revision plan.",
    )
    revision_parser.add_argument(
        "--notes",
        type=Path,
        default=None,
        help="Alignment notes JSON. Defaults to <output>/alignment_notes.json.",
    )
    revision_parser.add_argument(
        "--scene-plan",
        type=Path,
        default=None,
        help="Scene plan JSON. Defaults to <output>/scene_plan.reviewed.json if present, else <output>/scene_plan.json.",
    )
    revision_parser.add_argument(
        "--timing-plan",
        type=Path,
        default=None,
        help="Timing plan JSON. Defaults to <output>/timing_plan.json if present.",
    )
    revision_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("output"),
        help="Directory for generated files.",
    )

    fact_check_parser = subparsers.add_parser(
        "fact-check-summary",
        help="Summarize fact_check_notes.json exported from the review player.",
    )
    fact_check_parser.add_argument(
        "--fact-checks",
        type=Path,
        default=None,
        help="Fact-check notes JSON. Defaults to <output>/fact_check_notes.json.",
    )
    fact_check_parser.add_argument(
        "--scene-plan",
        type=Path,
        default=None,
        help="Scene plan JSON. Defaults to <output>/scene_plan.reviewed.json if present, else <output>/scene_plan.json.",
    )
    fact_check_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("output"),
        help="Directory for generated files.",
    )

    script_edits_parser = subparsers.add_parser(
        "apply-script-edits",
        help="Apply script_edits.json to create scene_plan.reviewed.json.",
    )
    script_edits_parser.add_argument(
        "--scene-plan",
        type=Path,
        default=None,
        help="Scene plan JSON. Defaults to <output>/scene_plan.reviewed.json if present, else <output>/scene_plan.json.",
    )
    script_edits_parser.add_argument(
        "--edits",
        type=Path,
        default=None,
        help="Script edits JSON. Defaults to <output>/script_edits.json.",
    )
    script_edits_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("output"),
        help="Directory for generated files.",
    )

    refresh_parser = subparsers.add_parser(
        "refresh-draft",
        help="Apply edits and regenerate voiceover, timing, scene draft, and review player.",
    )
    refresh_parser.add_argument(
        "--source",
        type=Path,
        default=None,
        help="Source video. Defaults to <output>/source.mp4.",
    )
    refresh_parser.add_argument(
        "--scene-plan",
        type=Path,
        default=None,
        help="Base scene plan. Defaults to <output>/scene_plan.reviewed.json if present, else <output>/scene_plan.json.",
    )
    refresh_parser.add_argument(
        "--script-edits",
        type=Path,
        default=None,
        help="Optional script edits JSON. Defaults to <output>/script_edits.json if present.",
    )
    refresh_parser.add_argument(
        "--visual-replacements",
        type=Path,
        default=None,
        help="Optional visual replacement manifest. Defaults to <output>/visual_replacements.json if present.",
    )
    refresh_parser.add_argument(
        "--voice",
        default=None,
        help="Edge TTS voice. Defaults to EDGE_TTS_VOICE from .env.",
    )
    refresh_parser.add_argument(
        "--skip-script-edits",
        action="store_true",
        help="Do not apply script_edits.json before rebuilding.",
    )
    refresh_parser.add_argument(
        "--skip-compose",
        action="store_true",
        help="Regenerate script-dependent audio and timing, but skip video composition.",
    )
    refresh_parser.add_argument(
        "--skip-review-player",
        action="store_true",
        help="Do not regenerate review_player.html.",
    )
    refresh_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned rebuild steps without running TTS or ffmpeg.",
    )
    refresh_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("output"),
        help="Directory for generated files.",
    )

    draft_parser = subparsers.add_parser(
        "make-draft",
        help="Run the basic pipeline from source input to final draft video.",
    )
    draft_parser.add_argument(
        "input",
        help="YouTube URL or local mp4 path.",
    )
    draft_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("output"),
        help="Directory for generated files.",
    )

    return parser


def run_init(output_dir: Path) -> int:
    try:
        created = initialize_project_output(output_dir)
    except SnvmError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print("Output folder ready.")
    for path in created:
        print(f"- {path}")
    return 0


def run_doctor(source: str | None) -> int:
    settings = load_settings()
    _print_settings(settings)

    if source:
        return _validate_source(source)

    return 0


def run_prepare_source(input_value: str, output_dir: Path) -> int:
    try:
        metadata = prepare_source(input_value, output_dir)
        metadata_path = save_source_metadata(metadata, output_dir)
    except SnvmError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print("Source video ready.")
    print(f"- Source: {metadata.source_path}")
    print(f"- Metadata: {metadata_path}")
    return 0


def run_transcribe(
    source_path: Path | None,
    output_dir: Path,
    model_name: str | None,
    device: str,
    compute_type: str,
    language: str | None,
) -> int:
    settings = load_settings()
    source = source_path or output_dir / "source.mp4"
    model = model_name or settings.whisper_model

    try:
        transcript_path = transcribe_source(
            source,
            output_dir,
            model,
            device=device,
            compute_type=compute_type,
            language=language,
        )
    except SnvmError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print("Transcript ready.")
    print(f"- Source: {source}")
    print(f"- Transcript: {transcript_path}")
    return 0


def run_analyze(transcript_path: Path | None, output_dir: Path) -> int:
    settings = load_settings()
    transcript = transcript_path or output_dir / "transcript.json"

    try:
        translation_path, structure_path = analyze_transcript(transcript, output_dir, settings)
    except SnvmError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print("Analysis ready.")
    print(f"- Translation: {translation_path}")
    print(f"- Structure analysis: {structure_path}")
    return 0


def run_scene_plan(
    translation_path: Path | None,
    structure_path: Path | None,
    output_dir: Path,
) -> int:
    translation = translation_path or output_dir / "translation.json"
    structure = structure_path or output_dir / "structure_analysis.json"

    try:
        scene_plan_path = generate_scene_plan(translation, structure, output_dir)
    except SnvmError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print("Scene plan ready.")
    print(f"- Scene plan: {scene_plan_path}")
    return 0


def run_review(
    transcript_path: Path | None,
    translation_path: Path | None,
    scene_plan_path: Path | None,
    output_dir: Path,
) -> int:
    transcript = transcript_path or output_dir / "transcript.json"
    translation = translation_path or output_dir / "translation.json"
    scene_plan = scene_plan_path or output_dir / "scene_plan.json"

    try:
        paths = generate_scene_review(transcript, translation, scene_plan, output_dir)
    except SnvmError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print("Scene review ready.")
    print(f"- JSON: {paths.json_path}")
    print(f"- Markdown: {paths.markdown_path}")
    return 0


def run_apply_review(
    scene_plan_path: Path | None,
    review_path: Path | None,
    output_dir: Path,
) -> int:
    scene_plan = scene_plan_path or output_dir / "scene_plan.json"
    review = review_path or output_dir / "scene_review.json"

    try:
        reviewed_scene_plan = apply_scene_review(scene_plan, review, output_dir)
    except SnvmError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print("Reviewed scene plan ready.")
    print(f"- Scene plan: {reviewed_scene_plan}")
    return 0


def run_timing_plan(scene_plan_path: Path | None, output_dir: Path) -> int:
    default_reviewed = output_dir / "scene_plan.reviewed.json"
    scene_plan = scene_plan_path or (
        default_reviewed if default_reviewed.exists() else output_dir / "scene_plan.json"
    )

    try:
        timing_plan = generate_timing_plan(scene_plan, output_dir)
    except SnvmError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print("Timing plan ready.")
    print(f"- Timing plan: {timing_plan}")
    return 0


def run_visual_replacements(scene_plan_path: Path | None, output_dir: Path) -> int:
    default_reviewed = output_dir / "scene_plan.reviewed.json"
    scene_plan = scene_plan_path or (
        default_reviewed if default_reviewed.exists() else output_dir / "scene_plan.json"
    )

    try:
        manifest_path = generate_visual_replacement_manifest(scene_plan, output_dir)
    except SnvmError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print("Visual replacement manifest ready.")
    print(f"- Manifest: {manifest_path}")
    return 0


def run_voiceover(scene_plan_path: Path | None, output_dir: Path, voice: str | None) -> int:
    settings = load_settings()
    scene_plan = scene_plan_path or output_dir / "scene_plan.json"
    selected_voice = voice or settings.edge_tts_voice

    try:
        audio_path = generate_voiceover(scene_plan, output_dir, selected_voice)
    except SnvmError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print("Voiceover ready.")
    print(f"- Voice: {selected_voice}")
    print(f"- Audio: {audio_path}")
    return 0


def run_compose(
    source_path: Path | None,
    scene_plan_path: Path | None,
    voiceover_path: Path | None,
    output_dir: Path,
) -> int:
    source = source_path or output_dir / "source.mp4"
    scene_plan = scene_plan_path or output_dir / "scene_plan.json"
    voiceover = voiceover_path or output_dir / "voiceover.mp3"

    try:
        final_path = compose_draft_video(source, scene_plan, voiceover, output_dir)
    except SnvmError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print("Draft video ready.")
    print(f"- Final: {final_path}")
    return 0


def run_compose_scenes(
    source_path: Path | None,
    scene_plan_path: Path | None,
    timing_plan_path: Path | None,
    voiceover_path: Path | None,
    visual_replacements_path: Path | None,
    output_dir: Path,
) -> int:
    source = source_path or output_dir / "source.mp4"
    default_reviewed = output_dir / "scene_plan.reviewed.json"
    scene_plan = scene_plan_path or (
        default_reviewed if default_reviewed.exists() else output_dir / "scene_plan.json"
    )
    timing_plan = timing_plan_path or output_dir / "timing_plan.json"
    voiceover = voiceover_path or output_dir / "voiceover.mp3"
    default_replacements = output_dir / "visual_replacements.json"
    visual_replacements = visual_replacements_path or (
        default_replacements if default_replacements.exists() else None
    )

    try:
        final_path = compose_scene_based_draft(
            source,
            scene_plan,
            timing_plan,
            voiceover,
            output_dir,
            visual_replacements,
        )
    except SnvmError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print("Scene-based draft video ready.")
    print(f"- Final: {final_path}")
    return 0


def run_review_player(
    video_path: Path | None,
    scene_plan_path: Path | None,
    timing_plan_path: Path | None,
    review_path: Path | None,
    output_dir: Path,
) -> int:
    default_scene_video = output_dir / "final_scenes.mp4"
    video = video_path or (default_scene_video if default_scene_video.exists() else output_dir / "final.mp4")
    default_reviewed = output_dir / "scene_plan.reviewed.json"
    scene_plan = scene_plan_path or (
        default_reviewed if default_reviewed.exists() else output_dir / "scene_plan.json"
    )
    default_timing = output_dir / "timing_plan.json"
    timing_plan = timing_plan_path or (default_timing if default_timing.exists() else None)
    default_review = output_dir / "scene_review.json"
    review = review_path or (default_review if default_review.exists() else None)

    try:
        html_path = generate_review_player(video, scene_plan, timing_plan, review, output_dir)
    except SnvmError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print("Review player ready.")
    print(f"- HTML: {html_path}")
    return 0


def run_revision_plan(
    notes_path: Path | None,
    scene_plan_path: Path | None,
    timing_plan_path: Path | None,
    output_dir: Path,
) -> int:
    notes = notes_path or output_dir / "alignment_notes.json"
    default_reviewed = output_dir / "scene_plan.reviewed.json"
    scene_plan = scene_plan_path or (
        default_reviewed if default_reviewed.exists() else output_dir / "scene_plan.json"
    )
    default_timing = output_dir / "timing_plan.json"
    timing_plan = timing_plan_path or (default_timing if default_timing.exists() else None)

    try:
        json_path, markdown_path = generate_revision_plan(notes, scene_plan, timing_plan, output_dir)
    except SnvmError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print("Revision plan ready.")
    print(f"- JSON: {json_path}")
    print(f"- Markdown: {markdown_path}")
    return 0


def run_fact_check_summary(
    fact_checks_path: Path | None,
    scene_plan_path: Path | None,
    output_dir: Path,
) -> int:
    fact_checks = fact_checks_path or output_dir / "fact_check_notes.json"
    default_reviewed = output_dir / "scene_plan.reviewed.json"
    scene_plan = scene_plan_path or (
        default_reviewed if default_reviewed.exists() else output_dir / "scene_plan.json"
    )

    try:
        json_path, markdown_path = generate_fact_check_summary(fact_checks, scene_plan, output_dir)
    except SnvmError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print("Fact-check summary ready.")
    print(f"- JSON: {json_path}")
    print(f"- Markdown: {markdown_path}")
    return 0


def run_apply_script_edits(
    scene_plan_path: Path | None,
    edits_path: Path | None,
    output_dir: Path,
) -> int:
    default_reviewed = output_dir / "scene_plan.reviewed.json"
    scene_plan = scene_plan_path or (
        default_reviewed if default_reviewed.exists() else output_dir / "scene_plan.json"
    )
    edits = edits_path or output_dir / "script_edits.json"

    try:
        reviewed_scene_plan = apply_script_edits(scene_plan, edits, output_dir)
    except SnvmError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print("Script edits applied.")
    print(f"- Scene plan: {reviewed_scene_plan}")
    return 0


def run_refresh_draft(
    source_path: Path | None,
    scene_plan_path: Path | None,
    script_edits_path: Path | None,
    visual_replacements_path: Path | None,
    output_dir: Path,
    voice: str | None,
    skip_script_edits: bool,
    skip_compose: bool,
    skip_review_player: bool,
    dry_run: bool,
) -> int:
    settings = load_settings()
    source = source_path or output_dir / "source.mp4"
    default_reviewed = output_dir / "scene_plan.reviewed.json"
    base_scene_plan = scene_plan_path or (
        default_reviewed if default_reviewed.exists() else output_dir / "scene_plan.json"
    )
    default_script_edits = output_dir / "script_edits.json"
    script_edits = script_edits_path or (
        default_script_edits if default_script_edits.exists() else None
    )
    default_replacements = output_dir / "visual_replacements.json"
    visual_replacements = visual_replacements_path or (
        default_replacements if default_replacements.exists() else None
    )
    selected_voice = voice or settings.edge_tts_voice
    scene_plan_after_edits = output_dir / "scene_plan.reviewed.json"
    scene_plan = (
        scene_plan_after_edits
        if script_edits and not skip_script_edits
        else base_scene_plan
    )
    timing_plan = output_dir / "timing_plan.json"
    voiceover = output_dir / "voiceover.mp3"
    final_video = output_dir / "final_scenes.mp4"

    if dry_run:
        print("Refresh draft plan:")
        if script_edits and not skip_script_edits:
            print(f"- Apply script edits: {script_edits} -> {scene_plan_after_edits}")
        elif skip_script_edits:
            print("- Skip script edits.")
        else:
            print("- No script_edits.json found; use existing scene plan.")
        print(f"- Scene plan: {scene_plan}")
        print(f"- Generate voiceover: {voiceover} (voice: {selected_voice})")
        print(f"- Generate timing plan: {timing_plan}")
        if skip_compose:
            print("- Skip scene-based video composition.")
        else:
            print(f"- Compose scene draft: {final_video}")
            if visual_replacements:
                print(f"- Use visual replacements: {visual_replacements}")
        if skip_review_player:
            print("- Skip review player generation.")
        else:
            print("- Generate review player HTML.")
        return 0

    try:
        if script_edits and not skip_script_edits:
            print("Running step: apply-script-edits")
            scene_plan = apply_script_edits(base_scene_plan, script_edits, output_dir)
        elif script_edits and skip_script_edits:
            print("Skipping script edits.")
        else:
            print("No script_edits.json found; using existing scene plan.")

        print("Running step: voiceover")
        voiceover = generate_voiceover(scene_plan, output_dir, selected_voice)

        print("Running step: timing-plan")
        timing_plan = generate_timing_plan(scene_plan, output_dir)

        video_for_player = output_dir / "final.mp4"
        if not skip_compose:
            print("Running step: compose-scenes")
            video_for_player = compose_scene_based_draft(
                source,
                scene_plan,
                timing_plan,
                voiceover,
                output_dir,
                visual_replacements,
            )
        elif final_video.exists():
            video_for_player = final_video

        if not skip_review_player:
            print("Running step: review-player")
            generate_review_player(
                video_for_player,
                scene_plan,
                timing_plan,
                output_dir / "scene_review.json",
                output_dir,
            )
    except SnvmError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print("Draft refresh complete.")
    print(f"- Scene plan: {scene_plan}")
    print(f"- Voiceover: {voiceover}")
    print(f"- Timing plan: {timing_plan}")
    if not skip_compose:
        print(f"- Video: {video_for_player}")
    if not skip_review_player:
        print(f"- Review player: {output_dir / 'review_player.html'}")
    return 0


def run_make_draft(input_value: str, output_dir: Path) -> int:
    steps = [
        ("prepare-source", lambda: run_prepare_source(input_value, output_dir)),
        ("transcribe", lambda: run_transcribe(None, output_dir, None, "cpu", "int8", None)),
        ("analyze", lambda: run_analyze(None, output_dir)),
        ("scene-plan", lambda: run_scene_plan(None, None, output_dir)),
        ("voiceover", lambda: run_voiceover(None, output_dir, None)),
        ("compose", lambda: run_compose(None, None, None, output_dir)),
    ]

    for name, step in steps:
        print(f"Running step: {name}")
        exit_code = step()
        if exit_code != 0:
            return exit_code

    print("Basic draft pipeline complete.")
    return 0


def _print_settings(settings: Settings) -> None:
    print("Configuration")
    print(f"- OpenAI model: {settings.openai_model}")
    print(f"- Whisper model: {settings.whisper_model}")
    print(f"- Edge TTS voice: {settings.edge_tts_voice}")
    if settings.openai_api_key:
        print("- OpenAI API key: set")
    else:
        print("- OpenAI API key: missing")

    if shutil.which("yt-dlp"):
        print("- yt-dlp: available")
    else:
        print("- yt-dlp: missing")

    if is_faster_whisper_available():
        print("- faster-whisper: available")
    else:
        print("- faster-whisper: missing")

    if is_edge_tts_available():
        print("- edge-tts: available")
    else:
        print("- edge-tts: missing")

    if is_ffmpeg_available():
        print("- ffmpeg: available")
    else:
        print("- ffmpeg: missing")


def _validate_source(source: str) -> int:
    if source.startswith(("http://", "https://")):
        print(f"- Source: URL detected ({source})")
        return 0

    path = Path(source)
    if not path.exists():
        print(f"Error: local source file does not exist: {path}", file=sys.stderr)
        return 1

    if path.suffix.lower() != ".mp4":
        print(f"Warning: expected an mp4 file, got: {path.name}")

    print(f"- Source: local file detected ({path})")
    return 0
