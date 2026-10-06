#!/usr/bin/env python3
"""BA Writer: localhost authoring server and deterministic static blog builder."""
from __future__ import annotations

import argparse, datetime as dt, hashlib, html, http.server, json, mimetypes, os, re
import secrets, shutil, subprocess, threading, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / ".blog-private"
PRIVATE_POSTS, PRIVATE_MEDIA = PRIVATE / "posts", PRIVATE / "media"
POSTS, PUBLIC_ASSETS = ROOT / "content/posts", ROOT / "blog/assets"
SITE_URL = "https://baproj.com"
RESERVED = {"write", "index", "assets", "feed", "blog"}
IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif", "image/heic": ".heic", "image/heif": ".heif"}
BLOCK_TYPES = {"paragraph", "heading", "quote", "original-thought", "callout", "divider", "code", "image", "gallery", "embed", "columns", "spacer", "html"}
E = html.escape

def now(): return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
def parse_date(value):
    if not value: return dt.datetime.now(dt.timezone.utc)
    try: parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError: parsed = dt.datetime.combine(dt.date.fromisoformat(value), dt.time(), dt.timezone.utc)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=dt.timezone.utc)
def display_date(value): return parse_date(value).strftime("%B %d, %Y").replace(" 0", " ")
def slugify(value): return re.sub(r"^-|-$", "", re.sub(r"[^a-z0-9]+", "-", value.lower().encode("ascii", "ignore").decode()))[:96]
def strip_md(value):
    value = re.sub(r"!\[[^]]*\]\([^)]*\)", "", value)
    value = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", value)
    return re.sub(r"\s+", " ", re.sub(r"[*_`>#-]", "", value)).strip()

def inferred_title(record):
    if record.get("title", "").strip(): return record["title"].strip()
    first = strip_md(record.get("text", "")) or "Untitled post"
    return first if len(first) <= 72 else first[:71].rsplit(" ", 1)[0] + "…"

def excerpt(record, limit=180):
    if record.get("description", "").strip(): return record["description"].strip()
    source = record.get("text", "")
    if not source:
        block = next((b for b in record.get("blocks", []) if b.get("type") in {"paragraph", "quote", "callout"} and b.get("text")), {})
        source = block.get("text", "")
    source = strip_md(source)
    return source if len(source) <= limit else source[:limit - 1].rsplit(" ", 1)[0] + "…"

def safe_url(value, embed=False):
    value = value.strip()
    if value.startswith("/") and not value.startswith("//"): return value
    if not re.match(r"^https://", value, re.I): return "#"
    if embed and (urllib.parse.urlparse(value).hostname or "").lower() not in {"youtube.com", "www.youtube.com", "youtu.be", "vimeo.com", "player.vimeo.com"}: return "#"
    return value

def inline(value):
    tokens = []
    def hold(text): tokens.append(text); return f"\x00{len(tokens)-1}\x00"
    value = re.sub(r"`([^`]+)`", lambda m: hold("<code>" + E(m.group(1)) + "</code>"), value)
    value = E(value)
    value = re.sub(r"\[([^]]+)\]\(([^\s)]+)\)", lambda m: hold(f'<a href="{E(safe_url(html.unescape(m.group(2))), quote=True)}">{m.group(1)}</a>'), value)
    value = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", value)
    value = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", value)
    for index, text in enumerate(tokens): value = value.replace(f"\x00{index}\x00", text)
    return value

def markdown(value):
    lines, output, index = value.replace("\r\n", "\n").split("\n"), [], 0
    while index < len(lines):
        line = lines[index]
        if not line.strip(): index += 1; continue
        if line.startswith("```"):
            language, code = slugify(line[3:].strip()), []
            index += 1
            while index < len(lines) and not lines[index].startswith("```"): code.append(lines[index]); index += 1
            output.append(f'<pre><code{f" class=language-{language}" if language else ""}>{E(chr(10).join(code))}</code></pre>'); index += 1; continue
        heading = re.match(r"^(#{1,3})\s+(.+)", line)
        if heading:
            level = max(2, len(heading.group(1))); output.append(f"<h{level}>{inline(heading.group(2))}</h{level}>"); index += 1; continue
        if re.match(r"^\s*(---+|\*\*\*+)\s*$", line): output.append("<hr>"); index += 1; continue
        if line.startswith(">"):
            quote = []
            while index < len(lines) and lines[index].startswith(">"): quote.append(lines[index][1:].lstrip()); index += 1
            output.append("<blockquote>" + markdown("\n".join(quote)) + "</blockquote>"); continue
        item = re.match(r"^\s*(?:([-*])|\d+\.)\s+(.+)", line)
        if item:
            kind, items = ("ul" if item.group(1) else "ol"), []
            while index < len(lines):
                current = re.match(r"^\s*(?:([-*])|\d+\.)\s+(.+)", lines[index])
                if not current or ("ul" if current.group(1) else "ol") != kind: break
                items.append("<li>" + inline(current.group(2)) + "</li>"); index += 1
            output.append(f"<{kind}>" + "".join(items) + f"</{kind}>"); continue
        paragraph = [line]; index += 1
        while index < len(lines) and lines[index].strip() and not re.match(r"^(#{1,3}\s|>|```|[-*]\s|\d+\.\s|---)", lines[index]): paragraph.append(lines[index]); index += 1
        output.append("<p>" + inline("\n".join(paragraph)) + "</p>")
    return "\n".join(output)

def sanitize_html(value):
    value = re.sub(r"<(script|style|iframe|object|embed|form|input|button|link|meta)[^>]*>.*?</\1\s*>", "", value, flags=re.I | re.S)
    value = re.sub(r"<(script|style|iframe|object|embed|form|input|button|link|meta)\b[^>]*?/?>", "", value, flags=re.I | re.S)
    value = re.sub(r"\s(on\w+|style|srcdoc)\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s>]+)", "", value, flags=re.I)
    return re.sub(r"(href|src)\s*=\s*([\"'])\s*(?:javascript|data):.*?\2", r'\1="#"', value, flags=re.I | re.S)

def media_map(record): return {item.get("id", ""): item for item in record.get("media", [])}

def image_html(record, media_id, layout="normal", caption="", alt="", preview=False):
    item = media_map(record).get(media_id)
    if not item: return ""
    alt, caption = alt or item.get("alt", ""), caption or item.get("caption", "")
    layout = layout if layout in {"normal", "wide", "full"} else "normal"
    if preview:
        image = f'<img src="/api/media/{E(record["id"], quote=True)}/{E(item["storedName"], quote=True)}" alt="{E(alt, quote=True)}">'
    elif item.get("variants"):
        srcset = ", ".join(f'{E(v["path"], quote=True)} {v["width"]}w' for v in item["variants"])
        image = f'<img src="{E(item["variants"][-1]["path"], quote=True)}" srcset="{srcset}" sizes="(max-width: 820px) 100vw, 960px" width="{item.get("width", "")}" height="{item.get("height", "")}" alt="{E(alt, quote=True)}" loading="lazy" decoding="async">'
    else: image = f'<img src="{E(item.get("publicPath", "#"), quote=True)}" alt="{E(alt, quote=True)}" loading="lazy">'
    return f'<figure class="content-image image-{layout}">{image}{f"<figcaption>{E(caption)}</figcaption>" if caption else ""}</figure>'

def original(value): return f'<aside class="original-thought"><h2>Original thought</h2><div>{E(value)}</div></aside>' if value else ""

def block_html(record, block, preview=False):
    kind = block.get("type", "paragraph")
    if kind == "paragraph": return f'<div class="prose-block">{markdown(block.get("text", ""))}</div>'
    if kind == "heading":
        level, text = (3 if int(block.get("level", 2)) == 3 else 2), block.get("text", "")
        return f'<h{level} id="{E(slugify(text), quote=True)}">{inline(text)}</h{level}>'
    if kind == "quote":
        citation = f'<cite>{E(block.get("caption", ""))}</cite>' if block.get("caption") else ""
        return f'<blockquote class="article-quote"><p>{inline(block.get("text", ""))}</p>{citation}</blockquote>'
    if kind == "original-thought": return original(block.get("text", ""))
    if kind == "callout": return f'<aside class="article-callout"><p>{inline(block.get("text", ""))}</p></aside>'
    if kind == "divider": return "<hr>"
    if kind == "spacer": return '<div class="article-spacer" aria-hidden="true"></div>'
    if kind == "code": return f'<pre><code>{E(block.get("text", ""))}</code></pre>'
    if kind == "image": return image_html(record, block.get("mediaId", ""), block.get("layout", "normal"), block.get("caption", ""), block.get("alt", ""), preview)
    if kind == "gallery": return f'<div class="article-gallery" data-count="{len(block.get("mediaIds", []))}">' + "".join(image_html(record, item, preview=preview) for item in block.get("mediaIds", [])) + "</div>"
    if kind == "embed":
        url = safe_url(block.get("url", ""), embed=True)
        if url == "#": return f'<p><a href="{E(safe_url(block.get("url", "")), quote=True)}">{E(block.get("url", ""))}</a></p>'
        parsed = urllib.parse.urlparse(url)
        if "youtu" in (parsed.hostname or ""):
            video = parsed.path.strip("/").split("/")[-1] if "youtu.be" in (parsed.hostname or "") else urllib.parse.parse_qs(parsed.query).get("v", [""])[0]
            url = f"https://www.youtube-nocookie.com/embed/{slugify(video)}"
        return f'<div class="article-embed"><iframe src="{E(url, quote=True)}" title="{E(block.get("title", "Embedded media"), quote=True)}" loading="lazy" allowfullscreen></iframe></div>'
    if kind == "columns": return '<div class="article-columns">' + "".join(f'<div>{markdown(column.get("text", ""))}</div>' for column in block.get("columns", [])[:3]) + "</div>"
    if kind == "html": return '<div class="custom-html">' + sanitize_html(block.get("html", "")) + "</div>"
    return ""

def reading_time(record):
    text = record.get("text", "") + " " + record.get("originalThought", "") + " ".join(str(b.get("text", "")) for b in record.get("blocks", []))
    return max(1, round(len(text.split()) / 220))

def entry_html(record, preview=False, adjacent=(None, None)):
    kind, title = record.get("type", "post"), inferred_title(record)
    published, updated = record.get("publishedAt") or record.get("createdAt") or now(), record.get("updatedAt", "")
    meta = f'<time datetime="{E(published, quote=True)}">{E(display_date(published))}</time> · {reading_time(record)} min read'
    if updated and parse_date(updated) > parse_date(published) + dt.timedelta(minutes=1): meta += f' · Edited <time datetime="{E(updated, quote=True)}">{E(display_date(updated))}</time>'
    if kind == "article":
        subtitle = f'<p class="post-description">{E(record.get("subtitle", ""))}</p>' if record.get("subtitle") else ""
        header = f'<header class="entry-header"><p class="entry-kind">Article</p><h1>{E(title)}</h1>{subtitle}<p class="post-meta">{meta}</p></header>'
        if record.get("coverMediaId"): header += image_html(record, record["coverMediaId"], "wide", preview=preview)
        body = '<div class="article-content">' + "".join(block_html(record, b, preview) for b in record.get("blocks", [])) + "</div>"
        headings = [b for b in record.get("blocks", []) if b.get("type") == "heading"]
        if len(headings) >= 3: body = '<nav class="article-toc" aria-label="On this page"><h2>On this page</h2>' + "".join(f'<a href="#{E(slugify(b.get("text", "")), quote=True)}">{E(b.get("text", ""))}</a>' for b in headings) + "</nav>" + body
    else:
        show_title = bool(record.get("title", "").strip())
        header = f'<header class="entry-header post-entry-header"><p class="entry-kind">Post</p>{f"<h1>{E(title)}</h1>" if show_title else ""}<p class="post-meta">{meta}</p></header>'
        parts = []
        if record.get("text"): parts.append(f'<div class="post-copy">{markdown(record["text"])}</div>')
        if record.get("originalThought"): parts.append(original(record["originalThought"]))
        if record.get("imageIds"): parts.append(f'<div class="post-gallery" data-count="{len(record["imageIds"])}">' + "".join(image_html(record, item, preview=preview) for item in record["imageIds"]) + "</div>")
        if record.get("link"): parts.append(f'<p class="post-link"><a href="{E(safe_url(record["link"]), quote=True)}">{E(record["link"])}</a></p>')
        body = "".join(parts)
    previous, following = adjacent
    neighbors = ""
    if not preview and (previous or following):
        neighbors = '<nav class="entry-neighbors" aria-label="More writing">'
        for label, item in (("Previous", previous), ("Next", following)):
            if item: neighbors += f'<a href="/blog/{E(item["slug"], quote=True)}/"><small>{label}</small>{E(inferred_title(item))}</a>'
        neighbors += "</nav>"
    return f'<article class="blog-entry blog-{kind}" data-entry-type="{kind}">{header}{body}</article>{neighbors}'

def shell(title, description, body, canonical, image="", record=None, scripts=()):
    home = (ROOT / "index.html").read_text()
    header = re.search(r'<header class="site-header">.*?</header>', home, re.S).group(0)
    header = header.replace('href="#home"', 'href="/"').replace('href="#story"', 'href="/#story"').replace('href="#contact"', 'href="/#contact"').replace('href="projects/', 'href="/projects/').replace('href="about/"', 'href="/about/"').replace('src="BA_new_logo', 'src="/BA_new_logo')
    header = header.replace('<a class="nav-link" href="/blog/">Blog</a>', '<a class="nav-link active" href="/blog/">Blog</a>')
    social = image or SITE_URL + "/site_media/BA_previewcard.png"
    meta = f'<meta name="description" content="{E(description, quote=True)}"><link rel="canonical" href="{E(canonical, quote=True)}"><meta property="og:site_name" content="BA"><meta property="og:type" content="{("article" if record else "website")}"><meta property="og:title" content="{E(title, quote=True)}"><meta property="og:description" content="{E(description, quote=True)}"><meta property="og:url" content="{E(canonical, quote=True)}"><meta property="og:image" content="{E(social, quote=True)}"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{E(title, quote=True)}"><meta name="twitter:description" content="{E(description, quote=True)}"><meta name="twitter:image" content="{E(social, quote=True)}"><link rel="alternate" type="application/rss+xml" title="BA Blog" href="{SITE_URL}/blog/feed.xml">'
    structured = ""
    if record:
        fingerprint = hashlib.sha256(json.dumps(record, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]
        meta += f'<meta name="ba-content-id" content="{fingerprint}"><meta property="article:published_time" content="{E(record.get("publishedAt", ""), quote=True)}">'
        schema = {"@context":"https://schema.org","@type":"Article" if record["type"] == "article" else "BlogPosting","headline":inferred_title(record),"description":description,"datePublished":record.get("publishedAt"),"dateModified":record.get("updatedAt") or record.get("publishedAt"),"mainEntityOfPage":canonical,"author":{"@type":"Person","name":"Ivan Kudrenko","url":SITE_URL+"/about/"},"publisher":{"@type":"Organization","name":"BA","url":SITE_URL},"image":social}
        structured = '<script type="application/ld+json">' + json.dumps(schema, ensure_ascii=False).replace("</", "<\\/") + "</script>"
    script_tags = "".join(f'<script src="{E(src, quote=True)}" defer></script>' for src in scripts)
    return f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{E(title)} — BA</title>{meta}<link rel="icon" href="/BA_new_favicon.svg"><link rel="stylesheet" href="/styles.css"><link rel="stylesheet" href="/blog/blog.css"><script src="/script.js" defer></script>{script_tags}{structured}</head><body class="blog-page">{header}<main class="container blog-main">{body}</main><footer class="site-footer"><div class="container footer-inner"><p>© {dt.date.today().year} Ivan Kudrenko</p><p>BA · software, devices, experiments</p></div></footer></body></html>'

def normalize(record):
    record = dict(record); record.setdefault("schemaVersion", 2); record.setdefault("id", secrets.token_hex(12))
    record.setdefault("type", "article" if record.get("content") else "post"); record.setdefault("status", "draft")
    record.setdefault("createdAt", record.get("date") or now()); record.setdefault("updatedAt", record.get("updated") or "")
    record.setdefault("publishedAt", record.get("date") if record.get("status") == "published" else "")
    for key in ("title","subtitle","description","text","originalThought","link"): record.setdefault(key, "")
    for key in ("blocks","imageIds","media","tags","redirects"): record.setdefault(key, [])
    record.setdefault("seo", {}); record.setdefault("layout", {}); record.setdefault("coverMediaId", "")
    if record.get("content") and not record["blocks"]:
        record["blocks"] = [{"id":secrets.token_hex(6),"type":"paragraph","text":record.pop("content")}]
        if record.get("originalThought"): record["blocks"].insert(0,{"id":secrets.token_hex(6),"type":"original-thought","text":record["originalThought"]}); record["originalThought"] = ""
    record.setdefault("slug", "")
    if not record["slug"]: record["slug"] = slugify(inferred_title(record)) or f'post-{record["id"][:8]}'
    return record

def validate(record, publishing=False):
    if not isinstance(record, dict): raise ValueError("Invalid content record.")
    record = normalize(record)
    if record["type"] not in {"post","article"}: raise ValueError("Choose Post or Article.")
    if not re.fullmatch(r"[a-f0-9]{24}", record["id"]): raise ValueError("Invalid content ID.")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", record["slug"]) or record["slug"] in RESERVED: raise ValueError("Use a clean slug containing lowercase letters, numbers, and hyphens.")
    if not isinstance(record["blocks"], list) or not all(isinstance(b, dict) and b.get("type") in BLOCK_TYPES for b in record["blocks"]): raise ValueError("An Article block is invalid.")
    if publishing:
        if record["type"] == "post" and not any((record["text"].strip(),record["originalThought"].strip(),record["imageIds"],record["link"].strip())): raise ValueError("Write something or add a photo before publishing.")
        if record["type"] == "article" and (not record["title"].strip() or not record["blocks"]): raise ValueError("An Article needs a title and at least one block.")
        used = set(record["imageIds"]) | {record.get("coverMediaId","")} | {b.get("mediaId","") for b in record["blocks"]} | {m for b in record["blocks"] for m in b.get("mediaIds",[])}
        block_alts = {block.get("mediaId"): block.get("alt", "") for block in record["blocks"] if block.get("type") == "image"}
        for item in record["media"]:
            if item.get("id") in used and not (item.get("alt", "").strip() or block_alts.get(item.get("id"), "").strip()): raise ValueError(f'Add alt text for “{item.get("originalName","image")}”.')
    return record

def load(path): return normalize(json.loads(path.read_text()))
def public_records():
    POSTS.mkdir(parents=True, exist_ok=True)
    records = [load(path) for path in POSTS.glob("*.json")]
    return sorted((record for record in records if record.get("status") == "published"), key=lambda r:parse_date(r.get("publishedAt","")), reverse=True)
def all_records():
    records = {r["id"]:r for r in public_records()}; PRIVATE_POSTS.mkdir(parents=True, exist_ok=True)
    for legacy in PRIVATE.glob("*.json"):
        migrated = load(legacy)
        destination = PRIVATE_POSTS / f'{migrated["id"]}.json'
        destination.write_text(json.dumps(migrated, ensure_ascii=False, indent=2) + "\n")
        legacy.unlink()
    for path in PRIVATE_POSTS.glob("*.json"): record = load(path); records[record["id"]] = record
    return list(records.values())

def feed_row(record, home=False):
    lead = record.get("coverMediaId") or ((record.get("imageIds") or [""])[0]); image = image_html(record,lead) if lead else ""
    tag = "h3" if home else "h2"; desc = excerpt(record)
    return f'<article class="blog-row" data-blog-type="{record["type"]}"><a href="/blog/{E(record["slug"],quote=True)}/"><div class="blog-row-meta"><span>{record["type"].title()}</span><time datetime="{E(record["publishedAt"],quote=True)}">{E(display_date(record["publishedAt"]))}</time></div><div class="blog-row-copy"><{tag}>{E(inferred_title(record))}</{tag}>{f"<p>{E(desc)}</p>" if desc else ""}</div>{image if not home else ""}<span class="blog-row-arrow" aria-hidden="true">→</span></a></article>'

def rss(records):
    items = []
    for r in records:
        link = f'{SITE_URL}/blog/{r["slug"]}/'; rendered = entry_html(r).replace("]]>","]]&gt;")
        items.append(f'<item><title>{E(inferred_title(r))}</title><link>{link}</link><guid isPermaLink="true">{link}</guid><pubDate>{parse_date(r["publishedAt"]).strftime("%a, %d %b %Y %H:%M:%S %z")}</pubDate><description>{E(excerpt(r))}</description><content:encoded><![CDATA[{rendered}]]></content:encoded></item>')
    return '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/"><channel><title>BA Blog</title><link>https://baproj.com/blog/</link><description>Thoughts, observations, things I’m building, and things I keep thinking about.</description><language>en-us</language>'+"".join(items)+"</channel></rss>\n"

def build():
    records, changed, blog = public_records(), set(), ROOT/"blog"; blog.mkdir(exist_ok=True)
    slugs = {r["slug"] for r in records} | {s for r in records for s in r.get("redirects",[])}
    for marker in blog.glob("*/.generated"):
        if marker.parent.name not in slugs: shutil.rmtree(marker.parent); changed.add(marker.parent)
    for index, record in enumerate(records):
        folder = blog/record["slug"]; folder.mkdir(exist_ok=True)
        previous = records[index+1] if index+1<len(records) else None; following = records[index-1] if index else None
        canonical = f'{SITE_URL}/blog/{record["slug"]}/'; lead = media_map(record).get(record.get("coverMediaId") or ((record.get("imageIds") or [""])[0]),{})
        image = SITE_URL+lead.get("publicPath","") if lead.get("publicPath") else ""
        body = '<a class="text-link back-to-blog" href="/blog/">← All writing</a>'+entry_html(record,adjacent=(previous,following))+'<div class="entry-actions"><button class="copy-link" type="button" data-copy-link>Copy link</button></div>'
        (folder/"index.html").write_text(shell(record.get("seo",{}).get("title") or inferred_title(record),record.get("seo",{}).get("description") or excerpt(record),body,canonical,image,record,["/blog/public.js"])); (folder/".generated").touch(); changed |= {folder/"index.html",folder/".generated"}
        for old in record.get("redirects",[]):
            target=blog/old; target.mkdir(exist_ok=True); destination=f'/blog/{record["slug"]}/'
            (target/"index.html").write_text(f'<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="robots" content="noindex"><link rel="canonical" href="{SITE_URL}{destination}"><meta http-equiv="refresh" content="0; url={destination}"><title>Moved — BA</title></head><body><a href="{destination}">This writing moved.</a></body></html>'); (target/".generated").touch(); changed |= {target/"index.html",target/".generated"}
    rows = "".join(feed_row(r) for r in records) or '<p class="blog-empty">No posts yet. There will be thoughts here soon.</p>'
    filters='<nav class="blog-filters" aria-label="Filter writing"><button type="button" data-filter="all" aria-pressed="true">All</button><button type="button" data-filter="post" aria-pressed="false">Posts</button><button type="button" data-filter="article" aria-pressed="false">Articles</button></nav>'
    body='<header class="blog-heading"><h1>Blog</h1><p>Thoughts, observations, things I’m building, and things I keep thinking about.</p></header>'+filters+f'<div class="blog-feed" aria-live="polite">{rows}</div><p class="blog-filter-empty" hidden>No writing in this format yet.</p>'
    (blog/"index.html").write_text(shell("Blog","Thoughts, observations, things I’m building, and things I keep thinking about.",body,SITE_URL+"/blog/",scripts=["/blog/public.js"])); (blog/"feed.xml").write_text(rss(records))
    pages=["/","/about/","/projects/activeview/","/projects/ba/","/projects/youtube/","/blog/"]
    urls=[f'<url><loc>{SITE_URL}{p}</loc></url>' for p in pages]+[f'<url><loc>{SITE_URL}/blog/{r["slug"]}/</loc><lastmod>{parse_date(r.get("updatedAt") or r["publishedAt"]).date()}</lastmod></url>' for r in records]
    (ROOT/"sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+"".join(urls)+"</urlset>\n"); (ROOT/"robots.txt").write_text("User-agent: *\nAllow: /\nSitemap: https://baproj.com/sitemap.xml\n")
    changed |= {blog/"index.html",blog/"feed.xml",ROOT/"sitemap.xml",ROOT/"robots.txt"}
    home=ROOT/"index.html"; text=home.read_text(); section='<!-- BLOG START --><section class="home-blog" id="blog"><div class="container"><header><h2>Blog</h2><a class="text-link" href="/blog/">View all posts →</a></header>'+(("".join(feed_row(r,True) for r in records[:3])) or '<p class="blog-empty">No posts yet. There will be thoughts here soon.</p>')+'</div></section><!-- BLOG END -->'
    text=re.sub(r'<!-- BLOG START -->.*?<!-- BLOG END -->',lambda _:section,text,flags=re.S) if '<!-- BLOG START -->' in text else text.replace('      <section class="contact-section"',section+'\n      <section class="contact-section"'); home.write_text(text); changed.add(home)
    return changed

def dimensions(path):
    if not shutil.which("sips"): return 0,0
    result=subprocess.run(["sips","-g","pixelWidth","-g","pixelHeight",str(path)],capture_output=True,text=True,timeout=30)
    width,height=re.search(r"pixelWidth:\s*(\d+)",result.stdout),re.search(r"pixelHeight:\s*(\d+)",result.stdout)
    return (int(width.group(1)),int(height.group(1))) if width and height else (0,0)

def process_media(record):
    source_folder,public_folder=PRIVATE_MEDIA/record["id"],PUBLIC_ASSETS/record["id"]
    for item in record["media"]:
        public_folder.mkdir(parents=True,exist_ok=True)
        source=source_folder/item["storedName"]
        if not source.exists() and item.get("publicPath"): continue
        if not source.exists(): raise ValueError(f'Missing image “{item.get("originalName","image")}”. Add it again.')
        stem=slugify(Path(item["storedName"]).stem) or item["id"]; width,height=dimensions(source); variants=[]
        if shutil.which("sips") and item["mime"] not in {"image/gif","image/webp"}:
            target_widths = sorted(set([size for size in (640,1200,2000) if not width or size < width] + ([min(width,2000)] if width else [2000])))
            for target_width in target_widths:
                destination=public_folder/f"{stem}-{target_width}.jpg"
                subprocess.run(["sips","-s","format","jpeg","-s","formatOptions","82","-Z",str(target_width),str(source),"--out",str(destination)],check=True,capture_output=True,timeout=120)
                actual,_=dimensions(destination); variants.append({"path":f'/blog/assets/{record["id"]}/{destination.name}',"width":actual or target_width})
        else:
            destination=public_folder/f'{stem}{IMAGE_TYPES.get(item["mime"],source.suffix)}'; shutil.copy2(source,destination); variants=[{"path":f'/blog/assets/{record["id"]}/{destination.name}',"width":width or 2000}]
        item.update({"variants":sorted(variants,key=lambda v:v["width"]),"publicPath":variants[-1]["path"],"width":width,"height":height})
    return record

def git_status(paths=None):
    command=["git","status","--porcelain=v1"]
    if paths: command += ["--"]+[str(p.relative_to(ROOT)) for p in paths]
    return subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=30,check=True).stdout.splitlines()
def git(*args,timeout=120): return subprocess.run(["git",*args],cwd=ROOT,capture_output=True,text=True,timeout=timeout,check=True)

def publish(record,push):
    record=validate(record,True); published=public_records(); old=next((r for r in published if r["id"]==record["id"]),None)
    if any(r["slug"]==record["slug"] and r["id"]!=record["id"] for r in published): raise ValueError("That URL already belongs to another item.")
    if old and old["slug"]!=record["slug"] and old["slug"] not in record["redirects"]: record["redirects"].append(old["slug"])
    protected=[ROOT/"index.html",ROOT/"blog/index.html",ROOT/"blog/feed.xml",ROOT/"sitemap.xml",ROOT/"robots.txt"]
    if push and git_status(protected): raise ValueError("Publishing paused because generated shared files have uncommitted changes. Commit this Blog system upgrade first; no publishing files were changed.")
    stamp=now(); record.update({"status":"published","hasPrivateChanges":False,"publishedAt":old.get("publishedAt") if old else (record.get("publishedAt") or stamp),"updatedAt":stamp if old else "","savedAt":stamp}); process_media(record)
    target=POSTS/f'{record["id"]}.json'; target.parent.mkdir(parents=True,exist_ok=True); target.write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n"); (PRIVATE_POSTS/f'{record["id"]}.json').unlink(missing_ok=True)
    generated=build(); intentional={target}|generated
    if any((PUBLIC_ASSETS/record["id"]).glob("*")): intentional.add(PUBLIC_ASSETS/record["id"])
    unrelated=[line for line in git_status() if not any(str(p.relative_to(ROOT)) in line for p in intentional)] if (ROOT/".git").exists() else []
    result={"post":record,"state":"generated","message":"Public files generated locally.","unrelated":unrelated}
    if not push:return result
    paths=sorted({p for p in intentional if p.exists()},key=str); pathspecs=[str(p.relative_to(ROOT)) for p in paths]; git("add","--",*pathspecs)
    git("commit","--only","-m",("Publish blog article: " if record["type"]=="article" else "Publish blog post: ")+inferred_title(record),"--",*pathspecs)
    branch=git("branch","--show-current").stdout.strip(); git("push","origin",branch,timeout=180)
    result.update({"state":"pushed","message":"Pushed to GitHub. Waiting for the live site…","branch":branch,"liveUrl":f'{SITE_URL}/blog/{record["slug"]}/',"fingerprint":hashlib.sha256(json.dumps(record,sort_keys=True,ensure_ascii=False).encode()).hexdigest()[:16]}); return result

def unpublish(record,push):
    record=validate(record); old=next((r for r in public_records() if r["id"]==record["id"]),None)
    if not old: raise ValueError("This item is not published.")
    if push and git_status([ROOT/"index.html",ROOT/"blog/index.html",ROOT/"blog/feed.xml",ROOT/"sitemap.xml"]): raise ValueError("Unpublishing paused because generated shared files have uncommitted changes.")
    record.update({"status":"draft","hasPrivateChanges":False,"savedAt":now()}); PRIVATE_POSTS.mkdir(parents=True,exist_ok=True); (PRIVATE_POSTS/f'{record["id"]}.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n")
    source=POSTS/f'{record["id"]}.json'; source.unlink(missing_ok=True); public_media=PUBLIC_ASSETS/record["id"]; shutil.rmtree(public_media,ignore_errors=True); generated=build(); pathspecs=sorted({str(p.relative_to(ROOT)) for p in generated|{source,ROOT/"blog"/old["slug"],public_media}})
    if push:
        git("add","-A","--",*pathspecs); git("commit","--only","-m",f'Unpublish blog: {inferred_title(record)}',"--",*pathspecs); branch=git("branch","--show-current").stdout.strip(); git("push","origin",branch,timeout=180)
        return {"post":record,"state":"pushed","message":"Unpublished and pushed. The URL will disappear after deployment."}
    return {"post":record,"state":"generated","message":"Unpublished locally and preserved as a private draft."}

class Handler(http.server.SimpleHTTPRequestHandler):
    server_version="BAWriter/2"
    def __init__(self,*args,**kwargs): super().__init__(*args,directory=str(ROOT),**kwargs)
    def log_message(self,*args): pass
    def allowed(self): return self.headers.get("Host")==f"127.0.0.1:{self.server.server_port}"
    def authenticated(self): return f"ba_session={self.server.session}" in self.headers.get("Cookie","").split("; ")
    def reply(self,value,status=200):
        data=json.dumps(value,ensure_ascii=False).encode(); self.send_response(status); self.send_header("Content-Type","application/json; charset=utf-8"); self.send_header("Cache-Control","no-store"); self.send_header("X-Content-Type-Options","nosniff"); self.end_headers(); self.wfile.write(data)
    def serve_file(self,path,kind):
        if not path.exists(): self.send_error(404); return
        self.send_response(200); self.send_header("Content-Type",kind); self.send_header("Cache-Control","no-store"); self.send_header("X-Content-Type-Options","nosniff"); self.end_headers(); self.wfile.write(path.read_bytes())
    def do_GET(self):
        parsed=urllib.parse.urlparse(self.path); path=parsed.path
        if not self.allowed(): self.reply({"error":"Invalid host."},403); return
        if path=="/health": self.reply({"ok":True}); return
        writer_files={"/writer/":("index.html","text/html; charset=utf-8"),"/writer":("index.html","text/html; charset=utf-8"),"/writer/editor.js":("editor.js","text/javascript; charset=utf-8"),"/writer/editor.css":("editor.css","text/css; charset=utf-8")}
        if path in writer_files: name,kind=writer_files[path]; self.serve_file(ROOT/"tools/writer"/name,kind); return
        if path.startswith("/api/"):
            if not self.authenticated(): self.reply({"error":"Sign in to your local Writer."},401); return
            if path=="/api/posts": self.reply({"posts":all_records(),"push":self.server.push,"branch":self.server.branch}); return
            if path.startswith("/api/media/"):
                parts=path.split("/")
                if len(parts)!=5 or not re.fullmatch(r"[a-f0-9]{24}",parts[3]) or not re.fullmatch(r"[\w.-]+",parts[4]): self.send_error(404); return
                media=PRIVATE_MEDIA/parts[3]/parts[4]; self.serve_file(media,mimetypes.guess_type(media.name)[0] or "application/octet-stream"); return
            if path=="/api/history":
                content_id=urllib.parse.parse_qs(parsed.query).get("id",[""])[0]
                result=subprocess.run(["git","log","--date=short","--pretty=format:%h%x09%ad%x09%s","--",f"content/posts/{content_id}.json"],cwd=ROOT,capture_output=True,text=True,timeout=30) if re.fullmatch(r"[a-f0-9]{24}",content_id) else None
                history=[dict(zip(("commit","date","message"),line.split("\t",2))) for line in (result.stdout.splitlines() if result else [])]; self.reply({"history":history}); return
            if path=="/api/deploy-status":
                query=urllib.parse.parse_qs(parsed.query); target=query.get("url",[""])[0]; fingerprint=query.get("fingerprint",[""])[0]
                if not target.startswith(SITE_URL+"/blog/") or not re.fullmatch(r"[a-f0-9]{16}",fingerprint): self.reply({"error":"Invalid deployment check."},400); return
                try:
                    request=urllib.request.Request(target+f"?deploy={int(time.time())}",headers={"User-Agent":"BA Writer deployment check"}); page=urllib.request.urlopen(request,timeout=10).read().decode("utf-8","replace"); live=f'content="{fingerprint}"' in page
                    self.reply({"state":"live" if live else "deploying","message":"Live" if live else "GitHub received the push; deployment is still updating."})
                except (urllib.error.URLError,TimeoutError): self.reply({"state":"deploying","message":"Waiting for the public site to respond."})
                return
            self.reply({"error":"Not found."},404); return
        if path.startswith(("/.blog-private","/tools/","/content/","/BA Writer.app/")) or any(p.startswith(".") for p in Path(urllib.parse.unquote(path)).parts): self.send_error(404); return
        super().do_GET()
    def do_POST(self):
        if not self.allowed() or self.headers.get("Origin")!=f"http://127.0.0.1:{self.server.server_port}": self.reply({"error":"Invalid origin."},403); return
        size=int(self.headers.get("Content-Length","0"))
        if size>30_000_000: self.reply({"error":"Upload is larger than 30 MB."},413); return
        try:
            if self.path=="/api/login":
                payload=json.loads(self.rfile.read(size))
                if not secrets.compare_digest(str(payload.get("password","")),self.server.password): self.reply({"error":"Incorrect password."},401); return
                self.send_response(200); self.send_header("Set-Cookie",f"ba_session={self.server.session}; HttpOnly; SameSite=Strict; Path=/"); self.send_header("Content-Type","application/json"); self.end_headers(); self.wfile.write(b"{}"); return
            if not self.authenticated(): self.reply({"error":"Sign in first."},401); return
            if self.path=="/api/upload":
                content_id=self.headers.get("X-Content-Id",""); name=urllib.parse.unquote(self.headers.get("X-Filename","image")); mime=self.headers.get("Content-Type","").split(";",1)[0].lower()
                if not re.fullmatch(r"[a-f0-9]{24}",content_id) or mime not in IMAGE_TYPES: raise ValueError("Choose a JPEG, PNG, WebP, GIF, HEIC, or HEIF image.")
                media_id=secrets.token_hex(8); stored=media_id+IMAGE_TYPES[mime]; folder=PRIVATE_MEDIA/content_id; folder.mkdir(parents=True,exist_ok=True); (folder/stored).write_bytes(self.rfile.read(size))
                self.reply({"media":{"id":media_id,"originalName":Path(name).name[:180],"storedName":stored,"mime":mime,"alt":"","caption":""}}); return
            payload=json.loads(self.rfile.read(size))
            if self.path=="/api/preview": self.reply({"html":entry_html(validate(payload),True)}); return
            with self.server.lock:
                record=validate(payload,self.path=="/api/publish"); draft=PRIVATE_POSTS/f'{record["id"]}.json'
                if self.path=="/api/save":
                    is_public=any(item["id"]==record["id"] for item in public_records()); record["status"]="published" if is_public else "draft"; record["hasPrivateChanges"]=is_public; record["savedAt"]=now(); PRIVATE_POSTS.mkdir(parents=True,exist_ok=True); draft.write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n"); self.reply({"post":record,"message":"Saved"}); return
                if self.path=="/api/publish": self.reply(publish(record,self.server.push)); return
                if self.path=="/api/unpublish": self.reply(unpublish(record,self.server.push)); return
                if self.path=="/api/delete":
                    if any(r["id"]==record["id"] for r in public_records()): raise ValueError("Unpublish this item before deleting it.")
                    draft.unlink(missing_ok=True); shutil.rmtree(PRIVATE_MEDIA/record["id"],ignore_errors=True); self.reply({"message":"Draft deleted."}); return
                if self.path=="/api/delete-media":
                    stored=payload.get("storedName","")
                    if not re.fullmatch(r"[\w.-]+",stored): raise ValueError("Invalid image.")
                    (PRIVATE_MEDIA/record["id"]/stored).unlink(missing_ok=True); self.reply({"message":"Image removed."}); return
            self.reply({"error":"Not found."},404)
        except (ValueError,KeyError,json.JSONDecodeError) as error: self.reply({"error":str(error)},400)
        except subprocess.CalledProcessError as error:
            detail=(error.stderr or error.stdout or "Git command failed.").strip().splitlines()[-1]; self.reply({"error":f"Git could not complete publishing: {detail}. Your content remains saved locally."},500)
        except Exception: self.reply({"error":"Could not complete that operation. Your last saved draft is still on this Mac."},500)

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("command",choices=["serve","build","check"]); parser.add_argument("--push",action="store_true"); parser.add_argument("--port",type=int,default=8787); args=parser.parse_args()
    if args.command=="build": build(); return
    if args.command=="check":
        for record in public_records(): validate(record,True)
        print(f"Validated {len(public_records())} published item(s)."); return
    for folder in (PRIVATE_POSTS,PRIVATE_MEDIA,POSTS): folder.mkdir(parents=True,exist_ok=True)
    server=http.server.ThreadingHTTPServer(("127.0.0.1",args.port),Handler); secret=PRIVATE/"writer-secret"
    if os.environ.get("BA_BLOG_PASSWORD"): password=os.environ["BA_BLOG_PASSWORD"]
    elif secret.exists(): password=secret.read_text().strip()
    else: password=secrets.token_urlsafe(24); secret.write_text(password); secret.chmod(0o600)
    server.password=password; server.session=secrets.token_urlsafe(32); server.push=args.push; server.lock=threading.Lock(); server.branch=subprocess.run(["git","branch","--show-current"],cwd=ROOT,capture_output=True,text=True).stdout.strip()
    print(f"BA Writer: http://127.0.0.1:{args.port}/writer/\nPassword: {password}\nGit publishing: {'enabled' if args.push else 'dry run'}",flush=True); server.serve_forever()

if __name__=="__main__": main()
