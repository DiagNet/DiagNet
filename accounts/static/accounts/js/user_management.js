document.addEventListener('DOMContentLoaded', () => {
	const userCreateModal = document.getElementById('userCreateModal');
	const userDetailModal = document.getElementById('userDetailModal');
	const userEditModal = document.getElementById('userEditModal');
	const userPasswordModal = document.getElementById('userPasswordModal');

	// View user details buttons
	document.body.addEventListener('click', (e) => {
		const detailBtn = e.target.closest('.detail-user-btn');
		if (detailBtn) {
			const userId = detailBtn.dataset.userId;
			const modalBody = document.getElementById('userDetailModalBody');
			htmx.ajax('GET', `/accounts/manage/users/${userId}/`, { target: modalBody });
			const modal = new bootstrap.Modal(userDetailModal);
			modal.show();
		}
	});

	// Edit user buttons
	document.body.addEventListener('click', (e) => {
		const editBtn = e.target.closest('.edit-user-btn');
		if (editBtn) {
			const userId = editBtn.dataset.userId;
			const modalBody = document.getElementById('userEditModalBody');
			htmx.ajax('GET', `/accounts/manage/users/${userId}/edit/`, { target: modalBody });
			const modal = new bootstrap.Modal(userEditModal);
			modal.show();
		}
	});

	// Password change buttons
	document.body.addEventListener('click', (e) => {
		const passBtn = e.target.closest('.password-user-btn');
		if (passBtn) {
			const userId = passBtn.dataset.userId;
			const modalBody = document.getElementById('userPasswordModalBody');
			htmx.ajax('GET', `/accounts/manage/users/${userId}/password/`, { target: modalBody });
			const modal = new bootstrap.Modal(userPasswordModal);
			modal.show();
		}
	});

	// Close modals on successful HTMX request (204 response)
	document.body.addEventListener('htmx:beforeSwap', (e) => {
		if (e.detail.xhr.status === 204) {
			// Close all user modals
			[userCreateModal, userDetailModal, userEditModal, userPasswordModal].forEach(modalEl => {
				if (modalEl) {
					const modal = bootstrap.Modal.getInstance(modalEl);
					if (modal) modal.hide();
				}
			});
		}
	});

	// Refresh table on userCreated or usersRefresh events
	document.body.addEventListener('userCreated', () => {
		htmx.trigger('#user-table', 'refresh');
	});

	document.body.addEventListener('usersRefresh', () => {
		htmx.trigger('#user-table', 'refresh');
	});
});
