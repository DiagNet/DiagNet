function createToast(message, level) {
  const toastContainer = document.getElementById("toast-container");
  const template = document.getElementById("toast-template");

  if (!toastContainer || !template) return;

  // Clone the template
  const clone = template.content.cloneNode(true);
  const toastEl = clone.querySelector(".toast");

  // Add specific classes and content
  toastEl.classList.add(`text-bg-${level || "info"}`);
  toastEl.querySelector(".toast-body").textContent = message;

  toastContainer.appendChild(toastEl);

  const toast = new bootstrap.Toast(toastEl);
  toast.show();

  // Remove from DOM after hidden
  toastEl.addEventListener("hidden.bs.toast", () => {
    toastEl.remove();
  });
}

document.body.addEventListener("showMessage", function (evt) {
  createToast(evt.detail.message, evt.detail.level);
});

// Initialize existing toasts (e.g. from Django messages)
document.addEventListener("DOMContentLoaded", function () {
  var toastElList = [].slice.call(document.querySelectorAll(".toast"));
  var toastList = toastElList.map(function (toastEl) {
    return new bootstrap.Toast(toastEl);
  });
  toastList.forEach((toast) => toast.show());
});
