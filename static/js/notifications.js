function createToast(message, level) {
  const toastContainer = document.getElementById("toast-container");
  const template = document.getElementById("toast-template");

  if (!toastContainer || !template) return;

  const clone = template.content.cloneNode(true);
  const toastEl = clone.querySelector(".toast");

  toastEl.classList.add(`text-bg-${level || "info"}`);
  toastEl.querySelector(".toast-body").textContent = message;

  toastContainer.appendChild(toastEl);

  if (typeof bootstrap !== "undefined") {
    const toast = new bootstrap.Toast(toastEl);
    toast.show();
  }

  toastEl.addEventListener("hidden.bs.toast", () => {
    toastEl.remove();
  });
}

document.body.addEventListener("showMessage", function (evt) {
  createToast(evt.detail.message, evt.detail.level);
});

document.addEventListener("DOMContentLoaded", function () {
  const toastContainer = document.getElementById("toast-container");
  if (!toastContainer) return;

  var toastElList = [].slice.call(toastContainer.querySelectorAll(".toast"));
  toastElList.forEach(function (toastEl) {
    if (typeof bootstrap !== "undefined") {
      var toast = new bootstrap.Toast(toastEl);
      toast.show();
    }
  });
});
