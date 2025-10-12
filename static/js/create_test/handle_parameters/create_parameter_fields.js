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
        return this.field
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
    switch (parameter.get('type')) {
        case "choice":
            return new ChoiceField(parameter);
        case "list":
            break;
        default:
            return new SingleLineInputField(parameter);
    }
}