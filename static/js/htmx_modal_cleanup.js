window.window._htmxClosedModals = false;

document.addEventListener("htmx:beforeSwap", (e) => {
  const target = e.detail.target;
  if (!target) return;

  const openModals = Array.from(target.querySelectorAll(".modal.show"));
  if (target.classList.contains("modal") && target.classList.contains("show")) {
    openModals.push(target);
  }

  if (openModals.length > 0) {
    window._htmxClosedModals = true;
    openModals.forEach((m) => bootstrap.Modal.getInstance(m)?.hide());
    const triggerEl = e.detail.requestConfig?.elt || e.detail.elt;
    const currentSwap =
      triggerEl?.closest("[hx-swap]")?.getAttribute("hx-swap") || "innerHTML";
    e.detail.swapOverride = `${currentSwap} swap:300ms`;
  }
});

document.addEventListener("htmx:afterSwap", () => {
  if (!window._htmxClosedModals) return;
  window._htmxClosedModals = false;

  if (document.querySelectorAll(".modal.show").length === 0) {
    document.querySelectorAll(".modal-backdrop").forEach((b) => b.remove());
    document.body.classList.remove("modal-open");
    document.body.style.overflow = "";
    document.body.style.paddingRight = "";
  }
});
