---
name: hero-content-maker
description: >-
  Create and optionally publish a coordinated three-part ILIAS lesson pack:
  polished PDF slides, an applied exercise, and a concise course announcement,
  grounded in verified teaching videos. Use when a user invokes Hero Content
  Maker or asks to turn a topic into a complete, course-ready ILIAS content pack.
  Do not use when the user only wants one existing ILIAS item edited or only
  wants resource recommendations.
---

# Hero Content Maker

Turn one teaching topic into exactly three coordinated deliverables:

1. a slide deck;
2. an exercise;
3. an announcement.

The videos are cited learning sources inside the pack, not extra deliverables.
Optimize the three items as one lesson experience rather than three independent
pieces of text.

## Required companion workflows

Use `find-teaching-content` to discover, compare, and verify videos. Use
`ilias-portal` for course resolution, authentication, publishing, and verified
results. Never bypass its confirmation or ambiguity safeguards.

The YouTube Data API v3 may be used for structured discovery when configured:
use `search.list` to find candidates and `videos.list` to verify metadata such
as duration and caption availability. A native web/video search is an acceptable
fallback. In either case, open serious candidates and verify their direct watch
pages before using them.

## Inputs and ordinary defaults

The topic is required. Reuse context already supplied by the user. Infer these
defaults when they do not materially affect the result:

- learner level: introductory;
- language: the language used by the user;
- lesson duration: 45–60 minutes;
- video role: one core explanation and, when useful, one distinct worked example;
- announcement visibility: course members.

Do not invent a deadline, grading policy, course, or prerequisite. A pack may be
drafted without them, but resolve them before publishing when they are needed.

## Workflow

### 1. Resolve the teaching target

Establish the topic, audience, lesson duration, and desired learning outcome.
For publishing, also resolve the exact ILIAS course and deadline. If the course
is ambiguous, list available courses and ask the user to choose; do not guess.

### 2. Build a small verified evidence set

Find three to five plausible videos, then select no more than two that add
different teaching value. Prefer official projects, universities, authors, or
recognized educators. Verify title, creator, direct URL, availability, and the
evidence used for the summary. Prefer transcript evidence; otherwise use visible
chapters and descriptions and label that limitation.

Reject candidates that are inaccessible, misleadingly titled, unnecessarily
long for the lesson, or only supported by a search snippet. Do not copy
transcripts or imply that a video was watched when only its metadata was checked.

### 3. Design one instructional arc

Define two to four measurable learning objectives and make every deliverable
support them. Use a coherent progression:

`motivation -> core idea -> worked example -> learner practice -> check and next step`

The slides explain and model the idea. The exercise makes students apply it.
The announcement tells students why the pack matters and exactly what to do.
Avoid repeating the same paragraphs across all three.

### 4. Create the three deliverables

Create three reviewable Markdown files with a shared, collision-resistant slug:

- `<slug>-slides.md`
- `<slug>-exercise.md`
- `<slug>-announcement.md`

Use a user-selected output directory when supplied; otherwise use a task-scoped
local directory and report its absolute path. Read
[quality-and-templates.md](references/quality-and-templates.md) before drafting
or reviewing the deliverables.

The slide file must include PDF styling and explicit page breaks compatible with
the project's `md-to-pdf` renderer. The exercise file contains the exact title,
instructions, deliverables, estimated effort, and rubric that will be sent to
ILIAS. The announcement file contains the exact title and body, including the
selected video links and placeholders for the published slide and exercise URLs.

### 5. Run the quality gate

Before presenting the pack, verify:

- factual claims are supported by the reviewed sources or stable knowledge;
- the learning objectives, examples, exercise, and rubric align;
- the exercise requires application rather than copying the videos;
- instructions are complete enough that a student can begin without guessing;
- slides are scannable, visually consistent, and not paragraph-heavy;
- links are direct, available, and attributed;
- accessibility does not depend on color, audio, or images alone;
- the announcement is concise and action-oriented;
- no deadline, course fact, video metadata, or publication result was invented.

Revise weak content before asking for publication approval.

### 6. Review once, then publish

Show a compact preview containing:

- selected videos and their verification basis;
- the three exact titles and file paths;
- learning objectives and exercise rubric summary;
- exact course, deadline or no deadline, and announcement visibility.

Ask for one grouped confirmation covering all three ILIAS writes. Drafting alone
does not require confirmation. If the user requested publishing but required
details remain unresolved, ask only for those details.

Immediately before writing, run `ilias_check_setup` and inspect current course
contents for conflicting titles. Refresh authentication once when the ILIAS
skill requires it. Do not silently overwrite or duplicate an existing item.

By default, publish the slide deck as a folder-style ILIAS lecture content item,
matching the ordinary ILIAS pattern that has its own content page and contains
the rendered PDF as a child file. Use a descriptive lecture title for the
folder and the lesson summary as its description. Treat the folder/content-page
URL as the canonical slides URL; do not return the child PDF download URL as the
main result. If the target course does not permit creating this structure, stop
and report that limitation instead of silently falling back to a bare file in
the course root.

Publish in this order:

1. render the slide Markdown to PDF, create the folder-style lecture content
   item, and upload the PDF inside it;
2. `ilias_publish_assignment` with the reviewed exercise fields;
3. replace the announcement placeholders with the returned slide and exercise
   URLs, then call `ilias_publish_announcement`.

After creating the slide content item, verify that its page shows the expected
folder title and the PDF child. Use the stable folder page URL (for example,
`ilias.php?baseClass=ilrepositorygui&ref_id=<folder_ref_id>` or the equivalent
`goto.php/fold/<folder_ref_id>`) in the announcement and final report.

Make each agent-level publishing call once. If a write fails, stop the remaining
writes, clearly report what was and was not published, and do not claim the pack
is complete. Do not delete successfully published items unless the user asks.

### 7. Report the result

On full success, return the three ILIAS URLs, the selected source links, and the
local artifact directory. Say explicitly that the slides, exercise, and
announcement were successfully published. On draft-only runs, return the three
file links and state that nothing was published.
