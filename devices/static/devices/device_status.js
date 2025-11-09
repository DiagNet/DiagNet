document.addEventListener("DOMContentLoaded", function () {
  const checkAllBtn = document.getElementById("check-all-devices");
  if (checkAllBtn) {
    checkAllBtn.addEventListener("click", function () {
      document.querySelectorAll("button.device-check").forEach((btn) => {
        btn.click();
      });
    });
  }
});

document.body.addEventListener("click", (event) => {
  const button = event.target.closest("button.device-check");
  if (!button) return;

  const row = button.closest("tr");
  const statusCell = row?.querySelector(".connection-status");
  if (statusCell) statusCell.innerHTML = "";
});
