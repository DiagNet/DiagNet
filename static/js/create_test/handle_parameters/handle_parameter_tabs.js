const parameter_tabs = document.querySelectorAll('.tab-btn');
const contents = document.querySelectorAll('.tab-content > div');

parameter_tabs.forEach(tab => {
    tab.addEventListener('click', () => {

        parameter_tabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        const target = tab.dataset.tab;
        contents.forEach(c => {
            c.id === target ? c.classList.add('active') : c.classList.remove('active');
        });
    });
});