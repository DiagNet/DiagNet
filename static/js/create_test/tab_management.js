/** Makes tab navigation unavailable for hidden tabs. */
function updateTabContentAccessibility() {
    console.log(document.activeElement);
    document.activeElement.blur();

    const navs = document.querySelectorAll('.create-popup-nav');
    const panes = document.querySelectorAll('.create-popup-content');

    const tabMap = new Map();

    for (let i = 0; i < navs.length; i++) {
        tabMap.set(navs[i], panes[i]);
    }

    console.log("UPDATE");
    navs.forEach(nav_pane => {
        const isActive = nav_pane.classList.contains('active'); // or whichever logic you use for current pane
        // focusable elements
        const focusable = tabMap.get(nav_pane).querySelectorAll('input, button, select, textarea, a, [tabindex], div.active');

        focusable.forEach(el => {
            if (isActive) {
                console.log("ACTIVE " + el.placeholder);
                el.setAttribute('tabindex', '0'); // skip tabbing
            } else {
                el.setAttribute('tabindex', '-1'); // skip tabbing
            }
        });
    });
}

updateTabContentAccessibility();