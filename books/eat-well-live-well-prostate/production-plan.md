# Production Plan — Eat Well, Live Well, Protect Your Prostate

**Title:** EAT WELL, LIVE WELL, PROTECT YOUR PROSTATE
**Subtitle:** A Comprehensive Guide to Prostate-Friendly Nutrition, Healthy Sexual Living, Weight Management, and Practical Strategies for Reducing Urinary Symptoms
**Author / Imprint:** TRIUNE BIBLICAL UNIVERSITY GLOBAL EXTENSION USA
**Format:** Single professional PDF with front cover, front matter, 40 body chapters, back matter.
**Length requirement:** More than 300,000 words excluding front matter and back matter.
**Content policy:** Strictly secular, evidence-informed health education. No faith, devotional, scriptural, or religious content anywhere in the manuscript. The imprint name appears only as the publisher line.

## Structure

| Part | Chapters | Focus |
| --- | --- | --- |
| Front matter | — | Cover, title page, copyright, dedication, preface, how to use this book, contents (excluded from word count) |
| Part I — Foundations | 1–4 | Prostate anatomy, aging, conditions, risk/screening/diagnosis |
| Part II — Eat Well | 5–15 | Nutrition science, dietary patterns, food groups, functional foods, hydration, supplements, foods to limit, meal planning |
| Part III — Healthy Sexual Living | 16–23 | Sexual physiology, erectile function, libido, ejaculation, fertility, intimacy, pelvic floor, sex after treatment |
| Part IV — Weight Management | 24–29 | Adiposity and risk, metabolism, weight-loss strategies, exercise, sleep/stress, maintenance |
| Part V — Urinary Symptoms | 30–35 | LUTS, nocturia/urgency, incontinence, behavioral strategies, pelvic floor rehab, medical/surgical options |
| Part VI — Practical Strategies | 36–40 | Personal health plans, recipe collection, meal plans, exercise programs, healthcare partnership and tracking |
| Back matter | — | Glossary, references, index, about the imprint (excluded from word count) |

## Images

- Composed professional front cover (art generated, typography overlaid, delivered as PNG and as PDF page 1).
- Six part-opener photographs.
- Chapter figures (medical illustrations, real-photo-style food and lifestyle photography) placed at the section that needs them, each with number, caption, and explanatory text in the body.

## Word-count method

1. Conservative manuscript count: prose words in `manuscript/chapters/*.md`, excluding headings, image lines, and figure captions.
2. PDF verification: extract text from body pages only (first chapter page through last chapter page, excluding references onward; front matter excluded).
3. Both counts must exceed 300,000. Record results in `verification-report.json`.

## Pipeline

- Manuscript: one markdown file per chapter in `manuscript/chapters/`.
- Assets: images in `assets/`.
- Builder: `scripts/build_prostate_book.py` → `deliverables/eat-well-live-well-protect-your-prostate.pdf`.
- Verifier: `scripts/verify_prostate_book.py`.
