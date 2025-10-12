const submitParametersButton = document.getElementById("submitParameters");

/** Abstract base class for parameter input fields. */
class ParameterField {
    /**
     * @param {Map<string, any>} parameter - Parameter map containing metadata like name, type, choices, etc.
     */
    constructor(parameter) {
        if (new.target === ParameterField) {
            throw new Error("Cannot instantiate abstract class ParameterField directly");
        }
        this.parameter = parameter;
        this.field = null; // Will hold the DOM element
    }

    getField() {
        return this.field;
    }

    /**
     * Create the DOM input field.
     * Must be implemented by subclasses.
     */
    createField() {
        throw new Error("createField() must be implemented in subclass");
    }

    /** Returns the current value of the input field. */
    getValue() {
        if (!this.field) return null;
        return this.field.value;
    }


    /** Checks if the field is empty. */
    isEmpty() {
        return this.field ? this.field.value.length === 0 : true;
    }

    /** Checks if the field just changed from empty to a value. */
    changedFromEmptyToValue() {
        return this.field ? this.field.value.length === 1 : true;
    }

    /** Enables the input field. */
    enable() {
        if (this.field) {
            this.field.disabled = false;
            this.field.readOnly = false;
        }
    }

    /**
     * Disables the input field.
     */
    disable() {
        if (this.field) {
            this.field.disabled = true;
            this.field.readOnly = true;
        }
    }

    /**
     * Attach a handler to execute on input change.
     * @param {function} callback
     */
    onChange(callback) {
        if (this.field) {
            this.field.addEventListener('input', callback);
        }
    }

    /**
     * Resets the input field's border to the default style.
     */
    unknownDatatype() {
        this.field.style.border = "";
    }

    /**
     * Marks the input field as valid by setting its border to green.
     */
    correctDatatype() {
        this.field.style.border = "2px solid green";
    }

    /**
     * Marks the input field as invalid by setting its border to red.
     */
    wrongDatatype() {
        this.field.style.border = "2px solid red";
    }

    /**
     * Checks whether the current field's value matches its expected datatype.
     */
    async checkDatatype() {
        return handleCheckDataType(this, this.parameter.get('type'));
    }
}

/**
 * Single-line text input.
 */
class SingleLineInputField extends ParameterField {
    createField() {
        this.field = document.createElement("input");
        this.field.type = "text";
        this.field.className = "form-control mb-2";
        this.field.placeholder = this.parameter.get('name');
        return this.field;
    }
}

/**
 * Choice (select) input.
 */
class ChoiceField extends ParameterField {
    createField() {
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

        return this.field;
    }

    /** Checks if the field is empty. */
    isEmpty() {
        return this.field ? this.field.value.length === 0 : true;
    }

    /** Checks if the field just changed from empty to a value. */
    changedFromEmptyToValue() {
        return this.field ? this.field.value.length >= 1 : true;
    }

    /**
     * Attach a handler to execute on input change.
     * @param {function} callback
     */
    onChange(callback) {
        if (this.field) {
            this.field.addEventListener('change', callback);
        }
    }
}

// TODO How does the ListField interact with allowing submission? in general whole list is work in progress
/**
 * List input field.
 * Can handle multiple values separated by newlines.
 */
class ListField extends ParameterField {

    /**
     * @param {Map<string, any>} parameter - Parameter metadata
     * @param {string} showParameters - The method to create new input fields
     */
    constructor(parameter, showParameters) {
        super(parameter);
        if (showParameters === undefined || showParameters === null) {
            throw new Error("ListField requires a valid method reference to showParameters");
        }
        this.showParameters = showParameters;
    }

    createField() {
        this.container = document.createElement("div");
        this.container.className = "list-field-container";

        let required_params = this.parameter.get('required');
        let optional_params = this.parameter.get('optional');
        let mutually_exclusive_bindings = this.parameter.get('mutually_exclusive');

        showParameters(
            new Map(Array.from(required_params.values(), innerMap => [innerMap["name"], new Map(Object.entries(innerMap))])),
            new Map(Array.from(optional_params.values(), innerMap => [innerMap["name"], new Map(Object.entries(innerMap))])),
            mutually_exclusive_bindings,
            this.container
        );

        return this.container;
    }

    getField() {
        return this.container;
    }

    /** Returns the values as an array of strings (splitting by newlines). */
    getValue() {
        if (!this.field) return [];
        return this.field.value
            .split("\n")
            .map(item => item.trim())
            .filter(item => item.length > 0);
    }

    /** Checks if the field is empty. */
    isEmpty() {
        return this.getValue().length === 0;
    }

    /** Checks if the field just changed from empty to a value. */
    changedFromEmptyToValue() {
        return this.getValue().length === 1;
    }

    /**
     * Attach a handler to execute on input change.
     * Fires on 'input' event for textarea.
     */
    onChange(callback) {
        if (this.field) {
            this.field.addEventListener('input', callback);
        }
    }

    /**
     * Checks whether the current field's value matches its expected datatype.
     */
    async checkDatatype() {
        return "success";
    }
}

/**
 * Enables the form's submit button.
 */
function enableSubmit() {
    submitParametersButton.disabled = false;
}

/**
 * Disables the form's submit button.
 */
function disableSubmit() {
    submitParametersButton.disabled = true;
}

/**
 * Creates a parameter field based on the specified type.
 *
 * @param {Map<string, Map<string, any>>} parameter - The parameter to handle
 * @param {function} showParameters Used to create more input fields when a list object is parsed.
 * @returns {Object} The parameter field object corresponding to the given type.
 */
function createParameterFields(parameter, showParameters) {
    console.log(parameter.get('type'));
    switch (parameter.get('type')) {
        case "choice":
            return new ChoiceField(parameter);
        case "list":
            return new ListField(parameter, showParameters);
        default:
            return new SingleLineInputField(parameter);
    }
}