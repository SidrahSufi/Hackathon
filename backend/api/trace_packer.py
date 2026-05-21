"""
Trace packer — bundles a run's state files into a downloadable zip.
"""
from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path


def _workspace_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def pack_trace(run_id: str) -> bytes:
    """
    Build an in-memory zip containing:
    - all *.json files from .state/<run_id>/
    - metadata.json with run_id, generated_at, file_list
    - README.txt explaining the contents

    Raises FileNotFoundError if the run doesn't exist on disk.
    """
    state_dir = _workspace_root() / ".state" / run_id
    if not state_dir.exists() or not state_dir.is_dir():
        raise FileNotFoundError(f"Run {run_id} not found in .state/")

    buf = io.BytesIO()
    file_list: list[str] = []

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for fp in sorted(state_dir.iterdir()):
            if fp.is_file() and fp.suffix == ".json":
                zf.write(fp, arcname=f"{run_id}/{fp.name}")
                file_list.append(fp.name)

        metadata = {
            "run_id": run_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "file_list": file_list,
        }
        zf.writestr(
            f"{run_id}/metadata.json", json.dumps(metadata, indent=2)
        )

        readme = (
            f"PulseAI trace bundle\n"
            f"====================\n\n"
            f"Run ID: {run_id}\n"
            f"Generated: {metadata['generated_at']}\n\n"
            f"Files:\n"
            + "\n".join(f"  - {f}" for f in file_list)
            + "\n\n"
            "Each JSON file is the output of one pipeline stage.\n"
            "See the project README for the schemas.\n"
        )
        zf.writestr(f"{run_id}/README.txt", readme)

    buf.seek(0)
    return buf.getvalue()
