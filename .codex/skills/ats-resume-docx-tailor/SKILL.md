---
name: ats-resume-docx-tailor
description: Use when EUNWHA provides a job posting, JD, target company, or internship/new-grad role and asks to create, rewrite, optimize, or export an ATS-friendly resume as an editable DOCX or Google Docs-ready source.
---

# ATS Resume DOCX Tailor

## Overview

Create one truthful, JD-specific resume source in `.docx`, optimized for ATS parsing and recruiter skim. Prefer a strong one-page SWE resume over keyword stuffing.

## Required Inputs

Use existing context when available. Ask only for missing facts that affect truthfulness:

- Target JD or job posting text/URL.
- Current resume source, if not already provided.
- Current school, degree, expected graduation, and internship eligibility for student roles.
- Real LinkedIn/GitHub URLs.
- Tools/skills that must be defensible in interview, especially AI coding tools and frontend skills.

## Workflow

1. Parse the JD.
   - Extract must-have keywords, preferred keywords, role level, product/domain signals, and hidden criteria.
   - For internships, explicitly check student enrollment, expected graduation, returning-to-school requirement, OOP/OOD, algorithms, data structures, SQL, Java/JavaScript/web, collaboration, and AI-assisted development.

2. Reuse EUNWHA's evidence.
   - First read `/Users/eunhwa/.codex/skills/jd-resume-tailor/SKILL.md`.
   - When needed, read its references:
     - `/Users/eunhwa/.codex/skills/jd-resume-tailor/references/eunhwa-master-evidence.md`
     - `/Users/eunhwa/.codex/skills/jd-resume-tailor/references/role-archetypes.md`
     - `/Users/eunhwa/.codex/skills/jd-resume-tailor/references/bullet-templates.md`
   - Preserve strongest truthful evidence: 78B+ rows, 50TB+, 3 regions, zero downtime, 100% data integrity, $2M+ / 95% cost reduction, DynamoDB single-table modeling, Cassandra at 18K+ QPS, IAM modernization, EKS migration, 56M+ users, 61% runtime reduction, and Apache Zeppelin recognition.

3. Build the targeted resume.
   - Summary: make target fit obvious in 2-4 lines.
   - Skills: order by JD priority, not by personal preference.
   - Experience: put the 4 strongest JD-matching bullets first.
   - Education: for student roles, include current or incoming program and expected graduation if true.
   - Open source/certifications: keep concise unless the JD directly rewards them.

4. Protect truthfulness.
   - Do not fabricate AI/LLM platform work, US work authorization, on-call ownership, staff/manager scope, production frontend ownership, or unsupported metrics.
   - If the user has study/project-only frontend experience, label it as coursework/projects rather than production experience.
   - If a program starts in the future, write `Incoming Fall YYYY` rather than implying current enrollment before matriculation.

5. Create the DOCX.
   - Use the `documents` skill when available.
   - Use a single-column, text-first layout. Avoid tables, text boxes, icons-only links, graphics, skill bars, photos, headers/footers, and two-column templates.
   - Use real visible text for email, LinkedIn, and GitHub.
   - Follow `references/docx-style.md` for typography and spacing.
   - Keep the editable `.docx` as the primary deliverable. Create PDF only when the user asks or when submitting directly requires PDF.

6. Verify before final handoff.
   - Run DOCX render QA with `render_docx.py` if `soffice` is available.
   - If render QA is unavailable, use a fallback visual check such as QuickLook when possible and run structural checks.
   - Run `scripts/check_resume_docx.py <docx>` or equivalent checks for readable text, links, placeholders, page-oriented density, and target keywords.
   - Confirm no placeholders like `[TODO]`, `[Company]`, or unsupported bracketed claims remain.

## Output Standard

Deliver:

- A final `.docx` link.
- Optionally a matching `.pdf` link only if requested.
- A short note listing the important ATS keywords covered and any verification limitation.

Do not paste the full resume back into chat unless the user asks for text review.

## Common Decisions

- Default font: Arial.
- Default body size: 10 pt when possible; use 9.5 pt only to preserve one page.
- Section headings: 10.5-11 pt bold.
- Name: 18-22 pt bold.
- Contact line: 9 pt.
- Margins: 0.5-0.75 inch.
- Prefer removing weaker bullets over shrinking below 9 pt.
