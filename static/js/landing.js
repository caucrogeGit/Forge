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
