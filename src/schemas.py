from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class CandidateProfile:
    full_name: str = ""
    email: str = ""
    phone_number: str = ""
    years_of_experience: float = 0.0
    desired_positions: list[str] = field(default_factory=list)
    current_location: str = ""
    tech_stack: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)
