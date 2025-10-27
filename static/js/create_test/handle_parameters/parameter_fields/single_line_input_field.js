const singleLineInputTemplate = document.getElementById('parameterInputTemplate');

// Info Template
const defaultParameterInfo = document.getElementById('RegularParameterInfo');

/** Displays a single line input field. */
class SingleLineInputField extends ParameterField {
    async createField() {
        this.container = this.loadTemplateContainer();
        this.field = this.container.querySelector('.param-input');

        let labelContact = this.getDisplayName();
        if (this.isRequired()) labelContact += this.requiredMark();
        this.container.querySelector('.param-label').innerHTML = labelContact;

        this.datatypeBadges =
            this.createDatatypeBadges(this.container.querySelector('.param-datatype'));

        return this.container;
    }

    // Template
    getTemplate() {
        return singleLineInputTemplate;
    }

    // Datatype Badges
    /**
     * Creates the number of datatype badges needed for this parameter.
     * @param {HTMLElement} templateNode The Template defining the badge.
     * @returns {Array<HTMLElement>} The Element with the number of needed badges.
     */
    createDatatypeBadges(templateNode) {
        let datatypes = this.getType();

        const badges = [templateNode];
        while (badges.length < datatypes.length) {
            const clone = templateNode.cloneNode(false);
            templateNode.after(clone);
            badges.push(clone);
        }

        return badges;
    }

    /** Loads the Datatypes of this parameter into the badges. */
    updateDatatypeBadges() {
        const parameterDatatypes = this.getType();
        for (let i = 0; i < parameterDatatypes.length; i++) {
            const datatype = parameterDatatypes[i];
            if (datatype.checkValidity()) {
                this.datatypeBadges[i].style.display = "";
                this.datatypeBadges[i].textContent = datatype.displayName();
            } else {
                this.datatypeBadges[i].style.display = "none";
            }
        }
    }

    // Field
    afterCreatingField() {
        super.afterCreatingField();
        this.updateDatatypeBadges(); // Update Badges after all parameters have been loaded.
    }

    getField() {
        return this.container;
    }

    getValue() {
        return this.field ? this.field.value : null;
    }

    clearValue() {
        if (this.field) this.field.value = "";
        this.triggerInputValidation();
    }

    isEmpty() {
        return this.field ? this.field.value.length === 0 : true;
    }

    changedFromEmptyToValue() {
        return this.field ? this.field.value.length === 1 : true;
    }

    enable() {
        if (this.field) {
            this.field.disabled = false;
            this.field.readOnly = false;
        }
    }

    disable() {
        if (this.field) {
            this.field.disabled = true;
            this.field.readOnly = true;
        }
    }

    // Datatype
    async checkDatatype() {
        const value = this.getValue();
        this.updateBadgesForParametersDependentOnThis();

        if (value.length === 0) {
            this.unknownDatatype();
            return DATATYPE_RESULT.UNKNOWN;
        }

        for (const datatype of this.getType()) {
            if (datatype.checkValidity() && datatype.check(value)) {
                this.correctDatatype();
                return DATATYPE_RESULT.SUCCESS;
            }
        }

        this.wrongDatatype();
        return DATATYPE_RESULT.FAIL;
    }

    unknownDatatype() {
        if (this.field) this.field.style.border = "";
    }

    correctDatatype() {
        if (this.field) this.field.style.border = "2px solid green";
    }

    wrongDatatype() {
        if (this.field) this.field.style.border = "2px solid red";
    }

    // Event Listeners
    dispatchEvent(event) {
        this.field.dispatchEvent(event);
    }

    onFocus(callback) {
        this.container.addEventListener('mousedown', callback);
    }

    onChange(callback) {
        if (this.field) this.field.addEventListener('input', callback);
    }

    // Info
    getInfo(globalTestClass) {
        const container = defaultParameterInfo.content.cloneNode(true).querySelector('div');

        // Parent
        const parent = this.getParent();
        container.querySelector('#infoTabParentName').textContent = parent ? parent.getDisplayName() : globalTestClass;
        container.querySelector('#infoTabParentType').textContent = parent ? "List" : "TestCase";

        // Datatypes
        const datatypeTemplateContainer = this.container.querySelector('.datatypeContainer');
        const datatypeContainers = this.getDatatypeInfo(this.getType(), datatypeTemplateContainer);


        return container;
    }

    /**
     * Creates a Container for each given datatype.
     * @param {Array<string>} datatypes An array of datatypes.
     * @param {HTMLElement} templateContainer The container that defines a datatype.
     * @returns {Array<HTMLElement>} An array of containers for each datatype.
     */
    getDatatypeInfo(datatypes, templateContainer) {
        const containers = [templateContainer];
        for (let i = 1; i < datatypes.length; i++) {
            containers.push(templateContainer.cloneNode(true));
        }

        for (let i = 0; i < datatypes.length; i++) {
            const datatype = datatypes[i];
            const container = containers[i];


        }

        return containers;
    }

    /**
     * Puts datatype info into the given container.
     * @param container The container to "decorate".
     * @param datatype The name of the datatype.
     */
    decorateDatatypeContainer(container, datatype) {
        container.querySelector('.infoTabDatatypeName').textContent = datatype;

    }
}