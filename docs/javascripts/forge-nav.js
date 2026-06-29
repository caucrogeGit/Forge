/* DOCS-NAV-LANDING-REPLICA-001
   Comportement des menus déroulants de la barre de navigation de la doc
   (réplique de la landing) : ouverture au clic, fermeture au clic extérieur
   et à la touche Échap. Le survol est géré en CSS. */
document.addEventListener("DOMContentLoaded", () => {
  const dropdowns = document.querySelectorAll(".forge-nav [data-dropdown]");
  if (!dropdowns.length) return;

  function closeAll() {
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
      closeAll();
      if (!wasOpen) {
        item.classList.add("is-open");
        trigger.setAttribute("aria-expanded", "true");
      }
    });
  });

  document.addEventListener("click", (event) => {
    if (!event.target.closest("[data-dropdown]")) closeAll();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeAll();
  });
});
