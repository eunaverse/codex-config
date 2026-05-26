---
name: behavioral-star-coach
description: Use when the user needs behavioral STAR interview answers, story banks, script rewrites, mock follow-up questions, role-specific communication coaching, or answer-quality checks for US tech interviews.
---

# Behavioral STAR Coach

## Overview

Build interview-ready STAR stories that are concise, credible, and adaptable to different behavioral prompts.

## EUNWHA-Specific Backend Scripts

When the prompt relies on EUNWHA's Samsung backend experience, IAM modernization, ClustrixDB migration evidence, `Tell me about yourself`, `Walk me through your resume`, `Why this role?`, backend ownership wording, or overclaiming risk, also use `$samsung-backend-interview-scripts`.

Keep this skill responsible for STAR structure, answer quality, length, and follow-up pressure testing. Use `$samsung-backend-interview-scripts` for evidence selection and Samsung-specific scope boundaries.

## User Script Library

When EUNWHA asks for an English interview script, use this Notion page as the canonical script library:

- Notion index: `https://www.notion.so/30b8a12184338100ba37d14940e9bb29`
- Page title: `영어면접_세션_모음`
- Existing reference pages include `Tell me about yourself`, `Walk me through your resume`, and `Why this role?`.

Default workflow for interview answer/script requests:

1. Fetch the Notion index page first.
2. Read existing child pages that are relevant to the requested question or prompt family before drafting. Do not rely on memory alone for the Notion tone.
3. Match the tone, level of specificity, structure, and defensible Samsung backend ownership boundaries from the existing scripts.
4. Run the Strength/Weakness Framing Preflight below before drafting.
5. Draft the script outside Notion first. Do not create or update the Notion page until the Direct Notion Write Review Loop below is clean.
6. Create or update a child page under the Notion index page for the final script by default. This is the default even if the user only says "write the answer", "prepare the script", "정리해줘", or similar wording.
7. Skip the Notion write only when EUNWHA explicitly asks for chat-only output, brainstorming only, a quick explanation, or says not to update Notion.
8. Include the final script, concise Korean coaching notes if useful, likely follow-up questions, and a short review-loop summary when substantial revisions were made.

## Direct Notion Write Review Loop

When EUNWHA asks to write, prepare, rewrite, finalize, organize, save, sync, or update an English interview answer/script, the default destination is the canonical Notion script library. The answer must pass a fresh 3-reviewer loop before any Notion write. Chat-only drafting, brainstorming, quick explanations, or mock-drill coaching skip this gate only when EUNWHA explicitly asks not to update Notion or the request does not produce final answer wording.

1. Build a local draft first
- Fetch the Notion index and relevant child pages.
- Draft the answer in the current session using the Pre-Draft Guardrails, Backend Answer Quality Gate, and any relevant Samsung-specific evidence rules.
- For existing-page updates, fetch the page and prepare the replacement content locally before calling a Notion update tool.

2. Spawn three independent reviewers in parallel
- Start exactly 3 separate subagents for the review cycle.
- Each reviewer must be fresh for that cycle; never reuse a reviewer from a previous cycle.
- Give each reviewer only the minimum shared context: prompt, target role or JD if available, current draft, verified evidence, ownership boundaries, and the quality gate.
- Do not pass one reviewer's findings, your planned fixes, or hidden conclusions to the other reviewers.
- Ask each reviewer to return either `no actionable findings` or a concise list of actionable weaknesses.
- If subagents are unavailable, stop before the Notion write and tell EUNWHA the Notion write gate cannot be completed.

3. Consolidate and revise
- Wait for all 3 reviewer outputs before revising.
- Treat overclaiming risk, weak evidence, unclear ownership, generic wording, missing follow-up resilience, unsupported metrics or company facts, and unnatural spoken phrasing as actionable.
- Treat any wording that implies ownership of database infrastructure, storage-layer internals, broad data infrastructure, company-specific facts, metrics, or product claims as actionable unless directly supported by EUNWHA's evidence or verified source material.
- Ignore purely stylistic disagreements if they weaken evidence accuracy or spoken clarity.
- If any reviewer gives an actionable finding, revise the draft and rerun the Backend Answer Quality Gate.

4. Repeat with three new reviewers after every revision
- After any revision, start a new review cycle with 3 brand-new independent reviewers.
- Do not reuse previous reviewer agents, even if their prior feedback was helpful.
- Continue until the newest 3-reviewer cycle reports no actionable findings.

5. Write to Notion only after a clean cycle
- Only create or update the Notion page after the latest 3 fresh reviewers report no actionable findings.
- If reviewers conflict on a factual claim, require unverified company-specific evidence, or expose a missing ownership boundary, do not create or update the Notion page at all. Mark the draft provisional in chat or local working context and ask for the missing evidence or user decision.
- If EUNWHA asks to bypass the review gate, do not write to the canonical Notion script library. Provide the draft in chat or local working context only, and explain that canonical Notion writes require a clean 3-reviewer pass.
- Keep the Notion page focused on the final usable script, follow-up answers, coaching notes, and concise quality status. Do not paste reviewer names, long reviewer transcripts, internal critique history, or rejected findings unless EUNWHA explicitly asks.
- In the final chat response, report the review-loop result. If the gate is blocked, pending, or revision-required, report that status only in chat or local working context and do not write to Notion. When writing to Notion after a clean pass, include a concise `Quality Review Log` section:
  - Review pass: `<number>`
  - Reviewers: `3 fresh subagents; no reviewer reused`
  - Result: `clean`
  - Findings addressed: `<short bullets, or "none">`
  - Notion write status: `completed after clean pass`

## Pre-Draft Guardrails

Before drafting, block vague prestige or abstraction-based motivation. Do not use these phrases as standalone reasons:

- "strong system design"
- "infrastructure depth"
- "innovative company"
- "challenging problems"
- "large-scale impact"
- "intersection of product and infrastructure"
- "global impact"

These phrases may only stay if tied to all of:

1. a concrete company, product, or infrastructure area,
2. a backend responsibility,
3. a user-facing or operational outcome,
4. EUNWHA's real Samsung backend experience.

Use this rewrite pattern:

> I am interested in [backend/system work] because it improves [product, user, reliability, or operational outcome] as [company/product] scales.

Run a "So what?" test on each motivation sentence:

- Weak: "I am interested in strong system design."
- Stronger: "I am interested in backend systems where design decisions directly affect product reliability, user experience, and scalability."

If the target company, product area, or concrete challenge is missing, label the draft provisional. Do not call it final.

## Strength/Weakness Framing Preflight

Run this before drafting any `strength`, `weakness`, `greatest strength`, `improvement`, or mixed strength/weakness answer.

1. Choose one umbrella strength
- Do not stack unrelated strengths with "also" unless they are clearly evidence of the same umbrella trait.
- Preferred umbrella forms:
  - `I bring structure to ambiguous or high-risk work by breaking it down, identifying risks, and turning it into a clear process the team can execute.`
  - `I turn unclear or repetitive engineering work into reliable systems and processes.`
- Use the first form when the evidence is mainly production execution and risk reduction.
- Use the second form only when the answer must combine production risk work with workflow automation.

2. Classify each example before writing
- Production example: should prove risk breakdown, execution path, correctness, reliability, or safe rollout.
- Workflow automation example: should prove reducing repeated manual coordination or making team execution more reliable.
- New tools / agent workflows: use only as an optional add-on unless there is concrete impact. Frame as practical, low-risk adoption, not as the main strength.

3. Check concept fit
- If two examples do not follow from the same umbrella strength, either change the umbrella strength or move one example to `Optional add-on`.
- Do not claim `same mindset` when the mechanism is different. Prefer:
  - `I also apply that strength to team workflows...`
  - `That also shows up in how I improve team workflows...`
- Avoid turning the opening into "my strength is A, and also B." The first sentence should name one strength only.

4. Keep spoken length realistic
- `30-second version`: about 55-75 words. Use one strength sentence, one compact evidence phrase, and one weakness/change sentence.
- `60-second answer`: about 115-145 words. Use one umbrella strength, at most two compact evidence examples, and a compressed weakness/change arc.
- If reviewers repeatedly flag length, cut examples before adding explanations. Put secondary material under `Optional add-on`.

5. Use natural spoken wording
- Prefer `I don't just focus on...` over `I do not only focus on...`.
- Prefer `keeping API specs updated alongside backend changes` over dense build-system wording unless the interviewer asks for technical detail.
- Avoid vague pronouns in automation sentences. Name the object: `manual coordination`, `important updates`, `API specs`, or `PR and review activity`.
- Avoid jargon such as `over-indexed`; say `spent too much time planning before getting feedback`.

## Backend Answer Quality Gate

Do not treat an answer as a strong or final model answer until it passes these checks:

1. Company or role fit
- The answer connects to the target company, role, product, or infrastructure challenge.
- Avoid generic claims like "innovative company" unless tied to a concrete system or product.

2. Backend engineering signal
- Include backend judgment such as reliability, scalability, correctness, API design, data models, data access patterns, latency, consistency, backward compatibility, migration safety, or safe rollout.
- For company-specific claims, verify the product or infrastructure fact from the user's JD, company page, or current public source. If not verified, mark it as a placeholder.

3. Evidence from EUNWHA's real experience
- Ground claims in Samsung production backend experience, especially identity and access management, production reliability, large-scale data, migration, or modernization work.
- Keep the scope defensible. Prefer "backend application-side ownership", "backend APIs", "data models", "data access patterns", and "safe rollout logic".
- Avoid overclaiming ownership of database infrastructure, storage-layer internals, or broad data infrastructure unless the user provides direct evidence.

4. Ownership boundary
- The answer must survive "What exactly did you own versus your team?".
- Separate personal actions from team outcomes when needed.

5. Tradeoff and judgment
- Show at least one engineering judgment when the prompt allows it: risk reduction, staged rollout, compatibility, failure containment, correctness versus speed, latency versus consistency, or operational safety.

6. Impact
- Include measurable impact when available. If numbers are unavailable, state user impact, reliability impact, risk reduction, or operational improvement.
- Do not invent metrics.

7. Spoken clarity
- The answer should be natural to say in 30, 60, or 90 seconds.
- The labeled answer length must match realistic spoken delivery, including pauses.
- Prefer one fluent script over fragmented notes when the user asks for a final answer.

8. Follow-up resilience
- Add likely follow-up questions and a short answer strategy.
- Flag weak points if a follow-up would expose missing evidence, vague motivation, or overbroad claims.

9. Interviewer challenge simulation
- Test the answer against: "What do you mean by that?", "Why this company specifically?", "Can you give a concrete product or infrastructure example?", "How is this connected to your Samsung backend experience?", and "What exactly did you own?".
- If the answer cannot handle these questions, rewrite before presenting it as final.

When a draft fails any gate, label it as provisional and explain what information is missing or what should be tightened.

## Workflow

1. Build story inventory
- Collect 8-12 real experiences across leadership, conflict, failure, ambiguity, and impact.

2. Map to prompt families
- Group stories by common interview dimensions (ownership, collaboration, judgment, growth).

3. Rewrite with STAR discipline
- Situation: only necessary context.
- Task: explicit responsibility.
- Action: concrete decisions and actions.
- Result: measurable impact and learned lesson.
- Run the Pre-Draft Guardrails before writing the first polished script.

4. Stress-test with follow-ups
- Ask "what would you do differently", "how did you measure impact", and "how did you influence others".
- Tighten answers to 60-120 seconds.

5. Final coaching
- Flag vague wording, missing ownership, and weak results.
- Provide stronger, concise alternatives.
- Run the Backend Answer Quality Gate before calling the answer final.

6. Notion write gate
- If the output will be written to the Notion script library, run the Direct Notion Write Review Loop before creating or updating the page.
- A draft can be shown in chat before the loop is clean, but it must be labeled provisional.

## Output Format

1. Story Bank (tagged by theme)
2. STAR Rewrite Set
3. Follow-up Q&A Drill
4. Weak Signal Fixes
5. Final 60-120s Interview Scripts
6. Quality Gate Assessment
7. Abstract Phrase Check
8. Company-Specific Evidence Status
9. Interviewer Challenge Simulation
10. Direct Notion Write Review Summary, when Notion was updated

## References

- Prompt families and examples: `references/prompt-families.md`
