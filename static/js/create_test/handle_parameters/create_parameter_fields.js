const singleLineInputTemplate = document.getElementById('parameterInputTemplate');
const choiceInputTemplate = document.getElementById('choiceInputTemplate');
const listInputTemplate = document.getElementById('listInputTemplate');
const singleLineInputTemplateForDevices = document.getElementById('parameterInputTemplateForDevices');

/**
 * Abstract base class representing a parameter input field.
 */
class ParameterField {
    /**
     * @param {Map<string, any>} parameter - Metadata map for the parameter.
     * @throws {Error} If instantiated directly (abstract class).
     */
    constructor(parameter) {
        if (new.target === ParameterField) {
            throw new Error("Cannot instantiate abstract class ParameterField directly");
        }
        this.parameter = parameter;
        this.field = null;
    }

    /**
     * Returns the DOM element representing this input field.
     * @returns {HTMLElement|null} The input field DOM element.
     */
    getField() {
        return this.field;
    }

    /**
     * Abstract method to create the DOM input element.
     * Must be implemented by subclasses.
     * @throws {Error} If not implemented in subclass.
     */
    createField() {
        throw new Error("createField() must be implemented in subclass");
    }

    /**
     * Returns the current value of the input field.
     * @returns {string|null|Array<any>} Current input value, or null if field does not exist.
     */
    getValue() {
        return this.field ? this.field.value : null;
    }

    /**
     * Clears the input field's value.
     */
    clearValue() {
        if (this.field) this.field.value = "";
    }

    /**
     * Checks whether the input field is empty.
     * @returns {boolean} True if empty or field not created, false otherwise.
     */
    isEmpty() {
        return this.field ? this.field.value.length === 0 : true;
    }

    /**
     * Checks if the field's value just changed from empty to a value.
     * @returns {boolean} True if value length is 1 or field not created.
     */
    changedFromEmptyToValue() {
        return this.field ? this.field.value.length === 1 : true;
    }

    /**
     * Enables the input field for user interaction.
     */
    enable() {
        if (this.field) {
            this.field.disabled = false;
            this.field.readOnly = false;
        }
    }

    /**
     * Disables the input field, preventing user interaction.
     */
    disable() {
        if (this.field) {
            this.field.disabled = true;
            this.field.readOnly = true;
        }
    }

    /**
     * Attaches a callback to execute whenever the input value changes.
     * @param {function} callback - Function to run on input event.
     */
    onChange(callback) {
        let list_parent = this.parameter['parent_list'];
        if (list_parent) {
            if (this.field) this.field.addEventListener('input', (e) => {
                callback(e);
                list_parent.onInternalChange()
            });
        }
        if (this.field) this.field.addEventListener('input', callback);
    }

    onFocus(callback) {
        if (this.field) this.field.addEventListener('focus', callback);
    }

    /**
     * Resets the input field's border to its default style.
     */
    unknownDatatype() {
        if (this.field) this.field.style.border = "";
    }

    /**
     * Marks the input field as valid by setting its border to green.
     */
    correctDatatype() {
        if (this.field) this.field.style.border = "2px solid green";
    }

    /**
     * Marks the input field as invalid by setting its border to red.
     */
    wrongDatatype() {
        if (this.field) this.field.style.border = "2px solid red";
    }

    /**
     * Checks if the current field's value matches the expected datatype.
     * @returns {Promise<string>} Result of the datatype validation.
     */
    async checkDatatype() {
        return handleCheckDataType(this, this.parameter['type']);
    }

    /**
     * Called after the Field that is returned by createField() is added in the document.
     */
    afterCreatingField() {
        // do nothing
    }
}


class SingleLineInputField extends ParameterField {
    createField() {
        if (this.parameter['type'] === "device") {
            this.container = singleLineInputTemplateForDevices.content.cloneNode(true).querySelector('div');

            this.searchResults = this.container.querySelector("#searchResults");
            this.insertDevicesIntoResults();
            this.resetPointer();

            this.parameter['datatype_dropdown_handler'] = (e) => {
                this.handleDropDownInput(e);
            };
        } else {
            this.container = singleLineInputTemplate.content.cloneNode(true).querySelector('div');
        }
        this.field = this.container.querySelector('.param-input');

        this.container.querySelector('.param-label').textContent = this.parameter['name'];
        this.field.placeholder = this.parameter['name'];

        return this.container;
    }

    resetPointer() {
        this.selectedIndex = -1;
        this.searchResults.querySelectorAll('li').forEach(li => li.classList.remove('active'));
    }

    async insertDevicesIntoResults() {
        await updateDevices();
        for (const device of allDevices) {

            const li = document.createElement('li');      // create li element
            li.className = 'list-group-item';
            li.textContent = device;
            li.addEventListener("click", () => {
                this.dropdown.hide();
                this.resetPointer();
                this.field.value = device;
                this.triggerDatatypeValidation();
            });
            this.searchResults.appendChild(li);
        }
    }

    handleDropDownKeyDown(e) {
        if (e && e.detail && e.detail.calledByDropDownSelection) {
            return;
        }

        const items = Array.from(this.searchResults.querySelectorAll('li'))
            .filter(li => li.offsetParent !== null);
        if (!items.length) return;
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            this.selectedIndex = (this.selectedIndex + 1) % items.length;
            this.updateSelection(items);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            this.selectedIndex = (this.selectedIndex - 1 + items.length) % items.length;
            this.updateSelection(items);
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (this.selectedIndex >= 0) this.selectItem(items[this.selectedIndex].textContent);
        } else if (e.key === 'Tab') {
            this.dropdown.hide();
            this.resetPointer();
        }
    }

    triggerDatatypeValidation() {
        const event = new CustomEvent('input', {
            bubbles: true,
            detail: {calledByDropDownSelection: true}
        });
        this.field.dispatchEvent(event);
    }

    selectItem(value) {
        this.field.value = value;
        this.dropdown.hide();
        this.triggerDatatypeValidation();
    }

    updateSelection(items) {
        items.forEach((li, i) => li.classList.toggle('active', i === this.selectedIndex));
        if (this.selectedIndex >= 0) {
            items[this.selectedIndex].scrollIntoView({block: 'nearest'});
        }
    }

    handleDropDownInput(event) {
        if (event && event.detail && event.detail.calledByDropDownSelection) {
            return;
        }
        this.resetPointer();
        const filter = this.field.value.toLowerCase();
        const items = this.searchResults.querySelectorAll('li');
        this.dropdown.show();

        items.forEach(item => {
            const text = item.textContent.toLowerCase();
            if (text.includes(filter)) {
                item.style.display = '';
            } else {
                item.style.display = 'none';
            }
        });
    }

    afterCreatingField() {
        if (this.parameter['type'] === "device") {
            this.dropdown = new bootstrap.Dropdown(this.field);
            this.field.addEventListener("blur", () => {
                this.dropdown.hide();
            });
            this.field.addEventListener("keydown", (e) => this.handleDropDownKeyDown(e));
        }
    }

    getField() {
        return this.container;
    }

    onFocus(callback) {
        this.field.addEventListener('focus', (event) => {
            callback(event);
            if (this.dropdown) this.dropdown.show();
        });
    }
}

class ChoiceField extends ParameterField {
    createField() {
        this.container = choiceInputTemplate.content.cloneNode(true).querySelector('div');
        this.field = this.container.querySelector('.choice-select');

        this.label = this.container.querySelector('.choice-label');
        this.label.textContent = this.parameter['name'];

        const options = this.parameter['choices'] || [];
        const defaultChoice = this.parameter['default_choice'];
        if (defaultChoice === undefined) options.unshift("");

        options.forEach(opt => {
            const option = document.createElement("option");
            option.value = opt.toLowerCase();
            option.textContent = opt;
            if (opt === defaultChoice) option.selected = true;
            this.field.appendChild(option);
        });

        return this.container;
    }

    clearValue() {
        /* do nothing */
    }

    getField() {
        return this.container;
    }

    isEmpty() {
        return this.field ? this.field.value.length === 0 : true;
    }

    changedFromEmptyToValue() {
        return this.field ? this.field.value.length >= 1 : true;
    }

    onChange(callback) {
        if (this.field) this.field.addEventListener('change', callback);
    }

    onFocus(callback) {
        this.container.addEventListener('click', callback);
    }

    /**
     * Checks if the current field's value matches the expected datatype.
     * @returns {Promise<string>} Result of the datatype validation.
     */
    async checkDatatype() {
        if (this.getValue().length === 0) {
            this.unknownDatatype();
            return DATATYPE_RESULT.UNKNOWN;
        } else {
            this.correctDatatype();
            return DATATYPE_RESULT.SUCCESS;
        }
    }

}

class ListField extends ParameterField {
    /**
     * @param {Map<string, any>} parameter - Metadata for the list.
     */
    constructor(parameter) {
        super(parameter);
        this.children = new Set();
    }

    createField() {
        this.addOutput = [];

        this.container = listInputTemplate.content.cloneNode(true).querySelector('div');

        this.label = this.container.querySelector('.list-label');
        this.label.textContent = this.parameter['name'] + " List-View";

        this.countBadge = this.container.querySelector('.list-count');
        this.addButton = this.container.querySelector('.add-to-list-btn');

        const requiredParams = this.parameter['required'] || [];
        const optionalParams = this.parameter['optional'] || [];
        this.allParameters = [...requiredParams, ...optionalParams];
        const mutually_exclusive_bindings = this.parameter['mutually_exclusive'];


        this.allParameters.forEach(value => value['parent_list'] = this);

        showParameters(
            requiredParams,
            optionalParams,
            mutually_exclusive_bindings,
            this.container,
            this.container,
            this.addButton
        );

        let nested_index = Number(this.parameter['nested_index'] ?? 0) + 1;
        for (const value of this.allParameters) {
            value['parent_name'] = this;
            value['parent_type'] = this.parameter['type'];
            value['nested_index'] = nested_index;

            const field = value['parameter_info'];
            this.children.add(field);

            field.getField().style.marginLeft = `${nested_index}rem`;
        }

        this.addButton.addEventListener("click", () => this.add());

        return this.container;
    }

    /** Collects the Values of child elements and returns them. */
    getValue() {
        let addOutputAsObject = []
        for (const item of this.addOutput) {
            addOutputAsObject.push(item);
        }
        return addOutputAsObject;
    }

    /** Removes the given Value */
    removeValue(value) {
        const removeIndex = this.addOutput.indexOf(value);
        if (removeIndex > -1) {
            this.addOutput.splice(removeIndex, 1);
            this.countBadge.innerHTML = (Number(this.countBadge.innerHTML) - 1) + "";
            this.callback();
        }
    }

    /**
     * Retrieves current values from all child fields.
     * @returns {Array} Values of all child input fields.
     */
    receiveValuesFromChildren() {
        let output = {};
        for (const value of this.allParameters) {
            output[value['name']] = value['parameter_info'].getValue();
        }
        return output;
    }

    /** Adds current child values to the output array and updates count. */
    add() {
        this.countBadge.innerHTML = (Number(this.countBadge.innerHTML) + 1) + "";
        this.addOutput.push(this.receiveValuesFromChildren());
        this.clearValue(false);
        this.callback();
    }

    getChildren() {
        return this.children;
    }

    /** Clears all child fields and disables the add button. */
    clearValue(clearSelf) {
        this.children.forEach(c => {
            c.clearValue(true)
        });
        disableSubmit(this.addButton);
        if (clearSelf) {
            this.addOutput.length = 0;
            this.callback();
            this.countBadge.innerHTML = "0";
        }
    }

    getField() {
        return this.container;
    }

    isEmpty() {
        return this.getValue().length === 0;
    }

    changedFromEmptyToValue() {
        return this.getValue().length === 1;
    }

    onInternalChange() {
        // do nothing
    }

    onChange(callback) {
        this.callback = callback;
    }

    onFocus(callback) {
        this.container.addEventListener('click', callback);
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

    async checkDatatype() {
        if (this.isEmpty()) {
            this.unknownDatatype();
            return DATATYPE_RESULT.UNKNOWN;
        } else {
            this.correctDatatype();
            return DATATYPE_RESULT.SUCCESS;
        }
    }
}

/**
 * Creates a Parameter Field according to its type.
 * There are 3 options:
 * 1. Single Input Fields (default)
 * 2. Multiple Choice (type === "choice")
 * 3. List Views (type === "list")
 *
 * @param parameter
 * @returns {ParameterField}
 */
function createParameterFields(parameter) {
    switch (parameter['type']) {
        case "choice":
            return new ChoiceField(parameter);
        case "list":
            return new ListField(parameter);
        default:
            return new SingleLineInputField(parameter);
    }
}
