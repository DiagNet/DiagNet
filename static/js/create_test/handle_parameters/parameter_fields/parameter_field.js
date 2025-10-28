/** Abstract base class representing a parameter input field. */
class ParameterField {
    /**
     * @param {Object.<string, any>} parameter - Metadata map for the parameter.
     * @throws {Error} If instantiated directly (abstract class).
     */
    constructor(parameter) {
        if (new.target === ParameterField) throw new Error("Cannot instantiate abstract class ParameterField directly");

        this.parameter = parameter;
        this.field = null;
        this.datatypeDependencies = [];
    }

    // Info
    /**
     * Equivalent to this.parameter[str].
     * @param str the info string to extract.
     */
    get(str) {
        return this.parameter[str];
    }

    /** Returns a list of all datatypes associated with this parameter. */
    getType() {
        const type = this.get('type');
        return type;
    }

    /** Returns the descripion associated with this parameter. */
    getDescription() {
        return this.get('description') ? this.get('description') : "";
    }

    /** Returns the internal name of this parameter. */
    getName() {
        return this.get('name');
    }

    /** Returns the display name of this parameter. */
    getDisplayName() {
        return this.get('display_name') ? this.get('display_name') : this.getName();
    }

    /** Returns if this parameter is considered "required". */
    isRequired() {
        return this.get('requirement') !== "optional";
    }

    /**
     * Returns the list containing this parameter.
     * If there is no parent, undefined is returned.
     */
    getParent() {
        return this.get('parent') ? this.get('parent') : undefined;
    }

    // Visibility
    /** Returns if the Parameter is currently shown. */
    isShown() {
        return this.getField().style.display === "";
    }

    /** Shows this Parameter */
    showField() {
        this.getField().style.display = "";
    }

    /** Hides this Parameter */
    hideField() {
        this.getField().style.display = "none";
    }

    // Activation Management
    /**
     * Simulates an Enum. Displays parameter activation states.
     * @type {{ACTIVATE: string, DEACTIVATE: string, UNKNOWN: string}}
     */
    static ACTIVATION_RESULT = {
        ACTIVATE: "active",
        DEACTIVATE: "not_active",
        UNKNOWN: "unknown"
    };

    /** Returns what parameters are triggering the activation of this parameter */
    getActivationTriggers() {
        return [
            ...Object.keys(this.get('forbidden_if') || {}),
            ...Object.keys(this.get('required_if') || {})
        ];
    }

    /**
     * Checks if the given activation keyword matches the given value.
     * @param mapKey activation keyword.
     * @param parameterName the Parameter that initiated the trigger.
     * @param value the value parsed in the trigger.
     * @param activateOnMatch
     */
    checkTriggerResult(mapKey, parameterName, value, activateOnMatch = true) {
        const map = this.get(mapKey)?.[parameterName];
        if (!map) return ParameterField.ACTIVATION_RESULT.UNKNOWN;
        const isMatch = new RegExp(map, "i").test(value);
        return (isMatch === activateOnMatch ? this.showField() : this.hideField(),
            isMatch === activateOnMatch ? ParameterField.ACTIVATION_RESULT.ACTIVATE : ParameterField.ACTIVATION_RESULT.DEACTIVATE);
    }

    /**
     * Handles an Activation-Trigger
     * @param parameterName the Parameter that initiated the trigger.
     * @param value the value parsed in the trigger.
     */
    handleActivationTrigger(parameterName, value) {
        let currentStateRequiredIf = this.checkTriggerResult('required_if', parameterName, value, true);
        let currentStateForbiddenIf = this.checkTriggerResult('forbidden_if', parameterName, value, false);

        return currentStateForbiddenIf === ParameterField.ACTIVATION_RESULT.UNKNOWN ? currentStateRequiredIf : currentStateForbiddenIf;
    }

    // Triggers

    /**
     * Dispatches an event for this parameter.
     * @param {Event} event The event to dispatch
     */
    dispatchEvent(event) {
        throw new Error("getField() must be implemented in subclass");
    }

    /** Triggers submit validation for this field */
    refreshSubmitValidity() {
        const event = new CustomEvent('input', {
            detail: {calledByInputValidation: true}
        });
        this.parameter['valid_submit_handler'](event);
    }

    /** Triggers Input Validation and sets a flag to prevent internal loops. */
    triggerInputValidation() {
        const event = new CustomEvent('input', {
            detail: {calledByInputValidation: true}
        });
        this.dispatchEvent(event);
    }

    /**
     * Checks if the given event was produced by triggerInputValidation()
     * @param event The event to check
     * @returns {boolean} True if it was triggered by triggerInputValidation(), otherwise false. (looks for internal flag event.detail.calledByInputValidation)
     */
    isTriggeredByInputValidation(event) {
        return event && event.detail && event.detail.calledByInputValidation
    }

    // Field
    /**
     * Returns the DOM element representing this input field.
     * @returns {HTMLElement|null} The input field DOM element.
     */
    getField() {
        throw new Error("getField() must be implemented in subclass");
    }

    /**
     * Abstract method to create the DOM input element.
     * Must be implemented by subclasses.
     * @throws {Error} If not implemented in subclass.
     */
    createField() {
        throw new Error("createField() must be implemented in subclass");
    }

    /** Returns the template that is used to create this ParameterField. */
    getTemplate() {
        throw new Error("getTemplate() must be implemented in subclass");
    }

    /** Makes a clone of the given template and returns the first div. */
    loadTemplateContainer() {
        return this.getTemplate().content.cloneNode(true).querySelector('div');
    }

    /**
     * Returns a red star as a string
     * @returns {string}
     */
    requiredMark() {
        return "<span class=\"text-danger star\">*</span>";
    }

    /**
     * Returns the current value of the input field.
     * @returns {string|null|Array<any>} Current input value, or null if field does not exist.
     */
    getValue() {
        throw new Error("getValue() must be implemented in subclass");
    }

    /** Clears the input field's value. */
    clearValue() {
        throw new Error("clearValue() must be implemented in subclass");
    }

    /**
     * Checks whether the input field is empty.
     * @returns {boolean} True if empty or field not created, false otherwise.
     */
    isEmpty() {
        throw new Error("isEmpty() must be implemented in subclass");
    }

    /**
     * Checks if the field's value just changed from empty to a value.
     * @returns {boolean} True if this field just changed from empty to not empty.
     */
    changedFromEmptyToValue() {
        throw new Error("changedFromEmptyToValue() must be implemented in subclass");
    }

    /** Enables the input field for user interaction. */
    enable() {
        throw new Error("enable() must be implemented in subclass");
    }

    /** Disables the input field, preventing user interaction. */
    disable() {
        throw new Error("disable() must be implemented in subclass");
    }

    /** Called after the Field that is returned by createField() is added in the document. */
    afterCreatingField() {
        // check activation triggers
        // If for example this parameter is referenced in another parameter's required_if then this method call will handle it.
        this.get('activation_handler')?.();
    }

    // Event Listeners
    /**
     * Attaches a callback to execute whenever the input value changes.
     *
     * @param {function} callback - Function to run on input event.
     */
    onChange(callback) {
        throw new Error("onChange() must be implemented in subclass");
    }

    /**
     * Attaches a callback to execute whenever the input gains focus.
     * @param {function} callback Function to run on input event.
     */
    onFocus(callback) {
        throw new Error("onFocus() must be implemented in subclass");
    }

    // Badges
    updateDatatypeBadges() {

    }

    // Datatype
    /** Returns the datatypeDependencyMap associated with this Parameter */
    getDatatypeDependencies() {
        return this.datatypeDependencies;
    }

    /**
     * Called by foreign datatypes to mark their parameter as dependent on this parameter.
     * @param parameter The parameter whose datatype is dependent on this parameter.
     */
    insertDependentParameter(parameter) {
        this.datatypeDependencies.push(parameter);
    }

    /** Updates the displayed Badges when a datatype validation has happened. */
    updateBadgesForParametersDependentOnThis() {
        for (const dependentField of this.getDatatypeDependencies()) {
            dependentField.updateDatatypeBadges();
            dependentField.triggerInputValidation();
        }
    }

    /**
     * Checks if the current field's value matches the expected datatype.
     * @returns {Promise<string>} Result of the datatype validation.
     */
    async checkDatatype() {
        throw new Error("checkDatatype() must be implemented in subclass");
    }

    /** Resets the input field's border to its default style. */
    unknownDatatype() {
        throw new Error("unknownDatatype() must be implemented in subclass");
    }

    /** Marks the input field as valid by setting its border to green. */
    correctDatatype() {
        throw new Error("correctDatatype() must be implemented in subclass");
    }

    /** Marks the input field as invalid by setting its border to red. */
    wrongDatatype() {
        throw new Error("wrongDatatype() must be implemented in subclass");
    }

    // Submit Validity
    /**
     * Additionally to Datatype Validation and Mutually Exclusive Validation,
     * this method also checks for additional submit conditions.
     */
    checkFieldSubmitValidity() {
        return true;
    }

    // Info

    /**
     * Returns an HTMLElement that contains Information describing this parameter.
     * @param {string} globalTestClass The global TestClass that has been selected.
     * @param {HTMLElement} infoContainer The container holding the info box.
     * @returns {HTMLElement} Container encapsulation the information that covers this parameter.
     */
    getInfo(globalTestClass, infoContainer) {
        throw new Error("getInfo() must be implemented in subclass");
    }
}