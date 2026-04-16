# TalentScout AI Hiring Assistant

This project implements an end-to-end AI/ML intern assignment solution for a fictional recruitment agency, **TalentScout**.

The app is a Streamlit chatbot that:
- greets candidates and explains the process,
- collects required profile information,
- uses the LLM to generate technical questions from candidate profile + experience + tech stack,
- keeps conversation context across steps,
- provides fallback messages for invalid/unexpected inputs,
- allows graceful conversation exit via keywords,
- stores anonymized/masked candidate records locally.

## Tech Stack

- Python 3.10+
- Streamlit (UI)
- OpenAI API (optional; with local fallback when API key is missing)
- Pytest (tests)

## Project Structure

```text
.
|-- app.py
|-- src
|   |-- config.py
|   |-- engine.py
|   |-- llm.py
|   |-- prompts.py
|   |-- schemas.py
|   |-- storage.py
|   `-- validators.py
|-- tests
|   |-- test_engine.py
|   `-- test_validators.py
|-- data
|-- requirements.txt
`-- .env.example
```

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy environment template:

```bash
cp .env.example .env
```

4. Add `OPENAI_API_KEY` in `.env` if you want live LLM-generated questions.

## Run

```bash
streamlit run app.py
```

Open the local URL shown by Streamlit (usually `http://localhost:8501`).

## Usage Flow

1. Candidate sees greeting and instructions.
2. Bot collects:
   - full name
   - email
   - phone number
   - years of experience
   - desired positions
   - current location
   - tech stack
3. Bot starts technical screening and asks 3-5 questions per technology (experience-adjusted depth).
4. Candidate answers each question.
5. Conversation ends with a generated candidate reference ID.
6. Masked data is persisted to `data/candidates.jsonl`.

## Prompt Design

- System prompt constrains behavior to hiring-assistant scope.
- User prompt includes candidate years of experience, desired role(s), location, and declared technologies.
- The LLM generates questions with difficulty aligned to candidate seniority.
- Temperature is low (`0.2`) to reduce randomness and keep outputs consistent.
- If OpenAI is unavailable, a profile-aware fallback builds dynamic questions from candidate context.

## Data Privacy and Handling

- Data is simulated/anonymized for assignment use.
- Stored email and phone are masked before writing to disk.
- Candidate ID is hashed and non-reversible.
- Local file storage only (`data/candidates.jsonl`).

## Fallback and Robustness

- Input validators detect malformed email/phone/experience values.
- Bot re-prompts with meaningful corrective guidance.
- Exit keywords supported anytime: `exit`, `quit`, `bye`, `goodbye`, `stop`, `end`.
- If user input is empty in technical round, bot requests a valid response and repeats the question.

## Testing

Run:

```bash
pytest -q
```

Covered:
- validators (email, phone, years parsing, tech stack normalization),
- happy-path conversation,
- exit keyword behavior.

## Challenges and Solutions

- **Challenge:** Question quality should adapt to candidate seniority and role target.
  **Solution:** Prompts now include full candidate context so the LLM adjusts difficulty and focus automatically.
- **Challenge:** Sensitive candidate information in local demo apps.
  **Solution:** Persist only masked contact information and hashed candidate IDs.
- **Challenge:** Maintaining coherent conversation flow.
  **Solution:** Implemented explicit state-machine style conversation engine.

## Assignment Deliverables Coverage

- Streamlit chatbot UI: implemented.
- Required candidate info capture: implemented.
- Profile + experience + tech-stack based technical question generation: implemented (LLM-first).
- Context handling: implemented with staged conversation state.
- Fallback behavior: implemented for invalid/unexpected input.
- End-conversation handling: implemented with graceful close and reference ID.
- README documentation: included.
