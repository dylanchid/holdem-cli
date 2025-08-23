# Holdem CLI — Product Requirements Document (Updated)

## 1. Summary

Holdem CLI is a terminal-first, offline-capable poker training tool for Texas Hold'em that provides interactive drills, single-hand simulations, equity calculations, and analytics in a lightweight CLI. It is designed to be fast, extensible, and educational rather than prescriptive.

Primary goals:

1. Deliver a usable MVP that helps beginners and intermediates improve their poker fundamentals.
2. Prioritize offline-first behavior, reproducible simulations, and local persistence.
3. Provide an extensible engine to add variants (Omaha) and advanced features later.

## 2. Guiding Principles

Offline First: core features work without network access.
Speed & Simplicity: minimal latency; intuitive commands.
Educational, Not Prescriptive: explanations and context with answers.
Extensible by Default: decoupled engine (Deck, Evaluator) and plugin hooks.

## 3. Target Users

- Beginners (basic quizzes, pot-odds)
- Intermediate players (simulations, equity)
- Tech-savvy users (CLI power users, contributors)
- Coaches (exportable hand histories, session tracking)

## 4. Must-Have / Should-Have / Nice-to-Have (Updated)

Must-Have (MVP)

Quiz engine: hand ranking, pot odds, pre-flop starting hand evaluation; difficulty levels; immediate explanations; scoring.
Single-hand simulator: full hand cycle (pre-flop → river) vs. rule-based AI; actions: fold/check/call/bet/raise.
Equity calculator: Monte Carlo engine for hand vs hand and range vs range; win/tie/loss percentages; JSON output option.
CLI: holdem main entry with subcommands and --help.
Local persistence: profiles & stats stored in SQLite.
Should-Have (Post-MVP)

Adaptive difficulty based on user stats.
ASCII/Unicode card rendering (post-MVP).
Exportable hand histories (.txt) and JSON for coach workflows.
Nice-to-Have (Future)

GTO chart lookup (pre-computed).
TUI (curses) and plugin API.
Optional cloud sync / Pro features (opt-in).

## 5. CLI Contract (spec)

Human-friendly and machine-readable outputs.
--json flag for programmatic consumption.
Deterministic seeding in tests and --seed optional flag.
Example commands:

Behavior:

holdem --help returns exit code 0 and usage.
Subcommands accept --profile NAME, --json, --seed N, and --iterations N where applicable.
holdem init creates config + DB at XDG standard path:
macOS: ~/Library/Application Support/holdem-cli/
Linux: $XDG_DATA_HOME/holdem-cli/ (default ~/.local/share/holdem-cli/)
Windows: %APPDATA%\holdem-cli\ (via WSL compatibility for MVP)

## 6. Persistence: Minimal SQLite Schema

Place under docs/schema.sql (or create on holdem init).

## 7. Performance & Accuracy Targets (Equity Engine)

Default Monte Carlo: N = 25,000 iterations.
Fallback mode: N = 2,500 iterations for low-end devices.
Target: Default run completes ≤ 2s on macOS Apple Silicon (M1/M2) CI runner and returns win/tie/loss within ±0.5% of exact enumeration for common two-card matchups.
CI: include deterministic seeded runs to validate convergence; unit tests comparing Monte Carlo to exact enumeration on small enumeratable cases.
Optimization path: pure-Python vectorization (numpy), optional numba, and a plugin C extension path.

## 8. Acceptance Criteria (measurable)

CLI: holdem --help returns usage and exit 0.
Quiz: For 1000 auto-generated questions (mixed types), 99% include an explanation string; difficulty changes distribution of question types.
Simulator: An automated integration test can run a full hand cycle and produce a hand history file.
Equity: Monte Carlo default on sample matchups achieves ≤ ±0.5% error vs enumeration and finishes ≤ 2s on macOS M1 runner; fallback finishes ≤ 2s on low-tier CI VM.

### Define CLI contract (examples)

- Add a minimal CLI spec (commands, flags, machine-readable output option). Example:

```bash
holdem --help
holdem quiz hand-ranking --count 10 --profile jordan
holdem simulate --mode headsup --ai easy --export-hand ~/hands/last.txt
holdem equity AsKs 7h7d --board 2c7s --iterations 25000 --json
```

Persistence: Creating/selecting a profile persists across process restarts and quiz/sim stats are retrievable. Store users, quiz_sessions, quiz_questions, sim_sessions, hand_history, stats. Example schema:

```sql
CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT UNIQUE, created_at TIMESTAMP);
CREATE TABLE quiz_sessions (id INTEGER PRIMARY KEY, user_id INTEGER, type TEXT, score INTEGER, total INTEGER, created_at TIMESTAMP);
CREATE TABLE quiz_questions (id INTEGER PRIMARY KEY, session_id INTEGER, prompt TEXT, correct_answer TEXT, chosen_answer TEXT, explanation TEXT);
CREATE TABLE sim_sessions (id INTEGER PRIMARY KEY, user_id INTEGER, variant TEXT, ai_level TEXT, result TEXT, created_at TIMESTAMP);
CREATE TABLE hand_history (id INTEGER PRIMARY KEY, sim_session_id INTEGER, text TEXT);
```

D. Equity engine spec (performance + fallbacks)

Default: Monte Carlo N=25,000 iterations (tunable).
Fast fallback: N=2,500 for devices that report <2s limit.
Accuracy verification: include unit tests comparing Monte Carlo to perfect enumeration on enumeratable cases.
Optimizations: vectorized Python (numpy), optional numba, or C extension plug-in path; cache repeated queries.

## 9. Roadmap & Phases (mapped to features)

Phase 0 — Sprint 0 (1 week)

CLI spec, DB schema, CI skeleton, unit tests for deck/shuffle/evaluator.
Phase 1 — MVP (Sprints 1–4, Months 1–2)

Deck & evaluator + tests, CLI scaffold, quiz engine, single-hand simulator (rule-based AI), equity Monte Carlo engine, SQLite persistence, holdem init.
Milestone: v1.0 Alpha (internal)

Phase 2 — Beta (Sprints 5–8, Months 3–4)

Adaptive difficulty, export hand history, JSON output, docs, public beta release.
Milestone: v1.0 Beta (public)

Phase 3 — Polish & Pro (Sprints 9–14, Months 5–7)

TUI (curses), GTO chart lookup, plugin API, PyPI packaging, optional cloud sync (Pro).
Milestone: v1.0 Full Release

## 10. High-Priority Backlog (Top 8)

Deck/shuffle/hand-evaluator library with deterministic RNG & unit tests.
CLI core (argparse or click) with init, quiz, simulate, equity, profile.
Quiz engine (3 types) + explanation store; session scoring.
Single-hand simulator vs rule-based AI (heads-up).
Equity Monte Carlo engine (25k default) with --iterations and --json.
SQLite persistence & holdem init creating DB schema.
Hand history export (.txt) and JSON output for programmatic workflows.
CI with test matrix (py 3.8–3.11);

## 11. QA, Tests & CI

Unit tests: deck, shuffle (statistical properties), hand evaluation (canonical cases), equity Monte Carlo vs enumeration, CLI smoke tests.
Integration tests: end-to-end simulate with --export-hand, verify DB writes.
CI: GitHub Actions matrix (3.8–3.11), macOS + ubuntu, run tests and Monte Carlo regression with small deterministic seeding.
Test determinism: expose --seed for Monte Carlo and simulator for reproducible test runs.

## 12. Security & Privacy

All user data stored locally by default (XDG paths).
No network activity unless user opts in (Pro cloud sync); explicit consent required.
Option to export DB with AES encryption (passphrase).
Backups: document location and export/import CLI.

## 13. Risks & Mitigations

Risk: Monte Carlo too slow on older hardware.
Mitigation: fallback iteration counts; vectorization; optional C extension.
Risk: CLI discoverability for non-technical users.
Mitigation: onboarding holdem init welcome message and in-CLI help; clear docs and examples.
Risk: Scope creep (GTO/solver).
Mitigation: keep GTO as pre-computed charts (Nice-to-Have) and add plugin API for solver integrations.

## 14. Metrics & OKRs (revised)

Objective: Shipping an MVP that improves users’ fundamentals.

KR1: 1,000 downloads across GitHub/PyPI in first 3 months.
KR2: Average quiz accuracy improvement of 20% across first 10 sessions per user (tracked in DB).
KR3: NPS ≥ 8 from first 50 feedbacks.
Product usage metrics (opt-in):

Sessions per active user/week.
Completion rate of drills (target 70% completion).

## 15. Next Steps (actionable)

Create a Sprint-0 ticket: implement CLI spec, DB schema, CI, and unit tests for deck/evaluator.
Implement holdem init to create config and DB using schema above.
Build minimal quiz hand-ranking and equity subcommands for internal alpha.
Add deterministic Monte Carlo test comparing to enumeration for a small case.
