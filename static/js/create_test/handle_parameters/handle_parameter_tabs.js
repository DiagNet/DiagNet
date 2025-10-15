const parameter_tabs = document.querySelectorAll('.tab-btn');
const contents = document.querySelectorAll('.tab-content > .param-tab-pane');

parameter_tabs.forEach(tab => {
    tab.addEventListener('click', () => {

        // Remove active and show from all tabs
        parameter_tabs.forEach(t => t.classList.remove('active'));
        contents.forEach(c => c.classList.remove('active', 'show'));

        // Activate the clicked tab and its pane
        tab.classList.add('active');
        const target = tab.dataset.tab;
        const pane = document.getElementById(target);
        if (pane) {
            pane.classList.add('active', 'show'); // <-- important
        }
    });
});
