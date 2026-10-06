(() => {
  const filterButtons = [...document.querySelectorAll("[data-filter]")];
  const rows = [...document.querySelectorAll("[data-blog-type]")];
  const empty = document.querySelector(".blog-filter-empty");
  const applyFilter = (filter) => {
    let visible = 0;
    rows.forEach((row) => {
      const show = filter === "all" || row.dataset.blogType === filter;
      row.hidden = !show;
      if (show) visible += 1;
    });
    filterButtons.forEach((button) => button.setAttribute("aria-pressed", String(button.dataset.filter === filter)));
    if (empty) empty.hidden = visible !== 0 || rows.length === 0 || filter === "all";
    const url = new URL(location.href);
    if (filter === "all") url.searchParams.delete("type");
    else url.searchParams.set("type", filter);
    history.replaceState(null, "", url);
  };
  filterButtons.forEach((button) => button.addEventListener("click", () => applyFilter(button.dataset.filter)));
  const initial = new URL(location.href).searchParams.get("type");
  applyFilter(["post", "article"].includes(initial) ? initial : "all");
  document.querySelector("[data-copy-link]")?.addEventListener("click", async (event) => {
    try {
      await navigator.clipboard.writeText(location.href);
      event.currentTarget.textContent = "Link copied";
    } catch {
      event.currentTarget.textContent = location.href;
    }
  });
})();
