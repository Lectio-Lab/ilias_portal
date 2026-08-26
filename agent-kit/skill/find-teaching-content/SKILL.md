---
name: find-teaching-content
description: >-
  Find, compare, and summarize verified YouTube videos and other educational
  resources, then optionally add a selected link with a short summary to ILIAS.
  Use when a user asks for teaching videos, lectures, tutorials, articles,
  documentation, interactive lessons, learning resources, or course-ready links.
---

# Find Teaching Content

Find resources that fit the learner and teaching goal, not merely popular search
results. Use native web or video search available in the current agent.

## Discovery workflow

1. Identify the topic, learner level, preferred language, resource type, and any
   duration or recency constraint. Infer ordinary defaults when they do not
   materially change the search.
2. Search current sources. For YouTube, prefer direct watch pages from official
   projects, universities, recognized educators, or authors with demonstrated
   subject expertise. Also consider authoritative documentation, open courses,
   notebooks, and interactive tutorials when they teach the topic better.
3. Open each serious candidate and verify its title, creator, direct URL,
   availability, and the metadata actually visible. Do not summarize from a
   search-result snippet alone.
4. Use a transcript when available. Otherwise use chapters and the creator's
   description, and label the summary as metadata-based. Never imply that the
   resource was watched or fully reviewed when it was not.
5. Rank a small set by topical fit, source authority, teaching clarity,
   accessibility, learner-level fit, and freshness where freshness matters.

Read [references/selection-and-publishing.md](references/selection-and-publishing.md)
when comparing multiple candidates or preparing an ILIAS addition.

## Expected result

For each recommended resource provide:

- title, resource type, creator/source, and direct link;
- duration and publication/update date when verified and relevant;
- a two- or three-sentence summary of what it teaches;
- why it fits the requested audience or lesson;
- evidence basis: transcript, chapters/description, or page contents.

Lead with the strongest recommendation. Keep alternatives meaningfully distinct.

## Add to ILIAS

Only publish when the user explicitly asks to add or share a selected resource.
Use the `ilias-portal` skill for authentication, course/item resolution,
confirmation, mutation, and verification.

- For a course-wide resource, publish an announcement containing the title,
  direct link, short summary, and why it is useful.
- For an exercise-specific resource, re-fetch the exercise and append a clearly
  titled **Additional Learning Resource** section with the link and summary.
- If the course, exercise, or selected candidate is ambiguous, resolve it before
  writing. Never publish every search result unless the user asks for all of them.
- Report success only after ILIAS verification and return the resulting ILIAS URL.

## Evidence and safety

- Keep attribution and link to the original source.
- Do not reproduce transcripts, paid course material, or substantial copyrighted
  text. Summarize in original language.
- Flag login requirements, region restrictions, age restrictions, sponsorship,
  or inaccessible captions when discovered.
- Do not invent duration, publication date, credentials, learning outcomes, or
  transcript details.
