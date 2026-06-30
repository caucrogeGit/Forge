/* DOCS-NAV-UNIVERSAL-001
   Comportement de la navigation universelle de la doc (réplique de la landing) :
   - menus déroulants (Documentation, Modules) : ouverture au clic (survol en CSS) ;
   - hamburger (petit écran) : ouvre/ferme le menu, FERMÉ par défaut ;
   - fermeture au clic sur un lien, au clic extérieur et à la touche Échap. */
document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.getElementById("forge-nav-toggle");
  const links = document.getElementById("forge-nav-links");
  const dropdowns = document.querySelectorAll(".forge-nav [data-dropdown]");

  function closeDropdowns() {
    dropdowns.forEach((d) => {
      d.classList.remove("is-open");
      const t = d.querySelector(".forge-nav-trigger");
      if (t) t.setAttribute("aria-expanded", "false");
    });
  }
  function closeMenu() {
    if (links) links.classList.remove("is-open");
    if (toggle) toggle.setAttribute("aria-expanded", "false");
  }

  dropdowns.forEach((item) => {
    const trigger = item.querySelector(".forge-nav-trigger");
    if (!trigger) return;
    trigger.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      const wasOpen = item.classList.contains("is-open");
      closeDropdowns();
      if (!wasOpen) {
        item.classList.add("is-open");
        trigger.setAttribute("aria-expanded", "true");
      }
    });
  });

  if (toggle && links) {
    toggle.addEventListener("click", (event) => {
      event.stopPropagation();
      if (links.classList.contains("is-open")) {
        closeMenu();
      } else {
        links.classList.add("is-open");
        toggle.setAttribute("aria-expanded", "true");
      }
    });
    links.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", () => {
        closeMenu();
        closeDropdowns();
      });
    });
  }

  document.addEventListener("click", (event) => {
    if (!event.target.closest("[data-dropdown]")) closeDropdowns();
    if (
      toggle && links &&
      !event.target.closest("#forge-nav-links") &&
      !event.target.closest("#forge-nav-toggle")
    ) {
      closeMenu();
    }
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeDropdowns();
      closeMenu();
    }
  });
});
