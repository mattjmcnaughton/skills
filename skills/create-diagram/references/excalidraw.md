# Excalidraw authoring reference

Deep authoring detail for hand-writing `.excalidraw` JSON: file wrapper, element schema, copy-paste templates, and a build strategy for large diagrams.

Adapted in part from [coleam00/excalidraw-diagram-skill](https://github.com/coleam00/excalidraw-diagram-skill) (MIT). Color and brand opinions have been stripped — pick concrete hex values per diagram.

## File wrapper

A valid `.excalidraw` file is a single JSON object:

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "https://excalidraw.com",
  "elements": [],
  "appState": {
    "viewBackgroundColor": "#ffffff",
    "gridSize": 20
  },
  "files": {}
}
```

- `elements` is the list you populate with shapes, text, arrows, lines.
- `appState.viewBackgroundColor` is the canvas color. Use `#ffffff` for light, `#1e1e1e` for dark.
- `files` is for embedded images. Leave empty unless you need them.

## Element types

| Type | Use for |
|---|---|
| `rectangle` | Processes, actions, components |
| `ellipse` | Entry/exit points, abstract states, marker dots |
| `diamond` | Decisions, conditionals |
| `arrow` | Directed connections between shapes |
| `line` | Non-directional structure (tree trunks, timelines, dividers) |
| `text` | Labels, titles, descriptions |
| `frame` | Grouping containers (rarely needed) |

## Common properties

Every element has these:

| Property | Type | Notes |
|---|---|---|
| `id` | string | Unique within the file. Descriptive strings (`"trigger_rect"`) beat numeric IDs for readability. |
| `type` | string | One of the element types above. |
| `x`, `y` | number | Top-left position in pixels. |
| `width`, `height` | number | Size in pixels. |
| `strokeColor` | string | Border color (hex). |
| `backgroundColor` | string | Fill color (hex or `"transparent"`). |
| `fillStyle` | string | `"solid"`, `"hachure"`, or `"cross-hatch"`. |
| `strokeWidth` | number | `1` thin, `2` standard, `3` emphasis. |
| `strokeStyle` | string | `"solid"`, `"dashed"`, or `"dotted"`. |
| `roughness` | number | `0` clean, `1` default sketchy, `2` rough. Use `0` for modern. |
| `opacity` | number | `0`-`100`. Always `100`; use color/size/stroke for hierarchy. |
| `angle` | number | Rotation in radians. `0` unless intentional. |
| `seed` | number | Random seed for hand-drawn look. Namespace by section. |
| `version`, `versionNonce` | number | Excalidraw internals. Any integers work. |
| `isDeleted` | boolean | `false`. |
| `groupIds` | array | `[]` unless grouping. |
| `boundElements` | array or null | Elements bound to this one (text in a shape, arrows attached). |
| `locked` | boolean | `false`. |

Text-specific: `text`, `originalText` (same string), `fontSize`, `fontFamily` (3 = sans), `textAlign`, `verticalAlign`, `lineHeight` (1.25), `containerId` (parent shape ID or null).

Arrow-specific: `points` (array of `[x, y]` pairs relative to the arrow's `x`/`y`), `startBinding`/`endBinding` (`{elementId, focus, gap}`), `startArrowhead`/`endArrowhead` (`null` or `"arrow"`).

Line-specific: same `points` structure as arrow; no bindings or arrowheads.

## Element templates

Replace placeholder hex colors with the palette you want for the diagram.

### Free-floating text (no container)

```json
{
  "type": "text",
  "id": "label1",
  "x": 100, "y": 100,
  "width": 200, "height": 25,
  "text": "Section title",
  "originalText": "Section title",
  "fontSize": 20,
  "fontFamily": 3,
  "textAlign": "left",
  "verticalAlign": "top",
  "strokeColor": "#1e1e1e",
  "backgroundColor": "transparent",
  "fillStyle": "solid",
  "strokeWidth": 1,
  "strokeStyle": "solid",
  "roughness": 0,
  "opacity": 100,
  "angle": 0,
  "seed": 11111,
  "version": 1,
  "versionNonce": 22222,
  "isDeleted": false,
  "groupIds": [],
  "boundElements": null,
  "link": null,
  "locked": false,
  "containerId": null,
  "lineHeight": 1.25
}
```

### Line (structural, not directional)

```json
{
  "type": "line",
  "id": "spine1",
  "x": 100, "y": 100,
  "width": 0, "height": 200,
  "strokeColor": "#1e1e1e",
  "backgroundColor": "transparent",
  "fillStyle": "solid",
  "strokeWidth": 2,
  "strokeStyle": "solid",
  "roughness": 0,
  "opacity": 100,
  "angle": 0,
  "seed": 44444,
  "version": 1,
  "versionNonce": 55555,
  "isDeleted": false,
  "groupIds": [],
  "boundElements": null,
  "link": null,
  "locked": false,
  "points": [[0, 0], [0, 200]]
}
```

### Small marker dot (timeline/bullet)

```json
{
  "type": "ellipse",
  "id": "dot1",
  "x": 94, "y": 94,
  "width": 12, "height": 12,
  "strokeColor": "#1e1e1e",
  "backgroundColor": "#1e1e1e",
  "fillStyle": "solid",
  "strokeWidth": 1,
  "strokeStyle": "solid",
  "roughness": 0,
  "opacity": 100,
  "angle": 0,
  "seed": 66666,
  "version": 1,
  "versionNonce": 77777,
  "isDeleted": false,
  "groupIds": [],
  "boundElements": null,
  "link": null,
  "locked": false
}
```

### Rectangle with bound text

```json
{
  "type": "rectangle",
  "id": "proc1",
  "x": 100, "y": 100,
  "width": 180, "height": 90,
  "strokeColor": "#1971c2",
  "backgroundColor": "#a5d8ff",
  "fillStyle": "solid",
  "strokeWidth": 2,
  "strokeStyle": "solid",
  "roughness": 0,
  "opacity": 100,
  "angle": 0,
  "seed": 12345,
  "version": 1,
  "versionNonce": 67890,
  "isDeleted": false,
  "groupIds": [],
  "boundElements": [{"id": "proc1_text", "type": "text"}],
  "link": null,
  "locked": false,
  "roundness": {"type": 3}
}
```

```json
{
  "type": "text",
  "id": "proc1_text",
  "x": 130, "y": 132,
  "width": 120, "height": 25,
  "text": "Process",
  "originalText": "Process",
  "fontSize": 16,
  "fontFamily": 3,
  "textAlign": "center",
  "verticalAlign": "middle",
  "strokeColor": "#1971c2",
  "backgroundColor": "transparent",
  "fillStyle": "solid",
  "strokeWidth": 1,
  "strokeStyle": "solid",
  "roughness": 0,
  "opacity": 100,
  "angle": 0,
  "seed": 11112,
  "version": 1,
  "versionNonce": 22223,
  "isDeleted": false,
  "groupIds": [],
  "boundElements": null,
  "link": null,
  "locked": false,
  "containerId": "proc1",
  "lineHeight": 1.25
}
```

### Arrow with bindings

```json
{
  "type": "arrow",
  "id": "arrow1",
  "x": 282, "y": 145,
  "width": 118, "height": 0,
  "strokeColor": "#1971c2",
  "backgroundColor": "transparent",
  "fillStyle": "solid",
  "strokeWidth": 2,
  "strokeStyle": "solid",
  "roughness": 0,
  "opacity": 100,
  "angle": 0,
  "seed": 33333,
  "version": 1,
  "versionNonce": 44444,
  "isDeleted": false,
  "groupIds": [],
  "boundElements": null,
  "link": null,
  "locked": false,
  "points": [[0, 0], [118, 0]],
  "startBinding": {"elementId": "proc1", "focus": 0, "gap": 2},
  "endBinding": {"elementId": "proc2", "focus": 0, "gap": 2},
  "startArrowhead": null,
  "endArrowhead": "arrow"
}
```

For curved arrows, add intermediate `[x, y]` waypoints to `points` — `[[0,0], [60,0], [60,40], [118,40]]` produces a step routing around an obstacle.

## Section-by-section build strategy

Comprehensive diagrams easily exceed a single response's token budget. Even when they fit, building one section at a time produces tighter results. Use this workflow for diagrams beyond ~10 elements.

1. **Start with the file wrapper** — write `type`, `version`, `appState`, `files`, and an empty `elements` array. Save and render to confirm the empty canvas is valid.
2. **Add one section per pass.** A section is a visual grouping: an entry point, a decision branch, a phase, an output. Use descriptive IDs (`"trigger_rect"`, `"fanout_arrow_left"`) so cross-section references read clearly.
3. **Namespace `seed` ranges by section** — section 1 uses `1xxxxx`, section 2 uses `2xxxxx`, and so on. Collisions don't break anything but make the file hard to reason about.
4. **Update cross-section bindings as you go.** When a new section's arrow needs to bind to an element from an earlier section, edit the earlier element's `boundElements` array in the same pass.
5. **Render and Read the SVG after each section.** Catch overlaps, clipping, and bad spacing early, when the fix is local.
6. **Review the whole file before declaring done.** Walk through every `boundElements`, `containerId`, `startBinding`, and `endBinding`. Confirm each referenced ID exists. Look for sections that are cramped while others have whitespace.

## What to avoid

- **Generating the entire diagram in one response** for anything non-trivial. You will truncate.
- **Python or shell generators** that compute coordinates. The indirection makes debugging harder than hand-edited JSON with descriptive IDs.
- **Numeric IDs** (`"1"`, `"2"`). Use descriptive strings; future-you reads them dozens of times.
- **Inventing colors per element.** Pick a palette of 3-6 hex values at the start of the diagram and stick to it.
- **Opacity for hierarchy.** Use color, size, and stroke width instead. `opacity: 100` everywhere.
