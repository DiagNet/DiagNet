const singleLineInputTemplate = document.getElementById('parameterInputTemplate');

/** Displays a single line input field. */
class SingleLineInputField extends Parameter_field {
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
            this.datatypeBadges[i].textContent = fetchDatatypeValueInfo(parameterDatatypes[i]);
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
        const result = handleCheckDataType(this, this.parameter['type']); // handle_datatypes.js
        this.updateBadgesForParametersDependentOnThis();
        return result;
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
        if (this.field) this.field.addEventListener('input',callback);
    }

}