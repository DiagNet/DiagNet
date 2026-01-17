document.addEventListener('DOMContentLoaded', () => {
	const groupCreateModal = document.getElementById('groupCreateModal');
	const groupDetailModal = document.getElementById('groupDetailModal');
	const groupMembershipModal = document.getElementById('groupMembershipModal');

	// View group details buttons
	document.body.addEventListener('click', (e) => {
		const detailBtn = e.target.closest('.detail-group-btn');
		if (detailBtn) {
			const groupId = detailBtn.dataset.groupId;
			const modalBody = document.getElementById('groupDetailModalBody');
			htmx.ajax('GET', `/accounts/manage/groups/${groupId}/`, { target: modalBody });
			const modal = new bootstrap.Modal(groupDetailModal);
			modal.show();
		}
	});

	// Manage membership buttons
	document.body.addEventListener('click', (e) => {
		const memberBtn = e.target.closest('.membership-group-btn');
		if (memberBtn) {
			const groupId = memberBtn.dataset.groupId;
			const modalBody = document.getElementById('groupMembershipModalBody');
			htmx.ajax('GET', `/accounts/manage/groups/${groupId}/members/`, { target: modalBody });
			const modal = new bootstrap.Modal(groupMembershipModal);
			modal.show();
		}
	});

	// Close modals on successful HTMX request (204 response)
	document.body.addEventListener('htmx:beforeSwap', (e) => {
		if (e.detail.xhr.status === 204) {
			// Close all group modals
			[groupCreateModal, groupDetailModal, groupMembershipModal].forEach(modalEl => {
				if (modalEl) {
					const modal = bootstrap.Modal.getInstance(modalEl);
					if (modal) modal.hide();
				}
			});
		}
	});

	// Refresh table on groupCreated or groupsRefresh events
	document.body.addEventListener('groupCreated', () => {
		htmx.trigger('#group-table', 'refresh');
	});

	document.body.addEventListener('groupsRefresh', () => {
		htmx.trigger('#group-table', 'refresh');
	});
});
