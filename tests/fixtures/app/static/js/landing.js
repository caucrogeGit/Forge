document.addEventListener("DOMContentLoaded", () => {

  // ── Tabs ──────────────────────────────────────────────────────────────────
  document.querySelectorAll("[data-tabs]").forEach((container) => {
    const buttons = container.querySelectorAll("[data-tab-btn]");
    const panels  = container.querySelectorAll("[data-tab-panel]");

    function activate(idx) {
      buttons.forEach((b, i) => b.classList.toggle("tab-active", i === idx));
      panels.forEach((p, i)  => p.classList.toggle("hidden",    i !== idx));
    }

    buttons.forEach((btn, i) => btn.addEventListener("click", () => activate(i)));
    activate(0);
  });

  // ── Nav hamburger (< 1098px) ────────────────────────────────────────────────
  const navToggle = document.getElementById("nav-toggle");
  const navLinks  = document.getElementById("nav-links");
  if (navToggle && navLinks) {
    const root = document.documentElement;
    // Padding vertical du panneau ouvert (.landing-nav-links.is-open : 1.5rem
    // haut + bas = 48px). Ajouté à la hauteur du contenu mesurée fermée.
    const PANEL_VPAD = 48;

    function openMenu() {
      // scrollHeight (fermé) = hauteur de la colonne de liens, padding vertical 0.
      const h = navLinks.scrollHeight + PANEL_VPAD;
      // --nav-push pilote la hauteur du panneau ET la descente du hero : les
      // deux s'animent ensemble, donc le menu ne recouvre jamais le hero.
      root.style.setProperty("--nav-push", h + "px");
      navLinks.classList.add("is-open");
      navToggle.setAttribute("aria-expanded", "true");
    }

    function closeMenu() {
      root.style.setProperty("--nav-push", "0px");
      navLinks.classList.remove("is-open");
      navToggle.setAttribute("aria-expanded", "false");
    }

    navToggle.addEventListener("click", () => {
      if (navLinks.classList.contains("is-open")) closeMenu();
      else openMenu();
    });
    navLinks.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", closeMenu);
    });
  }

  // ── Copy buttons ──────────────────────────────────────────────────────────
  document.querySelectorAll("[data-copy]").forEach((btn) => {
    btn.addEventListener("click", () => {
      navigator.clipboard.writeText(btn.dataset.copy).catch(() => {});
      const orig = btn.textContent;
      btn.textContent = "✓ Copié";
      setTimeout(() => { btn.textContent = orig; }, 2000);
    });
  });

});
