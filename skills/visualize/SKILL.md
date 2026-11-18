---
name: visualize
description: Produces the smallest visualization that makes a point from the current conversation clear, from an ASCII sketch in the reply to an HTML page rendered from bundled Mermaid or UI mockup templates with hash-pinned libraries, grounded in the application's real UI when the topic is user-facing. Use when the user asks to visualize, sketch, draw, diagram, or picture something, says a picture would help, or wants a diagram kept in the repository.
---

# Visualize

Draw the least that makes the idea click. The picture answers one question from
the current conversation, using its real names, code, data, and UI.

By default the picture is a throwaway aid for understanding. When the user wants
a diagram kept in the repository, see [Keep a diagram](#keep-a-diagram). For a
polished interactive page, use `static-html`.

## Choose what to show

- Use the user's argument when given, such as `/visualize the deploy order`.
- Otherwise visualize the main point of your most recent substantive
  explanation, proposal, or answer.
- Write down the one question the picture answers, such as "In what order do the
  three services start?" It becomes the title. If the picture would answer
  several questions, pick the one most likely confusing the user and name it so
  they can redirect you.
- Ask which idea they mean only when the candidates are equally likely and the
  wrong picture would waste their time. Then wait.

## Pick the smallest form

Use the first form that works:

1. **ASCII in the reply** (default). Boxes and arrows, a short flow, a timeline,
   a state machine with a few states, a memory or data layout, a table, a rough
   screen layout, before and after. Keep it within 80 columns in a fenced `text`
   block.
2. **Mermaid page** (`templates/mermaid.html`). When ASCII would get tangled:
   branching flows, more than about eight nodes, sequence diagrams with several
   participants, state, class, and ER diagrams, Gantt or timeline charts, and
   simple charts (`xychart-beta`, `pie`). If the client renders fenced
   `mermaid` blocks in the reply, use a block instead of a file.
3. **Mockup page** (`templates/mockup.html`). When the question is about what
   users see: a layout, the states of a screen, the path between screens, or a
   proposed UI change. See [Ground UI in the real app](#ground-ui-in-the-real-app).

Keep it minimal in content as well as form:

- Include only the elements the question needs. Collapse the rest into one
  labeled box ("auth service, unchanged") or leave it out.
- Label things with the conversation's real names: files, functions, services,
  tables, screens, and copy.
- Highlight the one part that matters, such as the changed step, the race, or the
  failing branch. Add a legend only when a symbol is not self-explanatory.
- Mark anything simplified or invented.

## Ground UI in the real app

When the topic touches what users see, look at the real application before
drawing.

- **See it first.** Use screenshots already in the conversation, an app or
  preview that is already running, or the repository's documented dev, preview,
  or Storybook command. Capture the affected screens and states with the
  client's browser or simulator tooling. Ask before starting anything that needs
  credentials, writes to shared or external state, or takes heavy setup.
- **Then read the source.** Read the components, templates, styles, design
  tokens, and copy that render the screen.
- **Prefer the real thing.** Often the whole visualization is one or two
  screenshots with numbered callouts, or current and proposed side by side.
- **Build mockups from the real UI.** Reuse the app's markup structure, class
  names, compiled CSS (pass it with `--css`), and copy. Do not draw a generic UI
  kit. For a proposed change, show the real current state next to the proposal
  and change only what the proposal changes.
- **Say what is not real.** If you could not see the running app, say so, and
  label any part based only on source code or invented.

## Render HTML forms

Resolve `VISUALIZE_DIR` to the absolute directory containing this `SKILL.md`
from the client's supplied skill path, and check that `scripts/render.py` and
`templates/` exist there. Keep the shell in the user's project so relative paths
resolve there.

Write the source next to the output, under `.agentic/visualize/` unless the user
or client names another location:

```bash
python3 "$VISUALIZE_DIR/scripts/render.py" mermaid \
  .agentic/visualize/deploy-order.mmd .agentic/visualize/deploy-order.html \
  --title "In what order do the services start?"

python3 "$VISUALIZE_DIR/scripts/render.py" mockup \
  .agentic/visualize/empty-cart.body.html .agentic/visualize/empty-cart.html \
  --title "Empty cart: current vs. proposed" --css path/to/app/built.css
```

Libraries load from jsDelivr at exact versions with Subresource Integrity
(`integrity="sha384-..."`) hashes from the `PINS` table in `scripts/render.py`,
so the browser refuses a script whose bytes changed. Never add an unpinned or
unhashed `<script>` or stylesheet to a page, and ask the user before adding a
new library (see [Add a mockup library](#add-a-mockup-library)). Viewing a
page needs network access to jsDelivr.

- **Mermaid:** the source is one diagram per file of Mermaid text (`.mmd`). The
  page sets
  `data-viz-status` on `<body>` to `ok` or `error` and shows parse and load
  errors on the page.
- **Mockup:** the source is an HTML fragment that goes into `<body>`. Local
  `<img src>` paths are embedded as data URLs, and every `--css` file is
  inlined. CSS `url()` assets are not embedded.
  - `--lib tailwind` loads the Tailwind browser build, which compiles the
    classes used on the page. Use it when the app uses Tailwind, so its real
    class names work, or when there is no app CSS to reuse.
  - `--lib react` loads React 18 and Babel. Put components in
    `<script type="text/babel">` and render them with
    `ReactDOM.createRoot(...)`. Use it only when the picture needs state, such as
    a toggle between the screen's states; static markup is smaller.
  - `--lib recharts` loads Recharts 3 (use with `--lib react`), exposed as the
    global `Recharts`. Use it for a chart Mermaid's `xychart-beta` or `pie`
    cannot show, such as several series, tooltips, or the app's own chart
    components.

  Use these chrome classes, which are styled after the app CSS so they win:

  ```html
  <div class="viz-row">
    <figure class="viz-frame">
      <figcaption>Current</figcaption>
      <img class="viz-shot" src="cart-current.png" alt="Current empty cart">
      <span class="viz-mark" style="top: 120px; left: 40px">1</span>
    </figure>
    <figure class="viz-frame">
      <figcaption>Proposed</figcaption>
      <!-- the app's real markup and class names -->
    </figure>
  </div>
  <ol class="viz-notes"><li>The empty state has no way back to the catalog.</li></ol>
  ```

  `viz-highlight` outlines an element in red.

The output is one HTML file that opens from disk. Check it before sharing: open
it with the client's browser tooling, confirm the console has no errors,
`data-viz-status="ok"` for Mermaid, capture a screenshot, and look at it for
overlap, clipping, unreadable text, and whether the answer to the question
stands out. Fix the source, render again, and check again. If no browser tooling
is available, say the page was not visually checked.

### Add a mockup library

Add one only when a visualization needs it, not in advance. Before adding or
bumping any library in `PINS`, ask the user and wait for approval. Name the
package, the exact version, the file, and why the existing libraries cannot do
the job. Without approval, use the libraries already pinned or a smaller form.

1. Find a single-file browser build (UMD, IIFE, or global) at an exact version.
   ESM builds that import other modules do not qualify.
2. Check that the npm package is published by the project itself: its
   `repository` is the vendor's own repository (`npm view <package>@<version>
   repository.url maintainers`). jsDelivr serves files from npm, so confirm the
   file it serves is byte-identical to the one in the npm tarball
   (`npm pack <package>@<version>`, extract it, and compare hashes).
3. Run `python3 "$VISUALIZE_DIR/scripts/render.py" pin <package>@<version>/<file>`
   and add the printed entry to `PINS`, listing the libraries it needs first.
4. Open a page that uses it and list every script resource it loaded, for
   example with `performance.getEntriesByType("resource")`. Every script must
   come from a hashed tag on the page. If the library fetches more scripts at
   runtime, pin those files too and load them first. If that is not possible, the library does not qualify. Fonts and other
   assets from the same pinned version are acceptable.
5. Add its name to `MOCKUP_LIBS`.
6. Render a sample and check it as described above, including a page with one
   hash character changed, which must fail to load.

## Keep a diagram

When the user asks to keep a diagram, write it where they say, or under the
repository's existing docs or diagrams directory. Keep the source next to it;
the source is what later edits change.

- In Markdown docs that GitHub or GitLab render, prefer a fenced `mermaid` block
  in the document itself. It needs no separate file.
- Otherwise render the Mermaid page next to its source, such as
  `docs/diagrams/auth-flow.mmd` and `docs/diagrams/auth-flow.html`. To change
  it, edit the source and render again; do not edit the HTML.

## Deliver

- **ASCII:** the block, then one or two sentences on how to read it and what to
  notice.
- **HTML:** link the file and show the inspected screenshot when the client can
  display images. Add one or two sentences on what to notice.

This is explanation only. Do not edit application code or continue the
underlying task; read-only inspection, the files under `.agentic/visualize/`,
and a diagram the user asked to keep are fine. After the visualization, stop
and let the user respond.
