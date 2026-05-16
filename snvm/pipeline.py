from pathlib import Path

from .errors import SnvmError


OUTPUT_SUBDIRS = ("assets", "clips", "voiceover", "subtitles", "logs")


def initialize_project_output(output_dir: Path) -> list[Path]:
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        created = [output_dir]

        for name in OUTPUT_SUBDIRS:
            path = output_dir / name
            path.mkdir(parents=True, exist_ok=True)
            created.append(path)

        return created
    except OSError as exc:
        raise SnvmError(f"Could not create output directory '{output_dir}': {exc}") from exc

