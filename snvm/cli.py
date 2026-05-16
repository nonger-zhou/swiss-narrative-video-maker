import argparse
import sys
from pathlib import Path

from .config import Settings, load_settings
from .errors import SnvmError
from .pipeline import initialize_project_output
from .source import prepare_source, save_source_metadata


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "init":
        return run_init(args.output)

    if args.command == "doctor":
        return run_doctor(args.source)

    if args.command == "prepare-source":
        return run_prepare_source(args.input, args.output)

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


def _print_settings(settings: Settings) -> None:
    print("Configuration")
    print(f"- OpenAI model: {settings.openai_model}")
    print(f"- Whisper model: {settings.whisper_model}")
    print(f"- Edge TTS voice: {settings.edge_tts_voice}")
    if settings.openai_api_key:
        print("- OpenAI API key: set")
    else:
        print("- OpenAI API key: missing")


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
