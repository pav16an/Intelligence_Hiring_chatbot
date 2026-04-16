from __future__ import annotations

import json
import re
from typing import Any

from src.prompts import SYSTEM_PROMPT, build_question_generation_prompt
from src.schemas import CandidateProfile

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore[assignment]


def _canonical(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _ensure_question_format(text: str) -> str:
    cleaned = text.strip().lstrip("- ").strip()
    return cleaned if cleaned.endswith("?") else f"{cleaned}?"


def _strip_code_fence(raw_text: str) -> str:
    text = raw_text.strip()
    if text.startswith("```") and text.endswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3:
            return "\n".join(lines[1:-1]).strip()
    return text


def _question_count_from_experience(years: float, minimum: int, maximum: int) -> int:
    if years <= 2:
        return minimum
    if years <= 5:
        return min(maximum, minimum + 1)
    return maximum


def _experience_band(years: float) -> str:
    if years <= 2:
        return "junior"
    if years <= 5:
        return "mid"
    return "senior"


def _match_declared_technology(label: str, declared_tech_stack: list[str]) -> str | None:
    label_key = _canonical(label)
    if not label_key:
        return None
    for tech in declared_tech_stack:
        if _canonical(tech) == label_key:
            return tech
    for tech in declared_tech_stack:
        tech_key = _canonical(tech)
        if label_key in tech_key or tech_key in label_key:
            return tech
    return None


def _parse_llm_questions(
    raw_text: str, declared_tech_stack: list[str], per_technology_count: int
) -> dict[str, list[str]]:
    content = _strip_code_fence(raw_text)
    payload = json.loads(content)
    if isinstance(payload, dict):
        payload = payload.get("questions", [])
    if not isinstance(payload, list):
        return {}

    grouped: dict[str, list[str]] = {tech: [] for tech in declared_tech_stack}
    for item in payload:
        if not isinstance(item, dict):
            continue
        technology = str(item.get("technology", "")).strip()
        question = str(item.get("question", "")).strip()
        matched = _match_declared_technology(technology, declared_tech_stack)
        if matched and question:
            grouped[matched].append(_ensure_question_format(question))

    for tech in declared_tech_stack:
        grouped[tech] = list(dict.fromkeys(grouped[tech]))[:per_technology_count]
    return grouped


def _profile_based_fallback(profile: CandidateProfile, per_technology_count: int) -> list[str]:
    role_text = ", ".join(profile.desired_positions) if profile.desired_positions else "the target role"
    band = _experience_band(profile.years_of_experience)

    templates_by_band: dict[str, list[str]] = {
        "junior": [
            "Explain the core concepts of {tech} and where you used them.",
            "Walk through a small project where you applied {tech} for {role}.",
            "How do you debug common errors when working with {tech}?",
            "What best practices do you follow while writing {tech}-based code?",
            "How do you test features built with {tech} before release?",
        ],
        "mid": [
            "Describe an architecture decision you made using {tech} for {role}.",
            "How do you optimize performance for a production feature built with {tech}?",
            "What trade-offs do you evaluate when designing with {tech}?",
            "How do you ensure reliability and observability for {tech}-based services?",
            "How do you mentor teammates on maintainable patterns in {tech}?",
        ],
        "senior": [
            "How would you design a scalable, fault-tolerant system using {tech} for {role}?",
            "What are advanced failure scenarios in {tech}, and how would you mitigate them?",
            "How do you balance delivery speed with engineering quality in {tech}-heavy systems?",
            "How would you define standards and governance for teams using {tech}?",
            "How do you evaluate long-term technical debt risk in {tech} architecture decisions?",
        ],
    }

    templates = templates_by_band[band]
    questions: list[str] = []
    for tech in profile.tech_stack:
        for index in range(per_technology_count):
            template = templates[index % len(templates)]
            question = _ensure_question_format(template.format(tech=tech, role=role_text))
            questions.append(f"[{tech}] {question}")
    return questions


class QuestionGenerator:
    def __init__(self, api_key: str | None, model: str, min_questions: int, max_questions: int) -> None:
        self.api_key = api_key
        self.model = model
        self.min_questions = min_questions
        self.max_questions = max_questions

    def _generate_with_openai(
        self, profile: CandidateProfile, per_technology_count: int
    ) -> dict[str, list[str]]:
        if not self.api_key or OpenAI is None:
            return {}

        client = OpenAI(api_key=self.api_key)
        prompt = build_question_generation_prompt(profile, per_technology_count)
        response: Any = client.responses.create(
            model=self.model,
            temperature=0.2,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        text_output = getattr(response, "output_text", "") or ""
        return _parse_llm_questions(text_output, profile.tech_stack, per_technology_count)

    def generate_technical_questions(self, profile: CandidateProfile) -> list[str]:
        if not profile.tech_stack:
            return []

        per_technology_count = _question_count_from_experience(
            profile.years_of_experience,
            minimum=self.min_questions,
            maximum=self.max_questions,
        )

        grouped: dict[str, list[str]] = {tech: [] for tech in profile.tech_stack}
        try:
            llm_grouped = self._generate_with_openai(profile, per_technology_count)
            for tech in profile.tech_stack:
                grouped[tech].extend(llm_grouped.get(tech, []))
        except Exception:
            pass

        final_questions: list[str] = []
        fallback_questions = _profile_based_fallback(profile, per_technology_count)
        fallback_by_tech: dict[str, list[str]] = {tech: [] for tech in profile.tech_stack}
        for line in fallback_questions:
            for tech in profile.tech_stack:
                if line.startswith(f"[{tech}] "):
                    fallback_by_tech[tech].append(line)
                    break

        for tech in profile.tech_stack:
            tech_questions = [f"[{tech}] {q}" for q in list(dict.fromkeys(grouped[tech]))]
            if len(tech_questions) < per_technology_count:
                for fallback_line in fallback_by_tech[tech]:
                    if fallback_line not in tech_questions:
                        tech_questions.append(fallback_line)
                    if len(tech_questions) >= per_technology_count:
                        break
            final_questions.extend(tech_questions[:per_technology_count])
        return final_questions
