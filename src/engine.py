from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Callable

from src.config import Settings
from src.llm import QuestionGenerator
from src.schemas import CandidateProfile
from src.storage import LocalStorage
from src.validators import (
    is_valid_email,
    is_valid_phone,
    normalize_tech_stack,
    parse_csv_list,
    parse_years_of_experience,
    sanitize_text,
)


@dataclass(frozen=True)
class CollectionStep:
    field_name: str
    prompt: str
    parser: Callable[[str], object | None]
    error_message: str


def _parse_name(value: str) -> str | None:
    cleaned = sanitize_text(value)
    return cleaned if len(cleaned.split()) >= 2 else None


def _parse_email(value: str) -> str | None:
    cleaned = sanitize_text(value)
    return cleaned if is_valid_email(cleaned) else None


def _parse_phone(value: str) -> str | None:
    cleaned = sanitize_text(value)
    return cleaned if is_valid_phone(cleaned) else None


def _parse_positions(value: str) -> list[str] | None:
    items = parse_csv_list(value)
    return items if items else None


def _parse_location(value: str) -> str | None:
    cleaned = sanitize_text(value)
    return cleaned if cleaned else None


def _parse_tech_stack(value: str) -> list[str] | None:
    stack = normalize_tech_stack(value)
    return stack if stack else None


STEPS: list[CollectionStep] = [
    CollectionStep(
        field_name="full_name",
        prompt="Please share your full name (first and last name).",
        parser=_parse_name,
        error_message="Please enter a valid full name (first and last name).",
    ),
    CollectionStep(
        field_name="email",
        prompt="What is your email address?",
        parser=_parse_email,
        error_message="That email format looks invalid. Please enter a valid email address.",
    ),
    CollectionStep(
        field_name="phone_number",
        prompt="Please provide your phone number (with country code if available).",
        parser=_parse_phone,
        error_message="Please enter a valid phone number.",
    ),
    CollectionStep(
        field_name="years_of_experience",
        prompt="How many years of professional experience do you have?",
        parser=parse_years_of_experience,
        error_message="Please enter years of experience as a number, like 2 or 4.5.",
    ),
    CollectionStep(
        field_name="desired_positions",
        prompt="What position(s) are you targeting? You can use commas for multiple roles.",
        parser=_parse_positions,
        error_message="Please provide at least one desired role (comma-separated for multiple).",
    ),
    CollectionStep(
        field_name="current_location",
        prompt="What is your current location?",
        parser=_parse_location,
        error_message="Please provide your current location.",
    ),
    CollectionStep(
        field_name="tech_stack",
        prompt=(
            "List your tech stack as comma-separated items "
            "(languages, frameworks, databases, tools)."
        ),
        parser=_parse_tech_stack,
        error_message="Please provide at least one technology in your tech stack.",
    ),
]


class ConversationEngine:
    def __init__(
        self,
        settings: Settings,
        question_generator: QuestionGenerator | None = None,
        storage_backend: LocalStorage | None = None,
    ) -> None:
        self.settings = settings
        self.question_generator = question_generator or QuestionGenerator(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            min_questions=settings.min_questions,
            max_questions=settings.max_questions,
        )
        self.storage = storage_backend or LocalStorage(settings.data_dir)
        self.reset()

    def reset(self) -> None:
        self.phase = "collect_profile"
        self.step_index = 0
        self.profile = CandidateProfile()
        self.technical_questions: list[str] = []
        self.technical_responses: list[dict[str, str]] = []

    def start_messages(self) -> list[str]:
        return [
            (
                "Hello! I am TalentScout's Hiring Assistant. I will collect your profile details "
                "and then ask technical questions based on your tech stack."
            ),
            "You can type exit, quit, bye, or stop anytime to end this conversation.",
            STEPS[0].prompt,
        ]

    def _is_exit(self, message: str) -> bool:
        cleaned = sanitize_text(message).lower()
        if not cleaned:
            return False
        if cleaned in self.settings.exit_keywords:
            return True
        pattern = r"\b(" + "|".join(re.escape(keyword) for keyword in self.settings.exit_keywords) + r")\b"
        return bool(re.search(pattern, cleaned))

    def _is_unclear_response(self, message: str) -> bool:
        lowered = message.lower().strip()
        unclear_markers = {
            "idk",
            "i dont know",
            "i don't know",
            "dont know",
            "don't know",
            "no idea",
            "n/a",
            "na",
            "?",
        }
        if lowered in unclear_markers:
            return True
        if len(lowered.split()) < 3:
            return True
        return False

    def _set_profile_value(self, field_name: str, value: object) -> None:
        setattr(self.profile, field_name, value)

    def handle_user_message(self, user_message: str) -> dict[str, object]:
        cleaned = sanitize_text(user_message)
        if self._is_exit(cleaned):
            self.phase = "ended"
            return {
                "ended": True,
                "messages": [
                    "Conversation ended successfully. Thank you for your time.",
                    "Our hiring team will review your details and contact you about next steps.",
                ],
            }

        if self.phase == "collect_profile":
            step = STEPS[self.step_index]
            parsed = step.parser(cleaned)
            if parsed is None:
                return {
                    "ended": False,
                    "messages": [
                        f"I could not validate that input. {step.error_message}",
                        step.prompt,
                    ],
                }
            self._set_profile_value(step.field_name, parsed)
            self.step_index += 1
            if self.step_index < len(STEPS):
                return {"ended": False, "messages": [STEPS[self.step_index].prompt]}

            self.phase = "technical_round"
            self.technical_questions = self.question_generator.generate_technical_questions(
                self.profile
            )
            if not self.technical_questions:
                self.phase = "ended"
                return {
                    "ended": True,
                    "messages": [
                        "I could not generate technical questions for this session.",
                        "Thank you for your time. Our team will follow up for the next steps.",
                    ],
                }
            first_question = self.technical_questions[0]
            return {
                "ended": False,
                "messages": [
                    (
                        "Thanks. Profile capture is complete. Starting technical screening now "
                        f"with {len(self.technical_questions)} questions."
                    ),
                    f"Question 1/{len(self.technical_questions)}: {first_question}",
                ],
            }

        if self.phase == "technical_round":
            if not cleaned:
                current_index = len(self.technical_responses)
                current_question = self.technical_questions[current_index]
                return {
                    "ended": False,
                    "messages": [
                        "Please share a brief response so I can continue the assessment.",
                        f"Question {current_index + 1}/{len(self.technical_questions)}: {current_question}",
                    ],
                }

            if self._is_unclear_response(cleaned):
                current_index = len(self.technical_responses)
                current_question = self.technical_questions[current_index]
                return {
                    "ended": False,
                    "messages": [
                        "Thanks for sharing. I could not clearly understand that response. Please rephrase in 1-3 sentences.",
                        f"Question {current_index + 1}/{len(self.technical_questions)}: {current_question}",
                    ],
                }

            current_index = len(self.technical_responses)
            current_question = self.technical_questions[current_index]
            self.technical_responses.append(
                {"question": current_question, "answer": cleaned}
            )

            if len(self.technical_responses) < len(self.technical_questions):
                next_index = len(self.technical_responses)
                next_question = self.technical_questions[next_index]
                return {
                    "ended": False,
                    "messages": [
                        f"Question {next_index + 1}/{len(self.technical_questions)}: {next_question}"
                    ],
                }

            candidate_id = self.storage.save_candidate_record(
                profile=self.profile,
                technical_responses=self.technical_responses,
            )
            self.phase = "ended"
            return {
                "ended": True,
                "messages": [
                    "Technical screening is complete. Thank you for your responses.",
                    (
                        f"Your candidate reference ID is {candidate_id}. "
                        "Our team will connect with you for the next steps."
                    ),
                ],
            }

        return {
            "ended": True,
            "messages": [
                "This conversation is already closed. Please restart the chat for a new submission."
            ],
        }
