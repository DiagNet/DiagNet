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

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("button.device-check").forEach((button) => {
    button.addEventListener("click", () => {
      const row = button.closest("tr");
      const statusCell = row.querySelector(".connection-status");

      // Clear status and force spinner visible
      statusCell.innerHTML = "";
    });
  });
});
