# Research: chatbot findings, Google tests and feature ideas

Started 2026-11-25 by the research session. **This folder holds notes, not decisions.** Decisions go in `PLAN.md`, `TODO.md` or the spec once the owner makes them.

## How it works

1. **The owner pastes something:** a ChatGPT, Gemini or Perplexity answer, or results and screenshots from testing Google Flights Explore, Flight Deals, Google Travel or AI Mode.
2. **The research session writes an inbox note:** `inbox/<YYYY-MM-DD>-<topic>.md`, using the template below.
3. **Ideas from the note go into [feature-ideas.md](feature-ideas.md).** Duplicates are merged, and each idea links back to its evidence.
4. **Google test results go into [google-comparison.md](google-comparison.md).** It shows where Google wins, where we win and what would close the gap.
5. **When the owner asks**, the session writes `what-to-build-next-<date>.md` for the development session. It's short, ranked, and each item says why and how big it is.

## Files

| File | What it is |
|---|---|
| [google-comparison.md](google-comparison.md) | Google vs Far Enough on the core question: "$X total for N people from Toronto, where can we go, all costs in?" |
| [feature-ideas.md](feature-ideas.md) | Living backlog: problem, evidence, effort, Phase 1 fit, recommendation |
| `inbox/` | One note per paste or test session |
| `screenshots/` | The owner's screenshots, named `<date>-<tool>-<what>.png` |

## Rules for evidence

- **Chatbot output is an unverified claim.** It is not a source. Every fact in an inbox note is labelled:
  - ✅ **confirmed**: checked against a primary source (official site, provider docs, government page), linked, with the check date.
  - ⚠️ **unverified**: not checked, or only third-party sources found.
  - ❌ **wrong**: a primary source contradicts it.
- **Check what would change a decision:** prices, provider terms, legal and regulatory claims (TICO, Competition Act, CASL), entry rules and what competitors offer. Leave trivia unchecked and say so.
- **Google tests are dated observations.** Google changes features by country and runs experiments per account. Record the date, device (desktop or mobile), whether you were signed in, and the country you searched from (Canada matters: some features are U.S. only).
- **Prices quoted by a chatbot are never used in the product.** The spec (§7) bans LLM-produced prices.
- No personal data in notes: no account emails or booking references.

## Inbox note template

```markdown
# <Topic> (<tool>, <date>)

**Asked:** the exact prompt or the steps taken.
**Tool and setup:** e.g. ChatGPT (model if shown), or Google Flights Explore, desktop, signed in, from Toronto.

## What it answered
A short summary in our own words. Quote at most one short line.

## Useful
- ...

## Wrong or unverified
| Claim | Status | Check |
|---|---|---|
| ... | ✅ / ⚠️ / ❌ | link, date |

## What it means for us
- Feature ideas added: ... (feature-ideas.md #n)
- Google comparison updated: ... (section)
```

## Who does what

The research session writes only in `docs/research/`. It does not change code (`backend/`, `site/`, `.github/`) and does not commit. The development session reviews and commits these files.
