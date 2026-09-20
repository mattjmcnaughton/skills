# Standalone React + TypeScript + Tailwind recipe

Use this when there is no suitable existing build setup. Run commands from a dedicated build directory, not the host application's root. The versions below are a tested baseline, not a claim that they are the latest or indefinitely secure. If compatibility or a security advisory requires changing a version, pin the replacement and rerun the build and offline checks.

## 1. Prepare the workspace

Create `package.json` in the new directory (do not overwrite an existing manifest):

```json
{"private": true, "type": "module"}
```

Install dependencies that must resolve from the page's source:

```bash
pnpm add --save-exact react@19.2.0 react-dom@19.2.0 \
  @types/react@19.2.2 @types/react-dom@19.2.2 tailwindcss@4.1.18
```

If pnpm is unavailable, use `npm install --save-exact` with the same packages. Keep the generated lockfile with retained build sources. `dlx`/`npx` supply CLI executables; they do not replace these local dependencies.

Create `tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "jsx": "react-jsx",
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "resolveJsonModule": true,
    "lib": ["ES2022", "DOM"],
    "skipLibCheck": true
  },
  "include": ["*.tsx", "*.ts", "src/**/*.tsx", "src/**/*.ts"]
}
```

Author `app.tsx`, mounting React into `document.getElementById('root')`. Create `style.css` with the following prelude, then add page-specific CSS:

```css
@import "tailwindcss" source(none);
@source "./app.tsx";
```

Add explicit `@source` entries for additional component directories. Restricting scanning prevents embedded datasets, unrelated files, and previous build outputs from generating unwanted utility classes.

## 2. Type-check and compile

Run in order and stop on any failure:

```bash
pnpm --package=typescript@5.9.3 dlx tsc --noEmit

pnpm dlx esbuild@0.27.2 app.tsx \
  --bundle --minify --format=iife --legal-comments=inline \
  --supported:inline-script=true \
  --define:process.env.NODE_ENV='"production"' \
  --outfile=compiled.js

pnpm dlx --allow-build=@parcel/watcher @tailwindcss/cli@4.1.18 \
  -i style.css -o compiled.css --minify
```

The targeted `@parcel/watcher` allowance is needed by pnpm versions that block this install script by default; the tested pnpm 12 setup otherwise fails with `ERR_PNPM_IGNORED_BUILDS`. Do not replace this with blanket lifecycle-script approval. If an older pnpm lacks `--allow-build`, follow its supported targeted approval mechanism or use the npm fallback.

Equivalent commands when pnpm is unavailable:

```bash
npx --yes --package=typescript@5.9.3 tsc --noEmit
npx --yes esbuild@0.27.2 app.tsx \
  --bundle --minify --format=iife --legal-comments=inline \
  --supported:inline-script=true \
  --define:process.env.NODE_ENV='"production"' \
  --outfile=compiled.js
npx --yes @tailwindcss/cli@4.1.18 -i style.css -o compiled.css --minify
```

Use the `typescript` package, not the unrelated `tsc` package. A successful esbuild run does not establish type correctness. npm may run package install scripts under its normal policy; `npx` is not a sandbox.

## 3. Embed the outputs

Create `embed.mjs`:

```js
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';

const css = readFileSync('compiled.css', 'utf8');
const js = readFileSync('compiled.js', 'utf8');
// esbuild's inline-script handling escapes script terminators. Fail rather
// than silently producing malformed HTML if either output is unsafe to embed.
if (/<\/style/i.test(css) || /<\/script/i.test(js)) {
  throw new Error('Unsafe closing tag in compiled output; fix before embedding.');
}
mkdirSync('dist', { recursive: true });
writeFileSync('dist/index.html', `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Page title</title>
  <link rel="icon" href="data:,">
  <style>${css}</style>
</head>
<body>
  <div id="root"></div>
  <script>${js}</script>
</body>
</html>`);
```

Set an appropriate title, then run:

```bash
node embed.mjs
```

This recipe embeds JavaScript and CSS, not arbitrary referenced files. Use inline SVG/data URLs for assets, system fonts or embedded fonts, and bundled data imports rather than runtime `fetch`. Check CSS URLs too. Deliver only `dist/index.html`; retain editable sources separately if useful.

## 4. Verify, then offer a preview

Follow the main skill's offline, interaction, and visual checks on `dist/index.html` opened directly from disk. Compilation alone is not verification. Ask before starting a local preview server unless serving was already requested. After approval, a simple command is:

```bash
python -m http.server 8000 --bind 127.0.0.1 --directory dist
```

If `python` is not on PATH, use uv to locate or download a Python interpreter:

```bash
uv run --no-project --python 3 python -m http.server 8000 --bind 127.0.0.1 --directory dist
```

`--no-project` avoids installing or synchronizing the host project's dependencies. uv may download Python if no suitable interpreter is available; no additional Python packages are needed for `http.server`. If uv is also unavailable, report that the preview cannot start and still deliver the standalone HTML.

Use the environment's service manager and networking instructions when required; adapt the bind address and port accordingly. Serve only `dist`, not the build directory or repository, and provide a URL the user can actually reach. This preview does not replace the offline check.
