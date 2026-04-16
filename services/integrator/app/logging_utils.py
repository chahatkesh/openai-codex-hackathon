from __future__ import annotations

import json
import logging
import time
from typing import Any
from uuid import UUID

logger = logging.getLogger("fusekit.integrator")


class StageTimer:
    def __init__(self, stage: str, job_id: UUID):
        self.stage = stage
        self.job_id = str(job_id)
        self.start = 0.0

    def __enter__(self):
        self.start = time.monotonic()
        logger.info(
            json.dumps(
                {
                    "event": "stage_start",
                    "job_id": self.job_id,
                    "stage": self.stage,
                }
            )
        )
        return self

    def __exit__(self, exc_type, exc, _tb):
        elapsed = int((time.monotonic() - self.start) * 1000)
        payload: dict[str, Any] = {
            "event": "stage_end",
            "job_id": self.job_id,
            "stage": self.stage,
            "elapsed_ms": elapsed,
            "status": "error" if exc else "ok",
        }
        if exc:
            payload["error"] = str(exc)[:500]
        logger.info(json.dumps(payload))
        return False
