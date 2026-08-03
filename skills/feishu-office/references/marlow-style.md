# MarlowStyle

MarlowStyle is a restrained visual profile for clear process diagrams.
Color is semantic: use each accent only for its assigned role.

## Composition

- Direction: arrange the main flow left to right on one horizontal baseline.
- Grouping lane: enclose the active process in one lavender-gray lane with
  `64 px` inner padding and a `16 px` corner radius.
- Node targets: use `320 x 128 px` as the target size for process nodes and
  `320 x 160 px` for an actor, trigger, passive note, or data-store. These are
  target sizes, not hard limits.
- Long text: widen or increase the node height and wrap the text. Never shrink
  the type or truncate content.
- Spacing: keep at least `48 px` between nodes, `32 px` between a node and its
  label, and `80 px` of open canvas around separate roles.
- Phase chips: for a single-step phase, size the chip to its content beneath the
  step; for a multi-step phase, let it span the related adjacent nodes. Keep
  `16 px` horizontal padding and an `8 px` corner radius.

## Palette

- Canvas: white `#FFFFFF` with generous whitespace.
- Grouping lanes: lavender-gray `#ECEEF6` with quiet separation.
- Normal nodes: white `#FFFFFF` with compact, readable labels.
- Borders: thin graphite `#2B2B2B`.
- Connectors: graphite `#2B2B2B`.
- Focal node: use exactly one pale-pink `#FBE3E5` step.
- Actor or trigger: muted terracotta `#C8564E` with white `#FFFFFF` text.
- Passive note or data-store: lavender `#ECEEF6` with graphite `#2B2B2B` text.
- Phase chips: pale pink `#F7D9DC` with maroon `#9A2B2B` text.
- Title highlight: restrained yellow `#F4E04D`.

## Type and Geometry

- Typeface: use the board's default sans-serif throughout; do not select or
  embed an additional font.
- Title: `40 px`, weight `700`; node label: `28 px`, weight `500`.
- Actor label: `30 px`, weight `700`; supporting text and connector labels:
  `18 px`, weight `400`; phase-chip text: `16 px`, weight `500`.
- Shape: use flat native rectangles with `12 px` corner radii; reserve the
  larger lane and chip radii defined above.
- Border: use a `2 px` graphite stroke on nodes and role boxes.

## Flow

- Main flow: solid `3 px` graphite connectors with direct arrowheads.
- Side flow: dashed `3 px` graphite connectors with a `10 px` dash and `8 px` gap rhythm.
- Route connectors straight or at right angles and keep labels clear of lines.
- Use no decorative gradients, shadows, textures, glows, or ornamental shapes.
