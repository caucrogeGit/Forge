// Configuration MathJax pour l'extension pymdownx.arithmatex (mode generic).
// Les formules sont émises dans des éléments de classe « arithmatex », avec
// les délimiteurs \( \) en ligne et \[ \] en bloc.
window.MathJax = {
  tex: {
    inlineMath: [["\\(", "\\)"]],
    displayMath: [["\\[", "\\]"]],
    processEscapes: true,
    processEnvironments: true
  },
  options: {
    ignoreHtmlClass: ".*|",
    processHtmlClass: "arithmatex"
  }
};

// Re-typeser à chaque navigation instantanée du thème Material.
document$.subscribe(() => {
  MathJax.startup.output.clearCache();
  MathJax.typesetClear();
  MathJax.texReset();
  MathJax.typesetPromise();
});
