/* DOCS-NAV-LANDING-REPLICA-001
   Menus déroulants de la barre de navigation de la doc (réplique de la landing) :
   ouverture au clic, fermeture au clic extérieur et à Échap (le survol est géré
   en CSS). La recherche est laissée entièrement au composant natif de Material. */
document.addEventListener("DOMContentLoaded", () => {
  const dropdowns = document.querySelectorAll(".forge-nav [data-dropdown]");
  if (!dropdowns.length) return;

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

  document.addEventListener("click", (event) => {
    if (!event.target.closest("[data-dropdown]")) closeAllDropdowns();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeAllDropdowns();
  });
});
