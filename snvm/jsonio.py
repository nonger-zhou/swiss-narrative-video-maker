import json
from pathlib import Path
from typing import Any

from .errors import SnvmError


def read_json(path: Path) -> Any:
    if not path.exists():
        raise SnvmError(f"Required JSON file does not exist: {path}")

    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise SnvmError(f"Invalid JSON in {path}: {exc}") from exc
    except OSError as exc:
        raise SnvmError(f"Could not read {path}: {exc}") from exc


def write_json(path: Path, data: Any) -> Path:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as exc:
        raise SnvmError(f"Could not write {path}: {exc}") from exc
    return path
