# BA Blog publishing system

The public Blog is a static part of baproj and remains fast on GitHub Pages. BA Writer is a separate private application that runs only on Ivan's Mac at `127.0.0.1`. No admin API, Git credential, draft, or editor bundle is shipped to visitors.

## How Ivan publishes a Post

1. Double-click **BA Writer.app** in the repository.
2. Click **New Post** and write in “What’s on your mind?”
3. Add photos, an Original Thought, or a link if wanted.
4. Preview if wanted.
5. Click **Publish**.

BA Writer saves automatically. Title, slug, excerpt, date, reading time, canonical URL, and metadata are automatic for Posts. **More** contains optional overrides.

## Post vs Article

- **Post** is the default quick composer. It supports any length of text, an exact Original Thought, a link, and multiple locally uploaded photos. A title is optional.
- **Article** is an ordered block document with title, subtitle, cover, paragraphs, H2/H3 headings, quotes, Original Thought, images, galleries, code, callouts, dividers, embeds, columns, spacers, and an advanced sanitized HTML block. Blocks can be reordered by drag, mouse buttons, or keyboard-accessible Move controls. Typing `/` in an empty text block opens the block menu.

Both formats appear together at `/blog/`, use permanent `/blog/<slug>/` URLs, and can be filtered by All, Posts, or Articles.

## Drafts and content storage

Portable JSON is the canonical format. Version 2 records contain `id`, `type`, `title`, `subtitle`, `slug`, `description`, `text`, `originalThought`, `blocks`, `imageIds`, `media`, `coverMediaId`, `publishedAt`, `updatedAt`, `createdAt`, `tags`, `seo`, `layout`, and `redirects`.

- Private drafts and draft media: `.blog-private/posts/` and `.blog-private/media/`. The entire directory is ignored by Git and blocked by the local server.
- Published source: `content/posts/<id>.json`.
- Published media: `blog/assets/<id>/`.
- Generated output: `blog/<slug>/index.html`, `blog/index.html`, `blog/feed.xml`, `sitemap.xml`, and the homepage Blog section.

Old version 1 records are migrated when read. The renderer is deterministic and raw content is escaped by default. `originalThought` is stored as a literal string and rendered with preserved whitespace; the system never rewrites, corrects, translates, or normalizes it.

Autosave writes to disk after a short pause. Closing the browser, restarting BA Writer, or restarting the Mac does not remove drafts. Drafts never enter public source, HTML, homepage listings, RSS, sitemap, or structured data.

## Photos

Add images from Finder, drag them into the composer, paste a screenshot with Command-V, or select several files. Draft originals stay private. Publishing uses macOS `sips` to create JPEG variants up to 640, 1200, and 2000 pixels wide, includes responsive `srcset`, and commits only the generated web assets. GIF and WebP files are preserved. Supported inputs are JPEG, PNG, WebP, GIF, HEIC, and HEIF. Alt text is required for every used image before Publish; captions are optional.

Posts use a restrained multi-photo layout. Article image blocks support Normal, Wide, and Full width. Gallery blocks support several images.

## What Publish does

Publish runs one guarded operation:

1. Saves and validates the record, links, blocks, images, and required alt text.
2. Processes responsive images.
3. Writes the published JSON source.
4. Generates the Blog feed, item page, homepage preview, RSS, sitemap, metadata, JSON-LD, and old-slug redirects.
5. Stages only the files produced for this Blog operation. It never runs `git add .`.
6. Creates `Publish blog post: <title>` or `Publish blog article: <title>`.
7. Pushes the current configured branch to `origin`.
8. Polls the real public URL until its content fingerprint is present, then reports **Live** and shows a link.

Unrelated repository changes are reported and left untouched. If a shared generated file already has unrelated uncommitted edits, publishing stops before changing files. This prevents a Blog operation from absorbing homepage or feed work. The initial system upgrade must therefore be committed once before ordinary one-click publishing.

If Git push fails, the writing and generated files remain local and the error is shown. BA Writer never claims content is live merely because Git accepted a push.

## Unpublish, edits, slugs, and history

Editing a published item creates a private saved draft while the current public version remains unchanged. **Publish update** preserves `publishedAt` and sets `updatedAt`. If a published slug changes, BA Writer stores the old slug and generates a canonical redirect page so existing links continue to resolve.

Unpublish removes the item from public pages, homepage, RSS, sitemap, and its canonical page while preserving it privately as a draft. Delete is available only for drafts and requires confirmation.

The Settings panel shows concise Git revision history for each published source file. Recovery is also possible with normal Git history, for example:

```sh
git log -- content/posts/<id>.json
git show <commit>:content/posts/<id>.json
```

## SEO and public output

Published items receive semantic server-rendered HTML, unique titles and descriptions, canonical URLs, Open Graph and Twitter metadata, publication and update timestamps, responsive image metadata, and Article/BlogPosting JSON-LD. `/blog/feed.xml` is the RSS feed and `/sitemap.xml` lists only published writing. `robots.txt` advertises the sitemap. Articles with at least three headings receive a small table of contents.

No public Blog page uses `noindex`. The local Writer page uses `noindex` and is served only by the localhost process. There is intentionally no public `/blog/write` admin route.

## Opening BA Writer and fallback commands

The macOS launcher is `BA Writer.app`. It finds the repository relative to itself, creates a private password if needed, starts the localhost server with Git publishing enabled, opens the browser, and restores saved drafts. The first screen presents **New Post** and **New Article** directly.

Because this repository lives in macOS's Desktop-protected folder, the launcher starts Python through a hidden Terminal command. Terminal does not need to be open beforehand. This preserves the `127.0.0.1`-only model while using Terminal's existing Desktop-folder permission. Startup errors include the actual log output and are also written to `.blog-private/writer.log`.

Terminal fallback:

```sh
# Real publishing
python3 tools/blog.py serve --push

# Safe local dry run: Publish generates output but does not commit or push
python3 tools/blog.py serve

# Rebuild existing published source
python3 tools/blog.py build

# Validate published records
python3 tools/blog.py check
```

Then open `http://127.0.0.1:8787/writer/`. The password is printed in the terminal and persisted with mode `0600` at `.blog-private/writer-secret`. `BA_BLOG_PASSWORD` can override it locally; never commit that value. `--port` changes the port.

## One-time deployment setup

The repository remote is `origin`, the current production branch is `main`, and `CNAME` points to `baproj.com`. Confirm GitHub Pages is configured to deploy the root of `main`, then authenticate Git on this Mac. GitHub CLI authentication was expired during this upgrade, so repository Pages settings could not be queried automatically. HTTPS push may use macOS Keychain independently of `gh`; otherwise run `gh auth login -h github.com` or change the remote to SSH.

Commit the Blog system upgrade before the first real Publish. No Blog content was published as part of this upgrade.

## Verification

```sh
PYTHONPYCACHEPREFIX=/tmp/ba-blog-pycache python3 tools/test_blog.py
node --check tools/writer/editor.js
node --check blog/public.js
python3 tools/blog.py check
```
