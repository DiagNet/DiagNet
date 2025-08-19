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
