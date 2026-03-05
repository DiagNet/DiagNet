document.body.addEventListener("click", (event) => {
  const button = event.target.closest("button.device-check");
  if (!button) return;

  const row = button.closest("tr");
  const statusCell = row?.querySelector(".connection-status");
  if (statusCell) statusCell.innerHTML = "";
});
