from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from src.schemas import CandidateProfile


def mask_email(email: str) -> str:
    if "@" not in email:
        return email
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        local_masked = "*" * len(local)
    else:
        local_masked = f"{local[0]}{'*' * (len(local) - 2)}{local[-1]}"
    return f"{local_masked}@{domain}"


def mask_phone(phone: str) -> str:
    digits = [char for char in phone if char.isdigit()]
    if len(digits) < 4:
        return "*" * len(phone)
    visible = "".join(digits[-4:])
    return f"***-***-{visible}"


class LocalStorage:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.output_file = self.data_dir / "candidates.jsonl"

    def _build_candidate_id(self, profile: CandidateProfile) -> str:
        seed = f"{profile.email}|{profile.phone_number}|{datetime.now(timezone.utc).isoformat()}"
        digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
        return digest[:12]

    def save_candidate_record(
        self, profile: CandidateProfile, technical_responses: list[dict[str, str]]
    ) -> str:
        candidate_id = self._build_candidate_id(profile)
        payload = {
            "candidate_id": candidate_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "profile": {
                "full_name": profile.full_name,
                "email_masked": mask_email(profile.email),
                "phone_masked": mask_phone(profile.phone_number),
                "years_of_experience": profile.years_of_experience,
                "desired_positions": profile.desired_positions,
                "current_location": profile.current_location,
                "tech_stack": profile.tech_stack,
            },
            "technical_round": technical_responses,
            "note": "Data is simulated and masked for privacy-first local storage.",
        }
        with self.output_file.open("a", encoding="utf-8") as file:
            file.write(json.dumps(payload) + "\n")
        return candidate_id
