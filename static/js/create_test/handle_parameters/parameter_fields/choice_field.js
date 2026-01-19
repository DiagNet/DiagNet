const choiceInputTemplate = document.getElementById('choiceInputTemplate');

/** Displays a multiple choice input field. */
class ChoiceField extends ParameterField {
    async createField() {
        this.container = this.loadTemplateContainer();
        this.field = this.container.querySelector('.choice-select');

        let labelContact = this.getDisplayName();
        if (this.isRequired()) labelContact += this.requiredMark();
        this.container.querySelector('.choice-label').innerHTML = labelContact;


        const options = this.get('choices') || [];
        if (!options.length) throwException(`Choice Field "${this.getDisplayName()}" has no attribute "choices" or it's empty.`)

        const defaultChoice = this.get('default_choice');
        const emptyChoice = this.get('empty_choice');
        if (emptyChoice === "true") options.unshift(""); // add empty choice

        options.forEach(optionName => {
            const option = this.createOption(optionName);
            if (optionName === defaultChoice) option.selected = true;
            this.field.appendChild(option);
        });

        return this.container;
    }

    // Options
    /**
     * Creates an Option with the specified Name.
     * @param optionName the name of the option.
     * @returns {HTMLOptionElement} a newly created option Element.
     */
    createOption(optionName) {
        const option = document.createElement("option");
        option.value = optionName;
        option.textContent = optionName;
        return option;
    }

    // Template
    getTemplate() {
        return choiceInputTemplate;
    }

    // Field
    getField() {
        return this.container;
    }

    getValue() {
        return this.field ? this.field.value : null;
    }

    clearValue() {
        /* do nothing */
    }

    isEmpty() {
        return this.field ? this.field.value.length === 0 : true;
    }

    changedFromEmptyToValue() {
        return this.field ? this.field.value.length >= 1 : true;
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
        let value = this.getValue().trim();
        if (value.length === 0) {
            this.unknownDatatype();
            this.updateBadgesForParametersDependentOnThis();
            return DATATYPE_RESULT.UNKNOWN;
        } else {
            this.correctDatatype();
            this.updateBadgesForParametersDependentOnThis();
            return DATATYPE_RESULT.SUCCESS;
        }
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

    // Triggers
    triggerInputValidation() {
        const event = new CustomEvent('change', {
            detail: {calledByInputValidation: true}
        });
        this.dispatchEvent(event);
    }

    // Event Listeners
    dispatchEvent(event) {
        this.field.dispatchEvent(event);
    }

    onFocus(callback) {
        this.container.addEventListener('mousedown', callback);
    }

    onChange(callback) {
        if (this.field) this.field.addEventListener('change', callback);
    }

    // Info
    getInfo(globalTestClass, infoContainer) {
        const container = defaultParameterInfo.content.cloneNode(true).querySelector('div');

        // Description
        const description = this.getDescription();
        const paramDescriptionContainer = container.querySelector('.paramDescriptionContainer');
        if (description.length === 0) { paramDescriptionContainer.remove(); }
        else {
            paramDescriptionContainer.querySelector('.paramDescription').textContent = description;
        }

        // Datatypes
        container.querySelector('.infoTabDatatypeName').textContent = gettext("Choice Field");
        container.querySelector('.infoTabDatatypeDescription').textContent = gettext(`Pick from a set of predefined choices for this parameter`);

        infoContainer.appendChild(container);
    }
}