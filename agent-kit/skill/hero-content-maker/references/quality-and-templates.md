# Hero Content Quality and Templates

Read this reference whenever Hero Content Maker drafts or reviews a lesson pack.

## Shared lesson contract

Start with a compact contract that drives all three deliverables:

- topic and learner level;
- two to four measurable learning objectives;
- assumed prerequisites;
- estimated lesson and exercise time;
- one core misconception to prevent;
- one core video and, only when it adds distinct value, one extension video.

Prefer objectives with observable verbs such as explain, compare, implement,
diagnose, interpret, or evaluate. Avoid vague objectives such as “understand.”

## Slides: 8–12 purposeful pages

Each page should do one job. A strong default sequence is:

1. title and useful hook;
2. learning objectives and prerequisites;
3. problem or motivation;
4. core mental model;
5. mechanism or process;
6. worked example;
7. second example or visual comparison;
8. common failure modes;
9. selected video and a focused viewing question;
10. retrieval check;
11. summary;
12. bridge to the exercise.

Use fewer pages when the topic is narrow. Prefer short bullets, diagrams made
from simple tables or text, concrete examples, and highlighted takeaways. Avoid
dense prose, decorative claims, unexplained jargon, and generic filler.

The slide Markdown should begin with renderer-compatible frontmatter like this:

```markdown
---
pdf_options:
  width: "13.333in"
  height: "7.5in"
  margin: "0"
  printBackground: true
css: |-
  @page { size: 13.333in 7.5in; margin: 0; }
  body { margin: 0; color: #172033; background: #f7f9fc; font-family: Inter, Arial, sans-serif; font-size: 24px; line-height: 1.35; }
  .markdown-body { box-sizing: border-box; max-width: none; min-height: 7.5in; padding: 0.62in 0.82in; }
  h1 { color: #12355b; font-size: 44px; margin: 0 0 24px; }
  h2 { color: #146c94; font-size: 32px; }
  strong { color: #b54708; }
  code { font-size: 0.82em; }
  table { width: 100%; font-size: 0.78em; }
  img { display: block; max-width: 88%; max-height: 4.7in; margin: 18px auto; }
  .page-break { page-break-after: always; }
---
```

Put `<div class="page-break"></div>` between pages. Keep every page within a
single 16:9 sheet. Use descriptive link text and include the direct video URL in
the resource page so it remains useful in the PDF.

## Exercise: authentic application

The exercise should contain:

- a motivating scenario or question;
- explicit prerequisites;
- numbered steps with expected outputs;
- concrete submission deliverables and accepted formats;
- estimated effort;
- deadline only when provided;
- two or three progressive hints that do not reveal the full solution;
- an optional extension that rewards deeper exploration;
- links to the selected videos with one sentence explaining when to use each;
- a transparent 100-point rubric with three to five criteria.

Award most points for applying, reasoning about, or evaluating the concept—not
for formatting. Ensure every rubric criterion maps to a requested deliverable.
Do not include a complete solution in student-facing instructions.

## Announcement: concise action layer

Keep the announcement around 90–160 words unless the user requests otherwise.
Use this order:

1. why the topic matters now;
2. what is available;
3. what students should do and in what order;
4. deadline, or an explicit statement that no deadline is set when useful;
5. slide, exercise, and selected video links;
6. one encouraging closing sentence with a concrete support route.

Do not paste the exercise instructions into the announcement. Its job is to
orient and activate students.

## Final alignment test

A pack passes only when a reviewer can answer yes to all of these:

- Can each learning objective be located in the slides and assessed in the exercise?
- Does the worked example prepare students without solving the exercise for them?
- Does each video have a specific instructional role and verified evidence basis?
- Does the rubric reward the outcomes named in the objectives?
- Does the announcement give a clear sequence and use the final published URLs?
- Would a learner know what success looks like and where to get help?
