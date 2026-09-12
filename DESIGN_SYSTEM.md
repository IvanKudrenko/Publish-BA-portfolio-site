# baproj.com implementation design system

This file implements the intent in `DESIGN.md`. When the two differ, `DESIGN.md` wins.

## Foundation

- Display type: `Helvetica Neue`, `Inter Tight`, system sans-serif; weight 200–300.
- Body/UI type: system sans-serif; weight 400–600.
- Background: `#ffffff`; text: `#111113`; secondary text: `#6e6e73`; quiet surface: `#f5f5f7`.
- BA blue: `--ba-blue: #1467d9`, used only for links, focus, and small accents.
- Content width: 1280px maximum with fluid gutters from 20px to 64px.
- Section rhythm: about 150px desktop and 80px mobile, varied for editorial pacing.

## Composition

- Whitespace separates sections. Hairlines are used only when they improve orientation.
- Headlines are short, thin, tightly set, and fluid with `clamp()`.
- Body copy stays readable at 17–20px and generally below 620px wide.
- Photography and existing project artwork carry color and personality.
- Images keep their natural proportions; prominent photos may break the text grid.

## Components

- Navigation: one shared header on every page. BA logo/name link home; Projects, Story, About, and Contact share one visual axis. Projects opens a restrained popover on desktop and an inline list on mobile.
- Hero: asymmetric text/photo composition, no card or decorative background. The tightly cropped Ivan/MacBook cutout stays secondary to the headline, with open space around the text and a visual anchor near the bottom of the first viewport.
- Homepage order: Hero → Story → Projects → BA → Contact. “View my work” deliberately skips Story and lands on Projects.
- Projects: a two-column desktop browsing grid and one-column phone layout. The original artwork is the visual; a title, short description, and at most one status follow it. The entire preview is a link.
- Story: asymmetric editorial rows with varied image scale and short, factual copy. About uses real photographs in alternating photo/text compositions, with captions instead of numbered timeline UI.
- Buttons: reserved for contact actions; text links are preferred elsewhere.
- Radius: 0 by default. Project artwork uses 14–17px; photographs/screenshots may use 10–14px; functional menus use 14px; buttons use 10px.
- Shadows: none on layout containers; project artwork may retain shadows already contained in the source image.
- Interaction: color and 1.015 image scale on hover/focus, with 220ms easing.

## Responsive behavior

- At 820px and below, hero, projects, and story become intentionally composed single-column layouts.
- Mobile gutters use 20px; the hero image can extend to the viewport edge.
- Project artwork is full width and never cropped.
- Navigation uses the existing accessible menu toggle below 760px.
- `prefers-reduced-motion` removes reveal and hover movement.
- Anchored sections use the real fixed-header height as scroll margin. Fresh pages without a hash begin at the top; direct hashes and browser back retain meaningful destinations.
- Light-page headers keep an opaque white surface so content never shows through the navigation while scrolling.

## Anti-patterns

- No decorative gradients, glass effects, glow, floating islands, card nesting, tag clouds, large pill navigation, repeated CTA rows, invented quotations, or identical feature-card grids.
- Project colors remain solid identity accents. Legacy gradient buttons, pill metadata, large shadows, and older floating navigation treatments are restyled into the shared system.
