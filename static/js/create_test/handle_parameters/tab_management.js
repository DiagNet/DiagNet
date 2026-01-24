/** Makes tab navigation unavailable for hidden tabs. */
function updateTabContentAccessibility() {
  document.activeElement.blur();

  const navs = document.querySelectorAll(".create-popup-nav");
  const panes = document.querySelectorAll(".create-popup-content");

  const tabMap = new Map();

  for (let i = 0; i < navs.length; i++) {
    tabMap.set(navs[i], panes[i]);
  }

  navs.forEach((nav_pane) => {
    const isActive = nav_pane.classList.contains("active"); // or whichever logic you use for current pane
    // focusable elements
    const focusable = tabMap
      .get(nav_pane)
      .querySelectorAll("input, button, select, textarea, a");

    focusable.forEach((el) => {
      if (isActive) {
        el.setAttribute("tabindex", "0"); // allow tabbing
      } else {
        el.setAttribute("tabindex", "-1"); // skip tabbing
      }
    });
  });
}

updateTabContentAccessibility();
