const submitParametersButton = document.getElementById("submitParameters");

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
        if (this.field) this.field.addEventListener('input', callback);
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
     * @returns {Promise<boolean>} Result of the datatype validation.
     */
    async checkDatatype() {
        return handleCheckDataType(this, this.parameter.get('type'));
    }
}

class SingleLineInputField extends ParameterField {
    createField() {
        this.container = document.createElement("div");
        this.container.className = "SingleLineInputContainer";
        this.container.style.padding = "5px 3px";
        this.container.style.margin = "10px 10px 10px 0px";

        let label = document.createElement("label");
        label.textContent = this.parameter.get('name');
        label.className = "form-label";
        label.style.fontSize = "15px";

        this.field = document.createElement("input");
        this.field.type = "text";
        this.field.className = "form-control mb-2";
        this.field.placeholder = this.parameter.get('name');

        this.container.appendChild(label);
        this.container.appendChild(this.field);

        return this.container;
    }

    getField() {
        return this.container;
    }
}

class ChoiceField extends ParameterField {
    createField() {
        this.container = document.createElement("div");
        this.container.className = "SingleLineInputContainer";
        this.container.style.padding = "5px 3px";
        this.container.style.margin = "10px 10px 10px 0px";

        let label = document.createElement("label");
        label.textContent = this.parameter.get('name');
        label.className = "form-label";
        label.style.fontSize = "15px";

        this.field = document.createElement("select");
        this.field.className = "form-select mb-2";

        const options = this.parameter.get('choices') || [];
        const defaultChoice = this.parameter.get('default_choice');
        if (defaultChoice === undefined) options.unshift("");

        options.forEach(opt => {
            const optionEl = document.createElement("option");
            optionEl.value = opt.toLowerCase();
            optionEl.textContent = opt;
            if (opt === defaultChoice) optionEl.selected = true;
            this.field.appendChild(optionEl);
        });

        this.container.appendChild(label);
        this.container.appendChild(this.field);
        return this.container;
    }

    clearValue() {} // do nothing

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
}

// TODO it list is required it can still be submitted if it is empty
class ListField extends ParameterField {
    /**
     * @param {Map<string, any>} parameter - Metadata for the list.
     * @param {function} showParameters - Callback to create child input fields.
     */
    constructor(parameter, showParameters) {
        super(parameter);
        if (!showParameters) throw new Error("ListField requires showParameters");
        this.showParameters = showParameters;
        this.children = new Set();
        this.addToList = null;
    }

    createField() {
        this.container = document.createElement("div");
        this.container.className = "list-field-container";
        this.container.style.width = "100%";

        const topRow = document.createElement("div");
        topRow.style.display = "flex";
        topRow.style.alignItems = "center";
        topRow.style.gap = "1rem";

        const label = document.createElement('label');
        label.id = "list-label";
        label.innerHTML = this.parameter.get('name') + " List-View";
        label.className = "form-label";
        topRow.appendChild(label);

        const addToList = document.createElement("button");
        addToList.textContent = "Add to List";
        addToList.style.padding = "6px 12px";
        addToList.style.cursor = "pointer";
        topRow.appendChild(addToList);

        const labelNumberOfListItems = document.createElement('label');
        labelNumberOfListItems.id = "list-label";
        labelNumberOfListItems.innerHTML = "0";
        labelNumberOfListItems.className = "form-label";
        topRow.appendChild(labelNumberOfListItems);
        this.labelNumberOfListItems = labelNumberOfListItems;

        this.container.appendChild(topRow);

        const requiredParams = new Map(Array.from(this.parameter.get('required').values(),
            innerMap => [innerMap["name"], new Map(Object.entries(innerMap))]));
        const optionalParams = new Map(Array.from(this.parameter.get('optional').values(),
            innerMap => [innerMap["name"], new Map(Object.entries(innerMap))]));
        const allParameters = new Map([...requiredParams, ...optionalParams]);
        const mutually_exclusive_bindings = this.parameter.get('mutually_exclusive');

        this.showParameters(
            requiredParams,
            optionalParams,
            mutually_exclusive_bindings,
            this.container,
            this.container,
            addToList
        );

        let nested_index = Number(this.parameter.get('nested_index') ?? 0) + 1;
        for (const value of allParameters.values()) {
            value.set('nested_index', nested_index);
            const field = value.get('DOM_INPUT_FIELD');
            this.children.add(field);
            field.getField().style.marginLeft = `${nested_index}rem`;
        }

        addToList.addEventListener("click", () => this.add());

        this.addToList = addToList;
        this.allParameters = allParameters;
        this.addOutput = [];

        return this.container;
    }

    getValue() {
        return this.addOutput;
    }

    /**
     * Retrieves current values from all child fields.
     * @returns {Array} Values of all child input fields.
     */
    receiveValuesFromChildren() {
        let output = [];
        for (const value of this.allParameters.values()) {
            output.push(value.get('DOM_INPUT_FIELD').getValue());
        }
        return output;
    }

    /**
     * Adds current child values to the output array and updates count.
     */
    add() {
        this.labelNumberOfListItems.innerHTML = (Number(this.labelNumberOfListItems.innerHTML) + 1) + "";
        this.addOutput.push(this.receiveValuesFromChildren());
        this.clearValue();
    }

    /**
     * Clears all child fields and disables the add button.
     */
    clearValue() {
        this.children.forEach(c => c.clearValue());
        disableSubmit(this.addToList);
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

    onChange(callback) {
        if (this.field) this.field.addEventListener('input', callback);
    }

    async checkDatatype() {
        return "success";
    }
}

function enableSubmit(button) {
    button.disabled = false;
}

function disableSubmit(button) {
    button.disabled = true;
}

function createParameterFields(parameter, showParameters) {
    switch (parameter.get('type')) {
        case "choice":
            return new ChoiceField(parameter);
        case "list":
            return new ListField(parameter, showParameters);
        default:
            return new SingleLineInputField(parameter);
    }
}
