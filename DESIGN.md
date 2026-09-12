# baproj.com — Design Direction

This file is the design source of truth for **baproj.com**.

Codex should read this document before making significant visual, layout, typography, animation, or homepage changes. The goal is **not** to rebuild the site from scratch. Preserve the existing information architecture, real project content, functionality, links, and BA identity while making the presentation more personal, minimal, intentional, and less AI-generated.

---

## 1. Core idea

The site should feel like a **personal inventor / product builder portfolio** with a restrained visual language inspired by **Apple web design from roughly the late 2000s through the mid-2010s**.

This is inspiration, not imitation.

The qualities to preserve are:

- very large, thin, confident headlines;
- generous whitespace;
- simple composition;
- strong typography;
- real photography and real project imagery;
- precise alignment;
- occasional controlled asymmetry;
- minimal decorative UI;
- subtle, deliberate motion;
- content taking priority over containers.

The simplest rule is:

> **Photos and typography are the visual system.**

The website should communicate:

> Here is Ivan. Here is what he builds. Here is how that developed over time.

It should not feel like a generic SaaS landing page, AI portfolio template, or collection of fashionable UI components.

---

## 2. Keep BA identity

Minimalism must **not erase individuality**.

Keep and respect:

- the **BA logo**;
- BA branding;
- Ivan's personality;
- the actual history of the project;
- the real projects and prototypes;
- the site's existing purpose as a personal site / calling card.

Do **not** remove the logo simply to make the page more minimal.

Do **not** turn the site into an Apple clone. Apple is a reference for restraint, hierarchy, typography, whitespace, and presentation — not the brand of this site.

When choosing between "more minimal" and "more personal", preserve the personal element.

---

## 3. Avoid common AI-site patterns

Actively inspect the current site for patterns that make it feel AI-generated or vibe-coded.

Reduce or remove when they do not serve the content:

- excessive cards and rounded rectangles;
- floating islands;
- glassmorphism;
- decorative gradients;
- generic bento grids;
- pill/chip overuse;
- decorative blobs;
- strong or unnecessary drop shadows;
- repeated "eyebrow + heading + paragraph" formulas;
- identical layouts for every section;
- identical project-card templates;
- every section having equal visual weight;
- unnecessary section wrappers;
- generic marketing copy;
- decorative UI with no informational purpose;
- excessive motion;
- effects added simply because they are fashionable.

Do not replace the current AI-looking style with a different trendy AI-looking style.

Not every idea needs a container.

---

## 4. Typography

Typography is one of the main signatures of the redesign.

### Large headlines

Use:

- very large sizes;
- thin/light weights;
- compact line-height;
- short phrases;
- careful letter spacing;
- large areas of negative space.

The desired feeling is close to early/mid-2010s Apple editorial and product pages.

A useful starting direction:

```css
font-family:
  -apple-system,
  BlinkMacSystemFont,
  "Helvetica Neue",
  Arial,
  sans-serif;

font-weight: 200-300;
line-height: 0.95-1.05;
```

Do not blindly copy these values everywhere. Tune them visually and responsively.

### Body copy

Body text should **not** be ultra-thin.

Use:

- regular readable weight;
- comfortable line-height;
- short paragraphs;
- restrained width;
- direct language.

The contrast between **large thin headlines** and **normal readable body text** is important.

---

## 5. Color and surfaces

Default direction:

- white or near-white background;
- near-black primary text;
- restrained neutral gray secondary text;
- color primarily introduced by photography, project imagery, and selected BA brand accents.

Avoid gradients unless there is a specific content-driven reason for one.

Avoid turning sections into floating cards merely to separate them. Use whitespace, typography, scale, alignment, and subtle rules/dividers first.

---

## 6. Hero — approved direction

The hero should be **minimal, product-oriented, and personal**.

### Main composition

Desktop direction:

- large thin headline on the left;
- Ivan working behind the MacBook on the right;
- substantial whitespace;
- controlled asymmetry;
- photo visually anchored toward the lower part of the viewport;
- the image may extend slightly beyond the normal content grid or viewport edge if it improves the composition.

The hero must **not** become a generic:

> text + two CTA buttons + image card

Do not put the main photo inside a rounded floating card.

Do not add a decorative hero gradient, glow, blob, or glass panel.

### Current preferred hero copy direction

Preferred headline:

> **I build things.**

Supporting copy can remain extremely short, for example:

> Software, devices, and experiments.

A small text link such as:

> View my work ↓

is preferable to a row of large generic CTA buttons.

The exact final copy may evolve, but preserve the minimal tone.

### Important photo rule

The MacBook should support the message that Ivan is a builder. It should **not** become the subject of the page.

The page is about Ivan and his work, not about Apple products.

---

## 7. Navigation

Navigation should be visually quiet.

Prefer a simple navigation integrated into the page rather than a floating rounded navigation island.

Keep the BA logo visible and intentional.

Possible structure:

- BA logo / identity on the left;
- a small number of clear links on the right.

Avoid excessive navigation effects.

---

## 8. Photography and personal history

A major part of the new identity should come from **real photos of Ivan across different ages and stages of his life**.

All candidate photos will be placed in:

> **`media for baproj/`**

Codex should **inspect the actual files in this folder before choosing or placing images**.

Do not assume every image must be used.

Select images according to:

- visual quality;
- relevance to the story;
- composition;
- age/stage represented;
- whether the image supports a specific section;
- whether the cutout quality is good enough;
- whether another image communicates the same idea better.

### Desired photo roles

Use photography to show:

- early curiosity about phones and technology;
- making and experimenting at a young age;
- presenting or explaining ideas;
- later product thinking;
- current work;
- real interaction with devices and prototypes.

The timeline/story should feel like a real personal history, not a résumé infographic.

### Background-removed photos

Background-removed images can be used as clean editorial elements, but avoid scattering cutout people everywhere.

A few carefully placed cutouts are stronger than many floating ones.

Inspect edges for:

- halos;
- rough masks;
- color spill;
- awkward crops.

If a cutout is not clean enough for a prominent placement, either use it smaller, use another version, or retain a natural photo background if appropriate.

### Photography principle

Use photos because they reveal something real about Ivan — not merely as decoration.

---

## 9. Story / timeline

The personal history is an important differentiator.

Avoid a generic sequence of six identical numbered cards.

Instead, create a more editorial story using a mix of:

- age or year;
- very short text;
- real photos;
- actual artifacts;
- different visual scale depending on importance.

The rhythm does not have to be perfectly uniform.

Some moments may deserve a large image. Others may need only a date and one line.

The page should feel curated rather than generated from a component template.

---

## 10. Projects

Projects should remain central, but they should **not all be forced into one identical card template**.

The presentation can adapt to the nature of each project while still belonging to the same design system.

Examples:

- **BlinkClip** — interface / software-first presentation;
- **ActiView** — prototype / object-first presentation;
- **BA** — identity / history / concept-first presentation;
- **Shadow Box** — visual or experimental presentation;
- other work — use the medium that best communicates the project.

Use real screenshots, real prototypes, sketches, photos, and artifacts whenever possible.

The project itself should determine the composition.

---

## 11. Interactivity and motion

The site is a personal calling card, so it should feel alive, but interaction must remain restrained.

Good interaction examples:

- subtle fade/translate entrances;
- smooth section navigation;
- gentle image reveals;
- timeline details appearing on hover/tap when useful;
- simple lightbox/detail viewing for real artifacts;
- subtle project transitions.

Avoid:

- constant floating motion;
- cursor-follow effects for decoration;
- exaggerated parallax;
- bounce/overshoot everywhere;
- large animated gradients;
- motion that competes with reading;
- animation added simply to make the site feel "premium".

Motion should clarify or reward interaction, not advertise itself.

Respect `prefers-reduced-motion`.

---

## 12. Responsive behavior

Do not simply collapse desktop components into a vertical stack.

Design mobile compositions intentionally.

For the hero:

- headline first;
- short supporting copy;
- large Ivan/MacBook image afterward;
- allow the image to use generous width and, if composition benefits, extend slightly beyond the viewport;
- preserve the strong typography.

Maintain whitespace and hierarchy on smaller screens rather than shrinking everything until it fits.

---

## 13. Writing tone

Avoid generic portfolio and AI-generated marketing language such as:

- "at the intersection of...";
- "crafting meaningful experiences...";
- "passionate about innovation...";
- "where creativity meets technology...";
- long explanations of why every section exists.

Prefer simple, specific statements.

Show evidence through the work and photography instead of repeatedly telling the visitor what kind of creator Ivan is.

---

## 14. Designer skills — required workflow

Before making a major visual redesign, Codex should **inspect and use the relevant installed design/UI skills** rather than relying only on a general coding pass.

In particular, if available, use tools/skills such as:

- **Impeccable** for visual critique, distillation, anti-AI-pattern review, and polish;
- a **frontend-design** skill for intentional visual direction;
- **web-design-guidelines / interface guidelines** for final UX, accessibility, typography, interaction, and responsive QA.

If equivalent or better design skills are installed later, inspect them and use the relevant ones.

Recommended workflow:

1. Read this `DESIGN.md`.
2. Inspect the current site and existing implementation.
3. Inspect `media for baproj/`.
4. Run a design critique using the appropriate designer skill(s).
5. Identify AI-looking patterns in the current page.
6. Propose the intended layout changes before performing a large redesign.
7. Implement without unnecessarily changing site structure or functionality.
8. Use a design/polish skill after implementation.
9. Perform responsive and accessibility QA.
10. Check again that the result has not reintroduced generic cards, islands, gradients, or template-like patterns.

Do not let a skill override this document's core direction. Skills are tools for execution and critique; **this document defines the design intent**.

---

## 15. Decision rule

When uncertain, ask:

> Does this make the site feel more like Ivan's actual work and story, or more like a reusable portfolio template?

Choose the first.

And when choosing between extra decoration and restraint:

> Prefer restraint.

When choosing between sterile minimalism and meaningful individuality:

> Preserve individuality.
