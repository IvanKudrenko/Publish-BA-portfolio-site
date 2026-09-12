const header = document.querySelector(".site-header");
const nav = document.querySelector(".site-nav");
const navToggle = document.querySelector(".nav-toggle");
const navLinks = [...document.querySelectorAll(".nav-link")];
const navDestinations = [...document.querySelectorAll(".site-nav a")];
const projectMenus = [...document.querySelectorAll(".nav-projects")];
const homeLinks = [...document.querySelectorAll('a[href="#home"]')];
const revealItems = document.querySelectorAll("[data-reveal]");
const trackedSections = [...document.querySelectorAll("section[id], header[id]")];
const isRootSectionsPage = Boolean(document.getElementById("home"));
let lastSyncedHash = window.location.hash || "";
let sectionTrackingReady = false;

if (navToggle && nav) {
  navToggle.addEventListener("click", () => {
    const isOpen = nav.classList.toggle("is-open");
    navToggle.setAttribute("aria-expanded", String(isOpen));
  });

  navDestinations.forEach((link) => {
    link.addEventListener("click", () => {
      nav.classList.remove("is-open");
      navToggle.setAttribute("aria-expanded", "false");
      projectMenus.forEach((menu) => menu.removeAttribute("open"));
    });
  });

  window.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      nav.classList.remove("is-open");
      navToggle.setAttribute("aria-expanded", "false");
      projectMenus.forEach((menu) => menu.removeAttribute("open"));
    }
  });

  window.addEventListener("resize", () => {
    if (window.innerWidth > 880) {
      nav.classList.remove("is-open");
      navToggle.setAttribute("aria-expanded", "false");
    }
  });
}

document.addEventListener("click", (event) => {
  projectMenus.forEach((menu) => {
    if (!menu.contains(event.target)) {
      menu.removeAttribute("open");
    }
  });
});

homeLinks.forEach((link) => {
  link.addEventListener("click", (event) => {
    event.preventDefault();

    if (window.location.hash !== "#home") {
      history.replaceState(null, "", "#home");
      lastSyncedHash = "#home";
    }

    window.scrollTo({
      top: 0,
      behavior: "auto",
    });

    if (nav && navToggle) {
      nav.classList.remove("is-open");
      navToggle.setAttribute("aria-expanded", "false");
    }
  });
});

const updateHeaderState = () => {
  if (!header) return;
  header.classList.toggle("scrolled", window.scrollY > 18);
};

const syncSectionHash = (sectionId) => {
  if (!isRootSectionsPage || !sectionId || !sectionTrackingReady) return;

  const nextHash = `#${sectionId}`;
  if (window.location.hash === nextHash && lastSyncedHash === nextHash) return;

  history.replaceState(null, "", nextHash);
  lastSyncedHash = nextHash;
};

const updateActiveNavLink = () => {
  if (!trackedSections.length) return;

  const offset = window.innerHeight * 0.22;
  let currentId = trackedSections[0].dataset.nav || trackedSections[0].id;

  const isAtPageBottom =
    window.innerHeight + window.scrollY >=
    document.documentElement.scrollHeight - 4;

  if (isAtPageBottom) {
    const lastSection = trackedSections[trackedSections.length - 1];
    currentId = lastSection.dataset.nav || lastSection.id;
  } else {
    trackedSections.forEach((section) => {
      const top = section.getBoundingClientRect().top;
      if (top - offset <= 0) {
        currentId = section.dataset.nav || section.id;
      }
    });
  }

  navLinks.forEach((link) => {
    const href = link.getAttribute("href") || "";
    const trackedId = link.dataset.section || "";
    const isActive =
      trackedId === currentId ||
      href === `#${currentId}` ||
      href.endsWith(`#${currentId}`);
    link.classList.toggle("active", isActive);
  });

  syncSectionHash(currentId);
};

updateHeaderState();

requestAnimationFrame(() => {
  const initialSection = window.location.hash
    ? document.getElementById(window.location.hash.slice(1))
    : null;

  if (initialSection) {
    const previousScrollBehavior = document.documentElement.style.scrollBehavior;
    document.documentElement.style.scrollBehavior = "auto";
    const headerOffset = (header?.offsetHeight || 72) + 8;
    window.scrollTo(0, Math.max(0, initialSection.offsetTop - headerOffset));
    document.documentElement.style.scrollBehavior = previousScrollBehavior;
  }

  updateActiveNavLink();
  sectionTrackingReady = true;
});

const navigationEntry = performance.getEntriesByType("navigation")[0];
if (!window.location.hash && navigationEntry?.type !== "back_forward") {
  window.scrollTo(0, 0);
}

window.addEventListener("scroll", () => {
  updateHeaderState();
  updateActiveNavLink();
});

if ("IntersectionObserver" in window) {
  const revealObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          revealObserver.unobserve(entry.target);
        }
      });
    },
    {
      threshold: 0.14,
      rootMargin: "0px 0px -30px 0px",
    }
  );

  revealItems.forEach((item) => revealObserver.observe(item));
} else {
  revealItems.forEach((item) => item.classList.add("is-visible"));
}
