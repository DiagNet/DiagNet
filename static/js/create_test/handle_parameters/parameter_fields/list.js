const listInputTemplate = document.getElementById('listInputTemplate');

/** Displays a list input field. */
class ListField extends Parameter_field {
    async createField() {
        this.container = this.loadTemplateContainer();

        this.items = []; // stores what was added to the list.
        this.children = new Set(); // stores the ParameterFields inside the list.


        let labelContact = this.getDisplayName();
        if (this.isRequired()) labelContact += this.requiredMark();
        this.container.querySelector('.list-label').innerHTML = labelContact;

        this.countBadge = this.container.querySelector('.list-count');
        this.addButton = this.container.querySelector('.add-to-list-btn');
        this.countInfo = this.container.querySelector('.count-label');

        this.parameters = this.get('parameters') || [];
        if (!this.parameters.length) throwException(`List "${this.getDisplayName()} does not have any parameters.`);
        const mutually_exclusive_bindings = this.get('mutually_exclusive');


        this.parameters.forEach(value => value['parent'] = this);

        await showParameters(
            this.parameters,
            mutually_exclusive_bindings,
            this.container,
            this.addButton,
            this.getDatatypeDependencyMap(),
            this.activationDependencyMap,
            false,
            () => this.checkGlobalSubmitValidity(this)
        );

        let nested_index = Number(this.get('nested_index') ?? 0) + 1;
        for (const value of this.parameters) {
            value['nested_index'] = nested_index;

            const field = value['parameter_info'];
            this.children.add(field);

            field.getField().style.marginLeft = `${nested_index}rem`;
        }

        // Stop list mousedown behaviour when clicking the add button.
        this.addButton.addEventListener("mousedown", (event) => { // TODO remove if unnecessary after test
            event.stopPropagation();
            event.preventDefault();
        });

        this.addButton.addEventListener("click", (event) => {
            event.stopPropagation();
            event.preventDefault();
            this.add();
            this.triggerFocus();
        });

        // Constraints
        this.loadConstraints();

        return this.container;
    }

    // Constraints
    /** Loads the constraints attached to this list. */
    loadConstraints() {
        if (this.get('constraints')) {
            for (const constraint of this.parameter['constraints']) {
                try {
                    const [key, value] = constraint.split("=");
                    this[key] = value;
                } catch (e) {
                    throwException("Failed to load constraint: " + constraint + " for parameter " + this.parameter['name']);
                }
            }
        }
    }

    // Template
    getTemplate() {
        return listInputTemplate;
    }

    // Field
    getField() {
        return this.container;
    }

    /** Collects the Values of child elements and returns them. */
    getValue() {
        return [...this.items];
    }

    // ClearValue includes add logic, you can find it deeper in the file.

    isEmpty() {
        return this.getValue().length === 0;
    }

    changedFromEmptyToValue() {
        return this.getValue().length === 1;
    }

    enable() {
        // TODO
        if (this.field) {
            this.field.disabled = false;
            this.field.readOnly = false;
        }
    }

    disable() {
        // TODO
        if (this.field) {
            this.field.disabled = true;
            this.field.readOnly = true;
        }
    }

    /** Removes the given value */
    removeValue(value) {
        const removeIndex = this.items.indexOf(value);
        if (removeIndex >= 0) {
            this.items.splice(removeIndex, 1);
            this.decreaseCountBadge();
            this.triggerInputValidation();
        }
    }

    // Datatype
    async checkDatatype() {
        if (this.isEmpty()) {
            this.unknownDatatype();
            return DATATYPE_RESULT.UNKNOWN;
        } else {
            this.correctDatatype();
            return DATATYPE_RESULT.SUCCESS;
        }
    }

    unknownDatatype() {
        // do nothing
    }

    correctDatatype() {
        // do nothing
    }

    wrongDatatype() {
        // do nothing
    }

    // Triggers
    triggerInputValidation() {
        this.callback(new Event('input', {bubbles: true}));
    }

    triggerFocus() {
        this.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
    }

    // Event Listeners
    dispatchEvent(event) {
        this.container.dispatchEvent(event);
    }

    onFocus(callback) {
        this.container.addEventListener('mousedown', callback);
    }

    onChange(callback) {
        this.callback = callback;
    }


    // countBadge
    clearCountBadge() {
        this.countBadge.innerHTML = "0";
        this.badgeInfoUpdate();
    }

    /** Increases the Count Badge signifying the amount of items in this list. */
    decreaseCountBadge() {
        this.countBadge.innerHTML = (Number(this.countBadge.innerHTML) - 1) + "";
        this.badgeInfoUpdate();
    }

    /** Decreases the Count Badge signifying the amount of items in this list. */
    increaseCountBadge() {
        this.countBadge.innerHTML = (Number(this.countBadge.innerHTML) + 1) + "";
        this.badgeInfoUpdate();
    }

    badgeCountCorrect() {
        this.countBadge.classList.remove('bg-primary', 'bg-warning', 'bg-secondary');
        this.countBadge.classList.add('bg-success');
        this.countInfo.innerHTML = "";
    }

    badgeCountUnknown() {
        this.countBadge.classList.remove('bg-primary', 'bg-warning', 'bg-success');
        this.countBadge.classList.add('bg-secondary');
        this.countInfo.innerHTML = "";
    }

    badgeCountMaxed() {
        this.countBadge.classList.remove('bg-secondary', 'bg-warning', 'bg-success');
        this.countBadge.classList.add('bg-primary');
        this.countInfo.innerHTML = "maximum length reached";
    }

    badgeCountTooLow() {
        this.countBadge.classList.remove('bg-secondary', 'bg-primary', 'bg-success');
        this.countBadge.classList.add('bg-warning');
        this.countInfo.innerHTML = "minimum length for this list is " + this.min_length;
    }

    badgeInfoUpdate() {
        const currentBadgeNumber = Number(this.countBadge.innerHTML);
        if (this.items.length === 0) {
            this.badgeCountUnknown();
        } else if (this.min_length && currentBadgeNumber < this.min_length) {
            this.badgeCountTooLow();
        } else if (this.max_length && currentBadgeNumber >= this.max_length) {
            this.badgeCountMaxed();
        } else {
            this.badgeCountCorrect();
        }
    }

    // Submit Validation
    /**
     * Handles a Global Submit Validation Check for Lists.
     * @param {ListField} listField The ListField
     * @returns {boolean}
     */
    checkGlobalSubmitValidity(listField) {
        if (listField.max_length !== undefined) {
            return listField.items.length < listField.max_length;
        }
        return true;
    }

    checkFieldSubmitValidity() {
        if (this.min_length !== undefined) {
            return this.items.length >= this.min_length;
        }
        return true;
    }

    /**
     * Retrieves current values from all child fields.
     * @returns {Array} Values of all child input fields.
     */
    receiveValuesFromChildren() {
        let output = {};
        for (const value of this.parameters) {
            output[value['name']] = value['parameter_info'].getValue();
        }
        return output;
    }

    /** Adds current child values to the current items and updates count. */
    add() {
        this.items.push(this.receiveValuesFromChildren());
        this.clearValue(false);
        this.triggerInputValidation();
        this.increaseCountBadge();
    }

    /** Clears all child fields and disables the add button. */
    clearValue(clearSelf) {
        this.children.forEach(c => {
            c.clearValue(true)
        });
        disableSubmit(this.addButton);
        if (clearSelf) {
            this.items.length = 0;
            this.triggerInputValidation();
            this.clearCountBadge();
        }
        this.triggerChildValidation();
    }

    triggerChildValidation() {
        let firstChild = [...this.children][0];
        if (firstChild) firstChild.triggerInputValidation();
    }
}