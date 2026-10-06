(() => {
  const $ = (id) => document.getElementById(id);
  const uid = (bytes = 12) => [...crypto.getRandomValues(new Uint8Array(bytes))].map((n) => n.toString(16).padStart(2, "0")).join("");
  const iso = () => new Date().toISOString();
  const dateOnly = (value = new Date()) => new Date(value).toLocaleDateString("en-CA");
  const slugify = (value) => value.normalize("NFKD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 96);
  const state = { posts: [], current: null, dirty: false, saveTimer: null, busy: false, uploadTarget: "post", dragging: null, push: false };
  const blockTypes = [
    ["paragraph", "Paragraph"], ["heading", "Heading"], ["quote", "Quote"], ["original-thought", "Original Thought"],
    ["image", "Image"], ["gallery", "Gallery"], ["code", "Code"], ["callout", "Callout"], ["divider", "Divider"],
    ["embed", "Embed"], ["columns", "Columns"], ["spacer", "Spacer"], ["html", "Custom HTML"]
  ];

  const status = (text) => { $("save-state").textContent = text; };
  const progress = (text) => { $("publish-progress").textContent = text; };
  async function api(path, body, options = {}) {
    const response = await fetch(`/api/${path}`, body === undefined ? {} : {
      method: "POST",
      headers: options.headers || { "Content-Type": "application/json" },
      body: options.raw ? body : JSON.stringify(body)
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "BA Writer could not complete that request.");
    return result;
  }

  function blank(type = "post") {
    return { schemaVersion: 2, id: uid(), type, status: "draft", title: "", subtitle: "", slug: "", description: "", text: "", originalThought: "", link: "", blocks: type === "article" ? [{ id: uid(6), type: "paragraph", text: "" }] : [], imageIds: [], coverMediaId: "", media: [], tags: [], seo: {}, layout: {}, redirects: [], createdAt: iso(), updatedAt: "", publishedAt: "", savedAt: "" };
  }

  function titleFor(record) {
    if (record.title?.trim()) return record.title.trim();
    const first = (record.text || "").replace(/\s+/g, " ").trim();
    return first ? (first.length > 72 ? `${first.slice(0, 68)}…` : first) : "Untitled post";
  }

  function mediaItem(id) { return state.current.media.find((item) => item.id === id); }
  function mediaSrc(item) { return item ? `/api/media/${state.current.id}/${item.storedName}` : ""; }
  function markDirty() {
    if (!state.current || state.busy) return;
    state.dirty = true;
    status("Unsaved changes");
    clearTimeout(state.saveTimer);
    state.saveTimer = setTimeout(saveDraft, 900);
  }

  function collect() {
    const record = structuredClone(state.current);
    record.type = document.querySelector("[data-mode][aria-pressed=true]").dataset.mode;
    record.text = $("post-text").value;
    record.originalThought = $("post-original").value;
    record.link = $("post-link").value.trim();
    if (record.type === "article") {
      record.title = $("article-title").value;
      record.subtitle = $("article-subtitle").value;
      record.blocks = [...$("blocks").querySelectorAll(".editor-block")].map(readBlock);
    }
    record.title = $("setting-title").value || record.title;
    record.slug = $("setting-slug").value.trim() || slugify(record.title || record.text) || `post-${record.id.slice(0, 8)}`;
    record.description = $("setting-description").value;
    record.tags = $("setting-tags").value.split(",").map((tag) => tag.trim()).filter(Boolean);
    record.seo = { title: $("setting-seo-title").value, description: $("setting-seo-description").value };
    const chosenDate = $("setting-date").value;
    if (chosenDate && record.publishedAt) record.publishedAt = `${chosenDate}T12:00:00Z`;
    return record;
  }

  async function saveDraft() {
    if (!state.current || state.busy || !state.dirty) return;
    state.busy = true; status("Saving…");
    try {
      const result = await api("save", collect());
      state.current = result.post; state.dirty = false; status("Saved");
      refreshLocalRecord(result.post);
    } catch (error) { status(error.message); }
    finally { state.busy = false; }
  }

  function refreshLocalRecord(record) {
    const index = state.posts.findIndex((item) => item.id === record.id);
    if (index >= 0) state.posts[index] = record; else state.posts.push(record);
  }

  function renderLibrary() {
    for (const [statusName, id] of [["draft", "draft-list"], ["published", "published-list"]]) {
      const container = $(id); container.replaceChildren();
      const matching = state.posts.filter((item) => statusName === "draft" ? item.status === "draft" || item.hasPrivateChanges : item.status === "published" && !item.hasPrivateChanges).sort((a, b) => (b.savedAt || b.publishedAt || b.createdAt).localeCompare(a.savedAt || a.publishedAt || a.createdAt));
      if (!matching.length) { const empty = document.createElement("p"); empty.className = "library-empty"; empty.textContent = statusName === "draft" ? "No drafts yet." : "Nothing published yet."; container.append(empty); continue; }
      matching.forEach((record) => {
        const button = document.createElement("button"); button.type = "button"; button.className = "library-item";
        const copy = document.createElement("span"); const title = document.createElement("strong"); title.textContent = titleFor(record); const meta = document.createElement("span"); meta.textContent = `${record.type === "article" ? "Article" : "Post"} · ${record.status === "published" ? "Published" : "Draft"}`; copy.append(title, meta);
        const time = document.createElement("time"); const date = record.savedAt || record.publishedAt || record.createdAt; time.dateTime = date; time.textContent = new Date(date).toLocaleDateString(); button.append(copy, time); button.addEventListener("click", () => openRecord(record)); container.append(button);
      });
    }
  }

  function switchScreen(screen) {
    $("library").hidden = screen !== "library"; $("editor").hidden = screen !== "editor";
    if (screen === "library") { $("settings").hidden = true; renderLibrary(); }
  }

  function setMode(type, convert = false) {
    const previousType = state.current.type;
    if (convert) state.current = collect();
    document.querySelectorAll("[data-mode]").forEach((button) => button.setAttribute("aria-pressed", String(button.dataset.mode === type)));
    $("post-composer").hidden = type !== "post"; $("article-composer").hidden = type !== "article";
    if (convert && previousType !== type) {
      if (type === "article" && state.current.text.trim() && !state.current.blocks.length) state.current.blocks = [{ id: uid(6), type: "paragraph", text: state.current.text }];
      state.current.type = type; renderBlocks(); markDirty();
    }
  }

  function setView(view) {
    document.querySelectorAll("[data-view]").forEach((button) => button.setAttribute("aria-pressed", String(button.dataset.view === view)));
    const preview = view === "preview"; $("preview").hidden = !preview; $("post-composer").hidden = preview || state.current.type !== "post"; $("article-composer").hidden = preview || state.current.type !== "article";
    if (preview) renderPreview();
  }

  function openRecord(record) {
    state.current = structuredClone(record); state.dirty = false;
    $("post-text").value = record.text || ""; $("post-original").value = record.originalThought || ""; $("post-link").value = record.link || "";
    $("post-original-wrap").hidden = !record.originalThought; $("post-link-wrap").hidden = !record.link;
    $("article-title").value = record.title || ""; $("article-subtitle").value = record.subtitle || "";
    $("setting-title").value = record.title || ""; $("setting-slug").value = record.slug || ""; $("setting-description").value = record.description || "";
    $("setting-tags").value = (record.tags || []).join(", "); $("setting-date").value = record.publishedAt ? dateOnly(record.publishedAt) : dateOnly();
    $("setting-seo-title").value = record.seo?.title || ""; $("setting-seo-description").value = record.seo?.description || "";
    $("publish").textContent = record.status === "published" ? "Publish update" : "Publish"; $("unpublish").hidden = record.status !== "published"; $("delete").hidden = record.status === "published";
    renderPostMedia(); renderCover(); renderBlocks(); setMode(record.type); setView("write"); switchScreen("editor"); status(record.savedAt ? "Saved" : "New draft"); progress(""); autoSizeAll(); loadHistory();
  }

  function makeBlock(type) {
    const block = { id: uid(6), type };
    if (["paragraph", "heading", "quote", "original-thought", "callout", "code"].includes(type)) block.text = "";
    if (type === "heading") block.level = 2;
    if (type === "image") { block.mediaId = ""; block.layout = "normal"; block.caption = ""; block.alt = ""; }
    if (type === "gallery") block.mediaIds = [];
    if (type === "embed") block.url = "";
    if (type === "columns") block.columns = [{ text: "" }, { text: "" }];
    if (type === "html") block.html = "";
    return block;
  }

  function readBlock(node) {
    const id = node.dataset.id, type = node.dataset.type, block = { id, type };
    const value = (selector) => node.querySelector(selector)?.value || "";
    if (["paragraph", "heading", "quote", "original-thought", "callout", "code"].includes(type)) block.text = value("textarea");
    if (type === "heading") block.level = Number(value("select[data-field=level]") || 2);
    if (type === "quote") block.caption = value("input[data-field=caption]");
    if (type === "image") { block.mediaId = node.dataset.mediaId || ""; block.layout = value("select[data-field=layout]") || "normal"; block.caption = value("input[data-field=caption]"); block.alt = value("input[data-field=alt]"); }
    if (type === "gallery") block.mediaIds = (node.dataset.mediaIds || "").split(",").filter(Boolean);
    if (type === "embed") block.url = value("input");
    if (type === "columns") block.columns = [...node.querySelectorAll("textarea")].map((area) => ({ text: area.value }));
    if (type === "html") block.html = value("textarea");
    return block;
  }

  function controlButton(label, action) { const button = document.createElement("button"); button.type = "button"; button.textContent = label; button.setAttribute("aria-label", action); return button; }
  function renderBlocks() {
    const container = $("blocks"); container.replaceChildren();
    state.current.blocks.forEach((block) => {
      const node = document.createElement("section"); node.className = "editor-block"; node.dataset.id = block.id; node.dataset.type = block.type; node.draggable = true;
      const controls = document.createElement("div"); controls.className = "block-controls";
      const drag = controlButton("⋮⋮", "Drag to reorder block"); drag.className = "drag-handle"; drag.tabIndex = -1;
      const select = document.createElement("select"); select.setAttribute("aria-label", "Block type"); blockTypes.forEach(([value, label]) => { const option = document.createElement("option"); option.value = value; option.textContent = label; option.selected = block.type === value; select.append(option); });
      select.addEventListener("change", () => { Object.assign(block, makeBlock(select.value), { id: block.id }); renderBlocks(); markDirty(); });
      const up = controlButton("↑", "Move block up"), down = controlButton("↓", "Move block down"), remove = controlButton("Remove", "Delete block");
      up.addEventListener("click", () => moveBlock(block.id, -1)); down.addEventListener("click", () => moveBlock(block.id, 1)); remove.addEventListener("click", () => { state.current.blocks = state.current.blocks.filter((item) => item.id !== block.id); renderBlocks(); markDirty(); }); controls.append(drag, select, up, down, remove); node.append(controls);
      renderBlockFields(node, block); bindBlockDrag(node); container.append(node);
    });
    autoSizeAll();
  }

  function field(tag, value, placeholder, dataField) { const input = document.createElement(tag); input.value = value || ""; input.placeholder = placeholder || ""; if (dataField) input.dataset.field = dataField; input.addEventListener("input", markDirty); if (tag === "textarea") input.addEventListener("keydown", slashCommand); return input; }
  function renderBlockFields(node, block) {
    if (["paragraph", "heading", "quote", "original-thought", "callout", "code"].includes(block.type)) node.append(field("textarea", block.text, block.type === "paragraph" ? "Start writing…" : blockTypes.find(([type]) => type === block.type)[1]));
    if (block.type === "heading") { const select = document.createElement("select"); select.dataset.field = "level"; select.innerHTML = '<option value="2">H2</option><option value="3">H3</option>'; select.value = block.level || 2; select.addEventListener("change", markDirty); node.append(select); }
    if (block.type === "quote") node.append(field("input", block.caption, "Attribution (optional)", "caption"));
    if (block.type === "divider" || block.type === "spacer") { const label = document.createElement("p"); label.textContent = block.type === "divider" ? "Divider" : "Space"; node.append(label); }
    if (block.type === "embed") node.append(field("input", block.url, "YouTube or Vimeo URL"));
    if (block.type === "html") node.append(field("textarea", block.html, "Advanced custom HTML (sanitized when rendered)"));
    if (block.type === "columns") (block.columns || [{ text: "" }, { text: "" }]).forEach((column) => node.append(field("textarea", column.text, "Column text")));
    if (block.type === "image") renderImageBlock(node, block);
    if (block.type === "gallery") renderGalleryBlock(node, block);
  }

  function renderImageBlock(node, block) {
    node.dataset.mediaId = block.mediaId || ""; const item = mediaItem(block.mediaId);
    if (item) { const image = document.createElement("img"); image.src = mediaSrc(item); image.alt = item.alt || ""; image.style.maxWidth = "100%"; image.style.borderRadius = "8px"; node.append(image); }
    const add = controlButton(item ? "Replace image" : "Choose image", "Choose image"); add.addEventListener("click", () => { state.uploadTarget = `block:${block.id}`; $("photo-input").multiple = false; $("photo-input").click(); }); node.append(add);
    const layout = document.createElement("select"); layout.dataset.field = "layout"; layout.innerHTML = '<option value="normal">Normal</option><option value="wide">Wide</option><option value="full">Full width</option>'; layout.value = block.layout || "normal"; layout.addEventListener("change", markDirty); node.append(layout, field("input", block.alt || item?.alt, "Alt text", "alt"), field("input", block.caption || item?.caption, "Caption (optional)", "caption"));
  }

  function renderGalleryBlock(node, block) {
    node.dataset.mediaIds = (block.mediaIds || []).join(","); const grid = document.createElement("div"); grid.className = "media-grid";
    (block.mediaIds || []).forEach((id, index) => { const item = mediaItem(id); if (!item) return; const card = document.createElement("div"); card.className = "media-card"; const image = document.createElement("img"); image.src = mediaSrc(item); image.alt = item.alt || ""; const controls=document.createElement("div"); controls.className="media-card-controls"; const left=controlButton("←","Move image left"),right=controlButton("→","Move image right"),remove=controlButton("Remove","Remove image"); left.onclick=()=>moveGalleryImage(block,index,-1); right.onclick=()=>moveGalleryImage(block,index,1); remove.onclick=()=>{block.mediaIds=block.mediaIds.filter((mediaId)=>mediaId!==id);renderBlocks();markDirty();}; controls.append(left,right,remove); const alt=field("input",item.alt,"Alt text"),caption=field("input",item.caption,"Caption (optional)"); alt.addEventListener("input",()=>item.alt=alt.value); caption.addEventListener("input",()=>item.caption=caption.value); const fields=document.createElement("div"); fields.className="media-card-fields"; fields.append(alt,caption); card.append(image,controls,fields); grid.append(card); }); node.append(grid);
    const add = controlButton("Add gallery images", "Add gallery images"); add.addEventListener("click", () => { state.uploadTarget = `gallery:${block.id}`; $("photo-input").multiple = true; $("photo-input").click(); }); node.append(add);
  }
  function moveGalleryImage(block,index,delta){const next=Math.max(0,Math.min(block.mediaIds.length-1,index+delta));const [id]=block.mediaIds.splice(index,1);block.mediaIds.splice(next,0,id);renderBlocks();markDirty();}

  function moveBlock(id, change) { const index = state.current.blocks.findIndex((block) => block.id === id), next = Math.max(0, Math.min(state.current.blocks.length - 1, index + change)); if (index === next) return; const [block] = state.current.blocks.splice(index, 1); state.current.blocks.splice(next, 0, block); renderBlocks(); markDirty(); }
  function bindBlockDrag(node) {
    node.addEventListener("dragstart", () => { state.dragging = node.dataset.id; node.classList.add("dragging"); }); node.addEventListener("dragend", () => { state.dragging = null; node.classList.remove("dragging"); });
    node.addEventListener("dragover", (event) => event.preventDefault()); node.addEventListener("drop", (event) => { event.preventDefault(); if (!state.dragging || state.dragging === node.dataset.id) return; const from = state.current.blocks.findIndex((block) => block.id === state.dragging), to = state.current.blocks.findIndex((block) => block.id === node.dataset.id); const [block] = state.current.blocks.splice(from, 1); state.current.blocks.splice(to, 0, block); renderBlocks(); markDirty(); });
  }

  function slashCommand(event) { if (event.key === "/" && !event.currentTarget.value.trim()) { event.preventDefault(); state.current.blocks = collect().blocks; $("block-menu").hidden = false; $("block-menu").querySelector("button")?.focus(); } }
  function addBlock(type) { state.current = collect(); state.current.blocks.push(makeBlock(type)); renderBlocks(); $("block-menu").hidden = true; markDirty(); requestAnimationFrame(() => $("blocks").lastElementChild?.querySelector("textarea,input")?.focus()); }

  async function uploadFiles(files, target = state.uploadTarget) {
    const images = [...files].filter((file) => file.type.startsWith("image/")); if (!images.length) return;
    state.busy = true; status("Saving photos…");
    try {
      for (const file of images) {
        const result = await api("upload", file, { raw: true, headers: { "Content-Type": file.type, "X-Content-Id": state.current.id, "X-Filename": encodeURIComponent(file.name) } });
        state.current.media.push(result.media);
        if (target === "post") state.current.imageIds.push(result.media.id);
        else if (target === "cover") state.current.coverMediaId = result.media.id;
        else if (target.startsWith("block:")) { const block = state.current.blocks.find((item) => item.id === target.split(":")[1]); if (block) block.mediaId = result.media.id; }
        else if (target.startsWith("gallery:")) { const block = state.current.blocks.find((item) => item.id === target.split(":")[1]); if (block) (block.mediaIds ||= []).push(result.media.id); }
      }
      renderPostMedia(); renderCover(); renderBlocks(); state.dirty = true; state.busy = false; await saveDraft();
    } catch (error) { status(error.message); }
    finally { state.busy = false; $("photo-input").value = ""; }
  }

  function mediaEditor(item, index) {
    const card = document.createElement("article"); card.className = "media-card"; card.draggable = true; card.dataset.id = item.id;
    const image = document.createElement("img"); image.src = mediaSrc(item); image.alt = item.alt || "";
    const controls = document.createElement("div"); controls.className = "media-card-controls";
    [["←", -1], ["→", 1]].forEach(([label, delta]) => { const button = controlButton(label, `Move image ${delta < 0 ? "left" : "right"}`); button.addEventListener("click", () => { const next = Math.max(0, Math.min(state.current.imageIds.length - 1, index + delta)); const [id] = state.current.imageIds.splice(index, 1); state.current.imageIds.splice(next, 0, id); renderPostMedia(); markDirty(); }); controls.append(button); });
    const remove = controlButton("Remove", "Remove image"); remove.addEventListener("click", async () => { state.current.imageIds = state.current.imageIds.filter((id) => id !== item.id); state.current.media = state.current.media.filter((media) => media.id !== item.id); renderPostMedia(); markDirty(); try { await api("delete-media", { ...collect(), storedName: item.storedName }); } catch {} }); controls.append(remove);
    const fields = document.createElement("div"); fields.className = "media-card-fields"; const alt = field("input", item.alt, "Alt text"); const caption = field("input", item.caption, "Caption (optional)"); alt.addEventListener("input", () => item.alt = alt.value); caption.addEventListener("input", () => item.caption = caption.value); fields.append(alt, caption); card.addEventListener("dragstart",()=>state.dragging=item.id); card.addEventListener("dragover",(event)=>event.preventDefault()); card.addEventListener("drop",(event)=>{event.preventDefault();const from=state.current.imageIds.indexOf(state.dragging),to=state.current.imageIds.indexOf(item.id);if(from>=0&&to>=0){const [id]=state.current.imageIds.splice(from,1);state.current.imageIds.splice(to,0,id);renderPostMedia();markDirty();}}); card.append(image, controls, fields); return card;
  }
  function renderPostMedia() { const grid = $("post-media"); grid.replaceChildren(); state.current.imageIds.forEach((id, index) => { const item = mediaItem(id); if (item) grid.append(mediaEditor(item, index)); }); }
  function renderCover() { const slot = $("cover-slot"); slot.replaceChildren(); const item = mediaItem(state.current.coverMediaId); if (!item) return; const card=document.createElement("article");card.className="media-card";const image=document.createElement("img");image.src=mediaSrc(item);image.alt=item.alt||"";const alt=field("input",item.alt,"Cover alt text"),caption=field("input",item.caption,"Cover caption (optional)");alt.addEventListener("input",()=>item.alt=alt.value);caption.addEventListener("input",()=>item.caption=caption.value);const fields=document.createElement("div");fields.className="media-card-fields";fields.append(alt,caption);const remove=controlButton("Remove cover","Remove cover");remove.addEventListener("click",()=>{state.current.coverMediaId="";renderCover();markDirty();});card.append(image,fields,remove);slot.append(card); }

  async function renderPreview() { state.current = collect(); status("Preparing preview…"); try { const result = await api("preview", state.current); $("preview").innerHTML = result.html; status(state.dirty ? "Unsaved changes" : "Saved"); } catch (error) { status(error.message); } }
  async function loadHistory() { const result = await api(`history?id=${encodeURIComponent(state.current.id)}`); $("history").replaceChildren(...(result.history.length ? result.history.map((entry) => { const p = document.createElement("p"); p.textContent = `${entry.date} · ${entry.commit} · ${entry.message}`; return p; }) : [Object.assign(document.createElement("p"), { textContent: "Published revisions will appear here through Git history." })])); }

  async function publish() {
    if (state.busy) return; state.current = collect(); state.busy = true; disable(true); progress("Publishing… · Saving content · Processing images"); status("Publishing…");
    try {
      const result = await api("publish", state.current); state.current = result.post; state.dirty = false; refreshLocalRecord(result.post); progress(result.state === "pushed" ? "✓ Saved · ✓ Images · ✓ Validated · ✓ Generated · ✓ Committed · ✓ Pushed · ◌ Deploying" : "✓ Saved · ✓ Images · ✓ Validated · ✓ Generated (dry run)"); status(result.message);
      if (result.unrelated?.length) status(`${result.message} Unrelated repository changes were left untouched.`);
      if (result.state === "pushed") pollDeployment(result); $("publish").textContent = "Publish update"; $("unpublish").hidden = false;
    } catch (error) { progress("Publishing stopped"); status(error.message); }
    finally { state.busy = false; disable(false); }
  }
  async function pollDeployment(result, attempts = 0) {
    if (attempts > 30) { progress("✓ Pushed · Deployment status timed out"); status("The push succeeded, but BA Writer could not confirm the live deployment. Check GitHub Pages."); return; }
    setTimeout(async () => { try { const check = await api(`deploy-status?url=${encodeURIComponent(result.liveUrl)}&fingerprint=${result.fingerprint}`); if (check.state === "live") { progress("✓ Saved · ✓ Images · ✓ Generated · ✓ Pushed · ✓ Live"); status("Live"); const link = document.createElement("a"); link.href = result.liveUrl; link.target = "_blank"; link.rel = "noopener"; link.textContent = "View live post ↗"; $("publish-progress").append(" · ", link); } else { progress("✓ Pushed · ◌ Deploying"); pollDeployment(result, attempts + 1); } } catch { pollDeployment(result, attempts + 1); } }, attempts < 4 ? 3000 : 10000);
  }
  function disable(value) { document.querySelectorAll("#content-form button, #content-form input, #content-form textarea, #content-form select").forEach((control) => control.disabled = value); }

  function autoSize(area) { area.style.height = "auto"; area.style.height = `${area.scrollHeight}px`; }
  function autoSizeAll() { document.querySelectorAll("textarea").forEach(autoSize); }
  document.addEventListener("input", (event) => { if (event.target.matches("textarea")) autoSize(event.target); if (event.target.closest("#content-form")) markDirty(); });
  document.addEventListener("keydown", (event) => {
    if (!(event.metaKey || event.ctrlKey)) return; const target = event.target; if (!target.matches("textarea,input")) return;
    if (["b", "i", "k"].includes(event.key.toLowerCase()) && target.matches("textarea")) { event.preventDefault(); const map = { b: ["**", "**"], i: ["*", "*"], k: ["[", "](https://)"] }; const [before, after] = map[event.key.toLowerCase()], start = target.selectionStart, end = target.selectionEnd, selected = target.value.slice(start, end) || "text"; target.setRangeText(before + selected + after, start, end, "end"); target.dispatchEvent(new Event("input", { bubbles: true })); }
  });
  document.addEventListener("paste", (event) => { const files = [...event.clipboardData.files].filter((file) => file.type.startsWith("image/")); if (files.length && !state.busy) { event.preventDefault(); uploadFiles(files, state.current.type === "post" ? "post" : "gallery:" + (state.current.blocks.find((block) => block.type === "gallery")?.id || (() => { const block = makeBlock("gallery"); state.current.blocks.push(block); return block.id; })())); } });
  document.addEventListener("dragover", (event) => { if ([...event.dataTransfer.types].includes("Files")) event.preventDefault(); });
  document.addEventListener("drop", (event) => { const files = [...event.dataTransfer.files].filter((file) => file.type.startsWith("image/")); if (files.length && !event.target.closest(".editor-block")) { event.preventDefault(); uploadFiles(files, state.current.type === "post" ? "post" : "cover"); } });

  document.querySelectorAll("[data-mode]").forEach((button) => button.addEventListener("click", () => setMode(button.dataset.mode, true)));
  document.querySelectorAll("[data-view]").forEach((button) => button.addEventListener("click", () => setView(button.dataset.view)));
  document.querySelectorAll("[data-photo]").forEach((button) => button.addEventListener("click", () => { state.uploadTarget = button.dataset.target || "post"; $("photo-input").multiple = state.uploadTarget === "post"; $("photo-input").click(); }));
  $("photo-input").addEventListener("change", () => uploadFiles($("photo-input").files));
  $("add-original").addEventListener("click", () => { $("post-original-wrap").hidden = false; $("post-original").focus(); });
  $("add-link").addEventListener("click", () => { $("post-link-wrap").hidden = false; $("post-link").focus(); });
  $("open-settings").addEventListener("click", () => $("settings").hidden = false); $("close-settings").addEventListener("click", () => $("settings").hidden = true);
  $("back-library").addEventListener("click", async () => { await saveDraft(); switchScreen("library"); });
  $("new-post").addEventListener("click", () => openRecord(blank("post")));
  $("new-article").addEventListener("click", () => openRecord(blank("article")));
  $("publish").addEventListener("click", publish);
  $("unpublish").addEventListener("click", async () => { if (!confirm("Remove this writing from the public Blog and keep it as a private draft?")) return; try { const result = await api("unpublish", collect()); state.current = result.post; refreshLocalRecord(result.post); status(result.message); progress(result.state === "pushed" ? "✓ Unpublish pushed · ◌ Deploying" : "✓ Unpublished locally"); $("unpublish").hidden = true; $("delete").hidden = false; } catch (error) { status(error.message); } });
  $("delete").addEventListener("click", async () => { if (!confirm("Delete this private draft and its local images? This cannot be undone.")) return; try { await api("delete", collect()); state.posts = state.posts.filter((item) => item.id !== state.current.id); switchScreen("library"); status("Draft deleted"); } catch (error) { status(error.message); } });
  $("add-block").addEventListener("click", () => $("block-menu").hidden = !$("block-menu").hidden);
  blockTypes.forEach(([type, label]) => { const button = document.createElement("button"); button.type = "button"; button.textContent = label; button.addEventListener("click", () => addBlock(type)); $("block-menu").append(button); });
  $("content-form").addEventListener("submit", (event) => event.preventDefault());
  window.addEventListener("beforeunload", (event) => { if (state.dirty) { event.preventDefault(); event.returnValue = ""; } });

  async function start() {
    const result = await api("posts"); state.posts = result.posts; state.push = result.push; $("login").hidden = true; $("workspace").hidden = false; status(result.push ? `Ready · publishing to ${result.branch}` : "Ready · dry run mode"); switchScreen("library");
  }
  $("login-form").addEventListener("submit", async (event) => { event.preventDefault(); try { await api("login", { password: $("password").value }); $("password").value = ""; history.replaceState(null, "", "/writer/"); await start(); } catch (error) { status(error.message); } });
  const token = new URL(location.href).searchParams.get("token");
  if (token) api("login", { password: token }).then(() => { history.replaceState(null, "", "/writer/"); return start(); }).catch(() => { $("login").hidden = false; status("Enter the Writer password"); });
  else start().catch(() => { $("login").hidden = false; status("Enter the Writer password"); });
})();
