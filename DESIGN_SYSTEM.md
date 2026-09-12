# baproj.com implementation design system

This file implements the intent in `DESIGN.md`. When the two differ, `DESIGN.md` wins.

# Geometry & Precision Rules

These rules are mandatory across the entire website. They are not suggestions. Do not knowingly introduce components that violate them.

## Spacing grid and proximity

- Use 4px for micro adjustments and 8px as the primary spacing rhythm.
- Preferred spacing scale: 4, 8, 12, 16, 24, 32, 48, 64, 96, and 128px.
- Avoid arbitrary spacing such as 13, 19, 27, or 37px unless a small optical correction has a clear reason.
- Use 8–16px for strongly related elements, 24–32px within one composition, 48–64px between groups, and 96–144px between major desktop sections.
- Related elements must be visibly closer than unrelated elements. Do not use one identical gap everywhere.

## Containers, borders, and shadows

- Resolve grouping in this order: whitespace → alignment → hairline → background → shadow.
- A box must justify its existence. Never add a container merely to make a section appear designed.
- Default to no border. When separation is necessary, use one restrained neutral 1px hairline near `rgba(0, 0, 0, 0.08–0.12)`.
- Default to no shadow. Reserve shadows for objects that genuinely float over another layer, such as dropdowns, popovers, and modals.
- Do not combine border, background, shadow, and rounding on an ordinary content block without a functional reason.

## Radius geometry

- Rounded corners are an implementation detail, not BA's identity.
- Large page and editorial text sections use 0px radius.
- Standalone editorial photos use approximately 6–10px when rounding improves the image.
- Dropdowns and popovers use approximately 8–12px. Buttons use approximately 6–10px.
- Product artwork keeps its own geometry. Do not wrap it in another decorative rounded card.
- Avoid large 20px+ radii and pill-shaped content blocks unless their semantics require them.
- When one rounded object sits inside another with a visible gap, the inner radius must be smaller: `inner radius ≈ outer radius - gap`. If the result approaches zero, use a square or nearly square inner edge.
- Before nesting rounded surfaces, remove the outer container when an image and nearby caption communicate the relationship on their own.

## Keylines and optical alignment

- Give every composition deliberate shared keylines: image and caption, artwork and project name, related headings, grid columns, navigation baseline, text columns, and image/text pairings.
- Small 1–3px optical corrections may override mathematical centering for icons, logos, arrows, and uneven visual weight. Optical correction must never justify random positioning.

## Hierarchy and text width

- Aim for one primary focal point and at most one strong supporting focal point within a viewport.
- Do not add competing badges, slogans, decorative effects, or oversized calls to action around an established focal point.
- Keep body text near 45–66 characters per line, usually with `max-width` between 55ch and 64ch. Short support copy may be narrower.

## Pills and chips

- Use pills or chips only for filters, selected options, compact toggles, or meaningful status.
- Ordinary features, keywords, and product characteristics use plain text, inline separators, or a simple list.
- Form must match meaning; never build decorative metadata clouds.

## Photography and captions

- Use only three main treatments: standalone editorial photograph, background-removed cutout, or product artwork.
- Editorial photographs use natural dimensions, no outer card, no decorative border, no shadow, and at most a restrained 6–10px radius.
- Cutouts use no artificial frame, rounded container, glow, or shadow halo. Use edge cleanup only when integration requires it.
- Product artwork keeps its own geometry and receives no redundant decorative wrapper.
- Captions align to the image keyline, sit approximately 8–12px below it, use small secondary type, and never occupy a separate card.
- On narrow screens, preserve intrinsic image proportions and important details. Use `display: block`, `max-width: 100%`, `height: auto`, and `min-width: 0` on shrinking grid or flex children. Use `object-fit: cover` only for intentional, safe crops.

## Usability

- Minimal appearance must retain useful navigation and information.
- Simplify presentation instead of removing useful functionality.
- Interactive controls should keep practical touch targets near 44px where appropriate.

## Anti-AI and copy authenticity

- Every decorative choice must solve a specific problem. Do not add a gradient, shadow, border, rounded container, chip, badge, icon tile, glow, panel, or floating element merely to make a section look designed.
- Reject generic startup, SaaS, agency, and vibe-coded portfolio patterns. Avoid repeated card grids, equal icon tiles, fake manifestos, dark gradient slogan cards, decorative blue/purple gradients, repeated eyebrow/heading/paragraph formulas, pill clouds, unjustified bento layouts, glass effects, floating islands, generic inspirational quotes, and over-polished AI copy.
- Ground sections in Ivan's real photography, products, artifacts, typography, BA identity, and authentic content.
- Story headlines must explain why a moment matters, what changed, or how it connects to the next stage. Never use a Story headline merely to describe what the photograph already shows.
- Never invent a quote, slogan, philosophy, personal statement, or manifesto for Ivan. AI may translate, simplify, correct, or shorten Ivan's words without changing their meaning.
- Approved authentic statements are “I build things.” and “I have more ideas than I build.” Additional slogans require Ivan's explicit approval.

## Foundation

- Display type: `Helvetica Neue`, `Inter Tight`, system sans-serif; weight 200–300.
- Body/UI type: system sans-serif; weight 400–600.
- Background: `#ffffff`; text: `#111113`; secondary text: `#6e6e73`; quiet surface: `#f5f5f7`.
- BA blue: `--ba-blue: #1467d9`, used only for links, focus, and small accents.
- Content width: 1280px maximum with fluid gutters from 20px to 64px.
- Section rhythm: 96–128px desktop and 64–80px mobile, varied for editorial pacing.

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
- Radius: 0 by default. Project artwork keeps its own geometry; photographs/screenshots use 6–10px when needed; functional menus use 8–12px; buttons use 6–10px.
- Shadows: none on layout containers; project artwork may retain shadows already contained in the source image.
- Interaction: color and 1.015 image scale on hover/focus, with 220ms easing.

## Responsive behavior

- At 820px and below, hero, projects, and story become intentionally composed single-column layouts.
- Mobile gutters use 20px; the hero image can extend to the viewport edge.
- Project artwork is full width and never cropped.
- Navigation uses the existing accessible menu toggle at 820px and below.
- `prefers-reduced-motion` removes reveal and hover movement.
- Anchored sections use the real fixed-header height as scroll margin. Fresh pages without a hash begin at the top; direct hashes and browser back retain meaningful destinations.
- Light-page headers keep an opaque white surface so content never shows through the navigation while scrolling.

## Anti-patterns

- No decorative gradients, glass effects, glow, floating islands, card nesting, tag clouds, large pill navigation, repeated CTA rows, invented quotations, or identical feature-card grids.
- Project colors remain solid identity accents. Legacy gradient buttons, pill metadata, large shadows, and older floating navigation treatments are restyled into the shared system.
