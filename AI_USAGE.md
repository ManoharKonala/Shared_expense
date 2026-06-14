# AI Usage Log

This document details how AI (specifically Google's Antigravity system, Claude, and Gemini) was utilized throughout this assignment to accelerate development while ensuring best practices.

## AI Tools Used
- **Antigravity IDE Agent**: Automated multi-file refactoring, implemented backend SQLAlchemy listeners, ran and verified `pytest` suites, and iteratively built the frontend React components.

## Overall Workflow
My workflow followed a "Plan → Scaffold → Implement → Test → Refine" pattern.
1. I provided the prompt to the AI, which synthesized the constraints and drafted an `implementation_plan.md`.
2. Upon my approval, the AI autonomously generated the SQLAlchemy models and wrote an automated seed script.
3. For complex logic (like the graph-based min-transactions engine), I let the AI write the first draft, ran tests, and requested refinements if calculations failed.
4. Finally, the AI iteratively scaffolded the Vite + Tailwind frontend, connecting it to the robust backend API.

## Example Prompts
1. *"The `app/models/` directory needs SQLAlchemy models mapped exactly to the prompt schema. Make sure `amount_in_inr` is defined as a Decimal to avoid floating-point errors."*
2. *"Implement `calculate_balances` and `suggest_settlements` using a greedy matching algorithm to minimize transactions."*
3. *"Write a comprehensive `pytest` suite for the `anomaly_detector.py`. It must test the fuzzy matching logic for names and the 'Sam/Meera' membership window logic."*
4. *"Create a React modal for uploading CSVs. It needs to fetch the `session_id` and map through the `anomalies` array to render approval buttons for each anomaly."*
5. *"The test `test_sam_meera_scenario` failed because of a SQLAlchemy initialization issue (`__new__`). Update the test helper to use the standard `GroupMember()` constructor."*

## 3 Concrete Cases Where AI Was Wrong
1. **The ContextVars Issue**: Initially, the AI tried to pass the `current_user` object all the way down into the SQLAlchemy `after_insert` event listeners. This polluted the function signatures and broke the layered architecture. *Correction:* I guided the AI to use `contextvars` inside the FastAPI dependency injection to elegantly decouple the HTTP request state from the database models.
2. **The "Penny" Divisibility Issue**: The AI's original split calculator threw errors when 100 divided by 3 resulted in 33.3333... *Correction:* I had the AI rewrite the logic to compute a base share and distribute the remainder penny-by-penny so that `sum(shares) == total` exactly.
3. **External Dependencies**: The AI added the `Levenshtein` package to `requirements.txt` to do fuzzy string matching. However, compiling this C-extension failed on Windows with Python 3.13. *Correction:* I had the AI remove the external dependency and write a pure Python implementation of the Levenshtein distance algorithm manually.
