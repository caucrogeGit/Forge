/* DOCS-NAV-SINGLE-BAR-001
   Hamburger de la barre de navigation (petit écran) : ouvre/ferme le panneau des
   onglets de navigation (Cœur de Forge, Opt-ins officiels). Fermé par défaut ;
   l'utilisateur l'ouvre au clic. Fermeture au clic sur un lien, au clic extérieur
   ou à la touche Échap. */
document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.getElementById("forge-nav-toggle");
  const tabs = document.getElementById("forge-tabs");
  if (!toggle || !tabs) return;

  function close() {
    tabs.classList.remove("is-open");
    toggle.setAttribute("aria-expanded", "false");
  }
  function open() {
    tabs.classList.add("is-open");
    toggle.setAttribute("aria-expanded", "true");
  }

  toggle.addEventListener("click", (event) => {
    event.stopPropagation();
    if (tabs.classList.contains("is-open")) close();
    else open();
  });

  tabs.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", close);
  });

  document.addEventListener("click", (event) => {
    if (!event.target.closest("#forge-tabs") && !event.target.closest("#forge-nav-toggle")) {
      close();
    }
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") close();
  });
});
