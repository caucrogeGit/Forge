/* DOCS-NAV-LANDING-REPLICA-001
   Comportement de la barre de navigation de la doc (réplique de la landing).
   - Menus déroulants : ouverture au clic, fermeture au clic extérieur / Échap
     (le survol est géré en CSS).
   - Recherche Material : fermeture fiable au clic en dehors et à Échap (le header
     custom ne reproduit pas le mécanisme d'overlay natif). */
document.addEventListener("DOMContentLoaded", () => {

  // ── Menus déroulants ────────────────────────────────────────────────────────
  const dropdowns = document.querySelectorAll(".forge-nav [data-dropdown]");

  function closeAllDropdowns() {
    dropdowns.forEach((d) => {
      d.classList.remove("is-open");
      const t = d.querySelector(".forge-nav-trigger");
      if (t) t.setAttribute("aria-expanded", "false");
    });
  }

  dropdowns.forEach((item) => {
    const trigger = item.querySelector(".forge-nav-trigger");
    if (!trigger) return;
    trigger.addEventListener("click", (event) => {
      event.preventDefault();
      const wasOpen = item.classList.contains("is-open");
      closeAllDropdowns();
      if (!wasOpen) {
        item.classList.add("is-open");
        trigger.setAttribute("aria-expanded", "true");
      }
    });
  });

  // ── Recherche Material : fermeture au clic extérieur / Échap ─────────────────
  const searchToggle = document.getElementById("__search");
  const search = document.querySelector(".md-search");

  function closeSearch() {
    if (!searchToggle) return;
    if (searchToggle.checked) {
      searchToggle.checked = false;
      searchToggle.dispatchEvent(new Event("change", { bubbles: true }));
    }
    const input = search && search.querySelector(".md-search__input");
    if (input) input.blur();
  }

  // ── Fermetures globales (clic extérieur, Échap) ──────────────────────────────
  document.addEventListener("click", (event) => {
    if (!event.target.closest("[data-dropdown]")) closeAllDropdowns();
    if (search && !event.target.closest(".md-search")) closeSearch();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeAllDropdowns();
      closeSearch();
    }
  });
});
