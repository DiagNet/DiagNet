const toastContainer = document.getElementById("toastContainer");

/**
 * Throws an Exception
 * @param message The message to display
 */
function throwException(message) {
    console.error(message)

    // Create toast element
    const toastEl = document.createElement("div");
    toastEl.className = "toast align-items-center text-bg-danger border-0";
    toastEl.setAttribute("role", "alert");
    toastEl.setAttribute("aria-live", "assertive");
    toastEl.setAttribute("aria-atomic", "true");

    toastEl.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">ERROR: ${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;

    toastContainer.appendChild(toastEl);

    // Initialize and show bootstrap toast
    const toast = new bootstrap.Toast(toastEl, { delay: 3000 });
    toast.show();

    // Remove from DOM after hidden
    toastEl.addEventListener('hidden.bs.toast', () => {
        toastEl.remove();
    });
}


const successToastEl = document.getElementById("successToast");
const successToastBody = document.getElementById("successToastBody");

/**
 * Shows a Success globally on the page.
 * @param message Message to display
 * @param duration the display duration
 */
function showSuccess(message, duration = 3000) {
    successToastBody.textContent = message;

    const toast = new bootstrap.Toast(successToastEl, { delay: duration });
    toast.show();
}