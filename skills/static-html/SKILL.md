---
name: static-html
description: Creates polished, self-contained single-page HTML files with embedded JavaScript, CSS, and assets. Uses React for interactivity and compiled Tailwind for styling. Use for shareable offline pages, interactive briefs, calculators, reports, and small dashboards that open directly in a browser without a server or installation.
---

# static-html

Create a finished, shareable HTML page that works offline when opened directly from disk. The recipient needs only the HTML file and a browser. Unlike a throwaway prototype, the deliverable should have accurate content, polished presentation, and working controls.

## Output contract

- Deliver one `.html` file containing all required JavaScript, CSS, images, icons, fonts, and initial data. No companion asset directory, CDN scripts, remote stylesheets, external font requests, runtime imports, or API calls.
- Download dependencies during authoring as needed; the exported page must not download anything to render or operate. Ordinary outbound links are fine, but following them is not an offline feature.
- Support `file://` opening without a development server, package installation, or build step for the recipient. Do not rely on service workers, fetching sibling files, or server routes.
- Keep interaction state in memory by default. Explicit local file selection and download/export controls are fine when requested; do not add persistence, uploads, analytics, authentication, or a backend by default.
- Never embed secrets. Treat embedded data as readable by anyone who receives the file, regardless of what the UI hides. Use only data intended for that audience; clearly label sample data.

## 1. Establish the page's purpose

Use the conversation and supplied content to identify the audience, the job the page should do, required interactions, and any visual references. Ask only about missing details that materially affect the result. Otherwise state reasonable assumptions and proceed.

Choose a descriptive filename. Use the user's requested destination or the repository's artifact convention; otherwise use `.agentic/<slug>/<slug>.html`. Preserve existing files and unrelated project configuration.

Match established branding when supplied. For open-ended visual exploration, follow available design guidance and tools before implementation. Do not turn a straightforward page request into a mandatory design interview.

## 2. Author the page

- Use React with TypeScript (`.tsx` components and `.ts` logic) for meaningful interactive state and Tailwind for styling. For a read-only page, plain HTML with compiled Tailwind is sufficient; do not include React solely to render static text.
- Reuse suitable local build tooling. Otherwise use a small isolated build workspace with React, React DOM, TypeScript, their corresponding React type definitions, a bundler such as esbuild, and Tailwind's build-time tooling. Keep dependencies and lockfiles out of unrelated application manifests.
- Prefer `pnpm dlx` for build CLI commands, falling back to `npx` when pnpm is unavailable; do not require global tool installs. Use explicit compatible package versions. For TypeScript, invoke the `tsc` binary from the `typescript` package (for example, `pnpm --package=typescript@<version> dlx tsc --noEmit` or `npx --package=typescript@<version> tsc --noEmit`), not the unrelated `tsc` package. Install imported dependencies such as React, React DOM, their type definitions, and Tailwind into the isolated workspace with pnpm (or npm); transient CLI execution does not make those packages resolvable from the page's source.
- Build a responsive layout with semantic headings, labelled controls, visible keyboard focus, adequate contrast, and usable narrow-screen layouts. Prefer system fonts; embed licensed font files if custom fonts are needed.
- Implement only useful controls, and make each one work. Do not ship placeholder buttons, invented claims, or fabricated data presented as real.
- Keep Tailwind class names statically discoverable, or explicitly include every runtime-selected class in the generated CSS using the installed version's supported mechanism.
- Treat pasted or locally imported data as untrusted content. Render it as text rather than interpolating it into raw HTML or executable JavaScript.

## 3. Build and embed

When creating a fresh build workspace, read [the build recipe](reference/build-recipe.md) and run its setup, type-check, bundle, CSS, and embedding steps. It supplies exact pnpm commands, npx fallbacks, a TypeScript configuration, and the targeted install-script allowance encountered in testing. Reuse equivalent existing tooling when available.

1. Type-check TypeScript sources with `tsc --noEmit` using strict checking and appropriate JSX, DOM, and module-resolution settings. Fix type errors before bundling; transpilation alone is not a type-check. Compile TSX/TypeScript to JavaScript and bundle the application with React and React DOM in production mode. Minify the output and use a browser-compatible self-contained script, such as an IIFE. Do not externalize dependencies, emit runtime chunks, or ship a browser-side TypeScript/JSX compiler.
2. Compile Tailwind into ordinary CSS for the classes the page uses, including base styles. Do not use Tailwind's browser/CDN runtime.
3. Inline the generated CSS into `<style>` and JavaScript into `<script>` in a complete HTML document with a title, UTF-8 charset, and viewport metadata. Preserve required license notices.
4. Embed images and fonts as data URLs or inline SVG. Resolve CSS `url(...)` and `@import` dependencies too; embedding a stylesheet alone does not embed the assets it references. SVGs must not reference external assets.
5. Serialize embedded data safely for its HTML context. Literal closing script/style tags inside embedded content can terminate those elements even inside JavaScript strings; use the bundler's inline-script safety support and context-appropriate escaping rather than naive concatenation. Escape `<` in serialized JSON embedded in a script element.
6. Ensure there are no runtime file paths, external source-map references, development clients, or hidden network dependencies. Keep editable source/build files if useful for requested revisions, but the delivered HTML must function without them. Remove disposable build scratch files when done.

## 4. Verify the exported artifact

Test the final `.html` file, not just the development preview. Use available browser tooling and load its skill when applicable.

- Open the exported file via `file://` in a fresh browser context with network access blocked. Avoid cached resources masking dependencies. Confirm the page renders and makes no attempted HTTP(S) requests during loading or its required interactions.
- Inspect the browser console for errors. Exercise the meaningful controls and verify their outputs, not merely that clicks succeed. Include affected non-default states and relevant empty/invalid-input states.
- Render at representative wide and narrow viewport sizes. Capture screenshots and inspect them for clipping, unreadable text, missing assets, and layout problems; fix problems and inspect a new capture.
- Check keyboard access, control labels, and focus behavior. If the page imports or exports data, exercise that path using disposable sample data.
- If a check cannot run, state the limitation. Do not call the page verified offline based only on inspecting its source or serving it through a local web server.

## 5. Deliver

Link the finished HTML file and briefly explain what it does and how to open it. Include one inspected representative screenshot when available and summarize the checks actually run, including any limitations. Do not report file size unless asked.

Ask, "Would you like me to start a local preview server?" before starting one, unless the user already explicitly requested serving the page. Use a simple static server such as `python -m http.server`; if `python` is unavailable, use `uv run --no-project --python 3 python -m http.server`. Serve only the output directory and provide its accessible preview URL. Follow the environment's service-management instructions. The preview is a convenience, not a replacement for the downloadable HTML; permission to preview is not permission to deploy or publish the page.
