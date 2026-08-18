import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)


class HistoryService:
    """Local storage for completed ScenePilot analyses."""

    _valid_file_id = re.compile(r"^[A-Za-z0-9_-]+$")

    def __init__(self, storage_dir: Path | None = None) -> None:
        self.storage_dir = storage_dir or (
            Path(__file__).resolve().parents[1] / "data" / "analyses"
        )
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_analysis(
        self,
        *,
        file_id: str,
        filename: str,
        text_length: int,
        scene_count: int,
        researched_scene_count: int,
        production_intelligence: dict[str, Any],
    ) -> bool:
        if not self._is_valid_file_id(file_id):
            logger.warning("Refusing to save an analysis with an invalid file ID")
            return False

        record = {
            "file_id": file_id,
            "filename": filename,
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "text_length": text_length,
            "scene_count": scene_count,
            "researched_scene_count": researched_scene_count,
            "production_intelligence": production_intelligence,
        }
        destination = self._path_for(file_id)
        temporary = destination.with_suffix(".tmp")

        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            with temporary.open("w", encoding="utf-8") as handle:
                json.dump(record, handle, ensure_ascii=False, indent=2)
            temporary.replace(destination)
            return True
        except (OSError, TypeError, ValueError) as exc:
            logger.error("Could not save analysis history: %s", exc)
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
            return False

    def list_analyses(self) -> list[dict[str, Any]]:
        analyses: list[dict[str, Any]] = []
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            files = self.storage_dir.glob("*.json")
        except OSError as exc:
            logger.error("Could not read analysis history: %s", exc)
            return analyses

        for path in files:
            analysis = self._read(path)
            if analysis is not None:
                analysis["display_date"] = self._display_date(
                    str(analysis.get("created_at", ""))
                )
                analyses.append(analysis)

        return sorted(analyses, key=lambda item: str(item.get("created_at", "")), reverse=True)

    def get_analysis(self, file_id: str) -> dict[str, Any] | None:
        if not self._is_valid_file_id(file_id):
            return None
        return self._read(self._path_for(file_id))

    def delete_analysis(self, file_id: str) -> bool:
        if not self._is_valid_file_id(file_id):
            return False
        try:
            self._path_for(file_id).unlink(missing_ok=True)
            return True
        except OSError as exc:
            logger.error("Could not delete analysis history: %s", exc)
            return False

    def _path_for(self, file_id: str) -> Path:
        return self.storage_dir / f"{file_id}.json"

    def _is_valid_file_id(self, file_id: str) -> bool:
        return bool(self._valid_file_id.fullmatch(file_id))

    def _read(self, path: Path) -> dict[str, Any] | None:
        try:
            with path.open(encoding="utf-8") as handle:
                analysis = json.load(handle)
        except FileNotFoundError:
            return None
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Skipping malformed analysis history entry %s: %s", path.name, exc)
            return None

        if not isinstance(analysis, dict) or not self._is_valid_file_id(str(analysis.get("file_id", ""))):
            logger.warning("Skipping invalid analysis history entry %s", path.name)
            return None

        return analysis

    def _display_date(self, created_at: str) -> str:
        try:
            return datetime.fromisoformat(created_at.replace("Z", "+00:00")).strftime(
                "%b %d, %Y"
            )
        except ValueError:
            return created_at
