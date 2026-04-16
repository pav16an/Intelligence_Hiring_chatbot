from __future__ import annotations

from src.schemas import CandidateProfile

SYSTEM_PROMPT = """
You are TalentScout's AI Hiring Assistant.
Your purpose is strict:
1) Gather candidate profile details in a professional tone.
2) Generate high-quality technical screening questions based on declared technologies.
3) Stay context-aware and never drift to unrelated topics.
4) Keep outputs concise, safe, and recruitment-oriented.
""".strip()


def build_question_generation_prompt(profile: CandidateProfile, per_technology_count: int) -> str:
    tech_text = ", ".join(profile.tech_stack)
    role_text = ", ".join(profile.desired_positions) if profile.desired_positions else "the target role"
    return (
        "You are creating an initial screening technical questionnaire for a candidate.\n"
        f"Candidate name: {profile.full_name}\n"
        f"Years of experience: {profile.years_of_experience}\n"
        f"Desired role(s): {role_text}\n"
        f"Current location: {profile.current_location}\n"
        f"Declared technologies: {tech_text}\n"
        "Tailor question depth to experience and target roles.\n"
        f"Generate exactly {per_technology_count} questions PER technology.\n"
        "Return strict JSON only as an array of objects with keys:\n"
        '- "technology": one of the declared technologies\n'
        '- "question": a single concise technical question\n'
        "No markdown, no comments, no extra text."
    )
