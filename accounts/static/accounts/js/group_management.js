document.addEventListener("DOMContentLoaded", () => {
  const groupCreateModal = document.getElementById("groupCreateModal");
  const groupDetailModal = document.getElementById("groupDetailModal");
  const groupMembershipModal = document.getElementById("groupMembershipModal");

  // Get URL patterns from data attributes
  const urlsEl = document.getElementById("group-urls");
  const urls = {
    detail: urlsEl.dataset.detailUrl,
    membership: urlsEl.dataset.membershipUrl,
    create: urlsEl.dataset.createUrl,
  };

  // Helper function to replace placeholder ID in URL pattern
  const buildUrl = (pattern, id) => pattern.replace("/0/", `/${id}/`);

  // Reset creation modal when opened
  groupCreateModal.addEventListener("show.bs.modal", () => {
    const modalBody = groupCreateModal.querySelector(".modal-body");
    htmx.ajax("GET", urls.create, { target: modalBody });
  });

  // View group details buttons
  document.body.addEventListener("click", (e) => {
    const detailBtn = e.target.closest(".detail-group-btn");
    if (detailBtn) {
      const groupId = detailBtn.dataset.groupId;
      const modalBody = document.getElementById("groupDetailModalBody");
      htmx.ajax("GET", buildUrl(urls.detail, groupId), { target: modalBody });
      const modal = new bootstrap.Modal(groupDetailModal);
      modal.show();
    }
  });

  // Manage membership buttons
  document.body.addEventListener("click", (e) => {
    const memberBtn = e.target.closest(".membership-group-btn");
    if (memberBtn) {
      const groupId = memberBtn.dataset.groupId;
      const modalBody = document.getElementById("groupMembershipModalBody");
      htmx.ajax("GET", buildUrl(urls.membership, groupId), {
        target: modalBody,
      });
      const modal = new bootstrap.Modal(groupMembershipModal);
      modal.show();
    }
  });

  // Close modals on successful HTMX request (204 response)
  document.body.addEventListener("htmx:beforeSwap", (e) => {
    if (e.detail.xhr.status === 204) {
      // Close all group modals
      [groupCreateModal, groupDetailModal, groupMembershipModal].forEach(
        (modalEl) => {
          if (modalEl) {
            const modal = bootstrap.Modal.getInstance(modalEl);
            if (modal) modal.hide();
          }
        },
      );
    }
  });

  // Refresh table on groupCreated or groupsRefresh events
  document.body.addEventListener("groupCreated", () => {
    htmx.trigger("#group-table", "refresh");
  });

  document.body.addEventListener("groupsRefresh", () => {
    htmx.trigger("#group-table", "refresh");
  });
});
