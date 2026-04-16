from src.config import Settings
from src.engine import ConversationEngine


class FakeGenerator:
    def generate_technical_questions(self, profile) -> list[str]:
        assert profile.tech_stack == ["Python", "Django"]
        assert profile.years_of_experience == 5.0
        assert profile.desired_positions == ["ML Engineer", "Backend Engineer"]
        return [
            "[Python] Explain Python generators and a real use case.",
            "[Django] How does Django ORM help in secure query building?",
            "[Python] How would you optimize a slow API endpoint?",
        ]


class FakeStorage:
    def __init__(self) -> None:
        self.saved = False
        self.last_profile = None
        self.last_responses = None

    def save_candidate_record(self, profile, technical_responses) -> str:
        self.saved = True
        self.last_profile = profile
        self.last_responses = technical_responses
        return "abc123xyz789"


def _settings() -> Settings:
    return Settings(
        data_dir=None,  # type: ignore[arg-type]
        openai_api_key=None,
        openai_model="gpt-4o-mini",
        min_questions=3,
        max_questions=5,
        exit_keywords=("exit", "quit", "bye"),
    )


def test_conversation_happy_path() -> None:
    fake_storage = FakeStorage()
    engine = ConversationEngine(
        settings=_settings(),
        question_generator=FakeGenerator(),  # type: ignore[arg-type]
        storage_backend=fake_storage,  # type: ignore[arg-type]
    )

    messages = engine.start_messages()
    assert "TalentScout" in messages[0]

    scripted_inputs = [
        "Ada Lovelace",
        "ada@talentscout.ai",
        "+44 20 7946 0958",
        "5",
        "ML Engineer, Backend Engineer",
        "London, UK",
        "Python, Django",
        "I use generators to stream large files efficiently.",
        "The ORM parameterizes queries by default.",
        "I profile bottlenecks and cache high-cost operations.",
    ]

    ended = False
    for item in scripted_inputs:
        result = engine.handle_user_message(item)
        ended = bool(result["ended"])

    assert ended is True
    assert fake_storage.saved is True
    assert fake_storage.last_profile.full_name == "Ada Lovelace"
    assert len(fake_storage.last_responses) == 3


def test_exit_keyword() -> None:
    engine = ConversationEngine(
        settings=_settings(),
        question_generator=FakeGenerator(),  # type: ignore[arg-type]
        storage_backend=FakeStorage(),  # type: ignore[arg-type]
    )
    result = engine.handle_user_message("exit")
    assert bool(result["ended"]) is True
