# Selection and ILIAS Publishing Guide

Use this guide when ranking several teaching resources or converting a selected
resource into course-ready ILIAS text.

## Candidate scoring

Assess each candidate on the evidence available. Do not fabricate a numeric
precision the evidence cannot support.

1. **Topical fit** — directly teaches the requested concept and desired depth.
2. **Authority** — official project, university, author, or educator with visible
   subject expertise.
3. **Teaching quality** — clear structure, demonstrations, examples, and useful
   pacing; captions or transcript improve accessibility.
4. **Audience fit** — prerequisites, language, duration, and complexity suit the
   intended learners.
5. **Currency** — APIs, interfaces, laws, and fast-changing technologies require
   recent material; foundational concepts may favor an older excellent resource.
6. **Access** — direct public link, no unexpected paywall or mandatory account,
   and no unresolved region or age restriction.

Popularity, view count, and search position are weak signals. Use them only as
secondary evidence.

## Verification levels

- **Transcript reviewed:** summary may describe specific covered concepts and
  examples supported by the transcript.
- **Chapters/description reviewed:** summarize the stated scope and structure;
  do not claim the full presentation was reviewed.
- **Page contents reviewed:** for articles, documentation, labs, or notebooks,
  summarize visible headings and substantive content.
- **Metadata only:** treat as a candidate, not a strong recommendation, unless
  the user explicitly accepts that limitation.

## Recommendation format

```markdown
### Resource title

- Type/source: YouTube video — Creator
- Link: https://...
- Duration/date: verified values, when available
- Summary: Two or three original sentences.
- Teaching fit: One sentence explaining audience and lesson fit.
- Evidence: Transcript reviewed | Chapters/description reviewed | Page reviewed
```

## ILIAS announcement template

```markdown
Recommended learning resource: Resource title

Link: https://...

Summary: Two or three sentences describing what the resource teaches.

Why this is useful: One sentence tied to the course topic or assignment.
```

Use `ilias_publish_announcement` after the user confirms the exact course,
resource, title, link, and summary. Return the verified ILIAS URL.

## Exercise append template

```markdown
Additional Learning Resource

- Resource title — https://...
  Short summary explaining what students will learn and how it supports the task.
```

Before using `ilias_edit_exercise`, re-fetch the current instructions. Append the
section once, preserve all unrelated text, pass current `expected_*` values, and
verify that both the link and summary appear afterward. If the same canonical
link is already present, do not duplicate it; report that it is already attached.
