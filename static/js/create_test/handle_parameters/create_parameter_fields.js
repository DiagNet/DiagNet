const singleLineInputTemplate = document.getElementById('parameterInputTemplate');
const choiceInputTemplate = document.getElementById('choiceInputTemplate');
const listInputTemplate = document.getElementById('listInputTemplate');
const singleLineInputTemplateForDevices = document.getElementById('parameterInputTemplateForDevices');

/** Abstract base class representing a parameter input field. */
class ParameterField {
    /**
     * Syntax used to describe a value being used by another datatype definition. <br>
     * For Example: type: CIDR-value(type) | Where type is the name of a parameter
     */
    static parameterDatatypeDependencyRegex = /value\(([^)]+)\)/;

    /**
     * Simulates an Enum. Displays Datatype-checking-results.
     * @type {{UNKNOWN: string, SUCCESS: string, FAIL: string}}
     */
    static ACTIVATION_RESULT = {
        ACTIVATE: "active",
        DEACTIVATE: "deactive",
        UNKNOWN: "unknown"
    };

    /**
     * @param {Object.<string, any>} parameter - Metadata map for the parameter.
     * @param {Object.<string, Array<ParameterField>>} datatypeDependencyMap - Stores the parameters which's datatype is dependent on other parameters.
     * @param {Object.<string, Array<ParameterField>>} activationDependencyMap Map of parameters that manages when a parameter is displayed.
     * @throws {Error} If instantiated directly (abstract class).
     */
    constructor(parameter, datatypeDependencyMap, activationDependencyMap) {
        if (new.target === ParameterField) throw new Error("Cannot instantiate abstract class ParameterField directly");

        this.parameter = parameter;
        this.field = null;
        this.datatypeDependencyMap = datatypeDependencyMap;
        this.activationDependencyMap = activationDependencyMap;
        datatypeDependencyMap[parameter['name']] = [];
    }

    // Activation Management
    /** Returns what parameters are triggering the activation of this parameter */
    getActivationTriggers() {
        return [
            ...Object.keys(this.get('forbidden_if') || {}),
            ...Object.keys(this.get('required_if') || {})
        ];
    }

    /** Returns if the Parameter is currently shown. */
    isShown() {
        return this.getField().style.display === "";
    }

    /** Triggers submit validition for this field */
    refreshSubmitValidity() {
        const event = new CustomEvent('input', {
            detail: {calledByInputValidation: true}
        });
        this.parameter['valid_submit_handler'](event);
    }

    /** Shows this Parameter */
    showField() {
        //let refreshSubmitValidity = !this.isShown();
        this.getField().style.display = "";
        //if (refreshSubmitValidity) this.refreshSubmitValidity();
    }

    /** Hides this Parameter */
    hideField() {
        //let refreshSubmitValidity = this.isShown();
        this.getField().style.display = "none";
        //if (refreshSubmitValidity) this.refreshSubmitValidity();
    }

    /**
     * Handles a Trigger
     * @param parameterName The Parameter that initiated the trigger.
     * @param value the value parsed in the trigger.
     */
    handleActivationTrigger(parameterName, value) {
        // forbidden if
        let currentState = ParameterField.ACTIVATION_RESULT.UNKNOWN;
        const requiredMap = this.get('required_if');
        if (requiredMap && parameterName in requiredMap) {
            const requiredRegex = new RegExp(requiredMap[parameterName].toLowerCase());
            if (requiredRegex.test(value.toLowerCase())) {
                this.showField();
                currentState = ParameterField.ACTIVATION_RESULT.ACTIVATE;
            } else {
                this.hideField();
                currentState = ParameterField.ACTIVATION_RESULT.DEACTIVATE;
            }
        }
        const forbiddenMap = this.get('forbidden_if');
        if (forbiddenMap && parameterName in forbiddenMap) {
            const forbiddenRegex = new RegExp(forbiddenMap[parameterName].toLowerCase());
            if (forbiddenRegex.test(value.toLowerCase())) {
                this.hideField();
                currentState = ParameterField.ACTIVATION_RESULT.DEACTIVATE;
            } else {
                this.showField();
                currentState = ParameterField.ACTIVATION_RESULT.ACTIVATE;
            }
        }


        return currentState;
    }

    // Info
    /**
     * Equivalent to this.parameter[str]
     * @param str the info string to extract
     */
    get(str) {
        return this.parameter[str];
    }

    // Field

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

    /** Clears the input field's value. */
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
     * @returns {boolean} True if this field just changed from empty to not empty.
     */
    changedFromEmptyToValue() {
        return this.field ? this.field.value.length === 1 : true;
    }

    /** Enables the input field for user interaction. */
    enable() {
        if (this.field) {
            this.field.disabled = false;
            this.field.readOnly = false;
        }
    }

    /** Disables the input field, preventing user interaction. */
    disable() {
        if (this.field) {
            this.field.disabled = true;
            this.field.readOnly = true;
        }
    }

    /** Called after the Field that is returned by createField() is added in the document. */
    afterCreatingField() {
        // check activation triggers
        this.parameter['activation_handler']?.();

        // check for datatype dependency
        const match = this.parameter['type'].match(ParameterField.parameterDatatypeDependencyRegex); // value(target_field)
        if (match) {
            const dependentOn = match[1]; // value(target_field) -> target_field
            try {
                this.getDatatypeDependencyMap()[dependentOn].push(this); // Mark itself dependent on read parameter
            } catch (e) {
                throwException("Could not build Datatype dependencies for parameter " + this.get('name') + ". (maybe you mistyped a parameter name?)")
            }
        }
    }

    // Event Listeners
    /**
     * Attaches a callback to execute whenever the input value changes.
     * If this field has a parent, input changes trigger onInternalChange() for the parent field.
     *
     * @param {function} callback - Function to run on input event.
     */
    onChange(callback) {
        let list_parent = this.parameter['parent_list'];
        if (list_parent) {
            if (this.field) this.field.addEventListener('input', (e) => {
                callback(e);
                list_parent.onInternalChange();
            });
        }
        if (this.field) this.field.addEventListener('input', callback);
    }

    /**
     * Attaches a callback to execute whenever the input gains focus.
     * @param {function} callback Function to run on input event.
     */
    onFocus(callback) {
        if (this.field) this.field.addEventListener('focus', callback);
    }

    /** Triggers Input Validation and sets a flag to prevent internal loops. */
    triggerInputValidation() {
        const event = new CustomEvent('input', {
            detail: {calledByInputValidation: true}
        });
        this.field.dispatchEvent(event);
    }

    /**
     * Checks if the given event was produced by triggerInputValidation()
     * @param event The event to check
     * @returns {boolean} True if it was triggered by triggerInputValidation(), otherwise false. (looks for internal flag event.detail.calledByInputValidation)
     */
    isTriggeredByInputValidation(event) {
        return event && event.detail && event.detail.calledByInputValidation
    }

    // Datatype
    /** Returns the datatypeDependencyMap associated with this Parameter */
    getDatatypeDependencyMap() {
        return this.datatypeDependencyMap;
    }

    /** Resets the input field's border to its default style. */
    unknownDatatype() {
        if (this.field) this.field.style.border = "";
    }

    /** Marks the input field as valid by setting its border to green. */
    correctDatatype() {
        if (this.field) this.field.style.border = "2px solid green";
    }

    /** Marks the input field as invalid by setting its border to red. */
    wrongDatatype() {
        if (this.field) this.field.style.border = "2px solid red";
    }

    /**
     * Checks if the current field's value matches the expected datatype.
     * @returns {Promise<string>} Result of the datatype validation.
     */
    async checkDatatype() {
        return handleCheckDataType(this, this.parameter['type']); // handle_datatypes.js
    }

    // Submit Validity
    /**
     * Additionally to Datatype Validation and Mutually Exclusive Validation,
     * this method also checks for additional submit conditions.
     */
    checkFieldSubmitValidity() {
        return true;
    }
}

/** Displays a single line input device field. */
class SingleLineDeviceField extends ParameterField {
    // Field
    async createField() {
        this.container = singleLineInputTemplateForDevices.content.cloneNode(true).querySelector('div');

        this.visibleItems = [];

        this.searchResults = this.container.querySelector("#searchResults");
        _ = this.insertDevicesIntoResults();
        this.resetPointer();

        // Additional Handler for the device dropdown
        this.parameter['datatype_dropdown_handler'] = (e) => {
            this.handleDropdownInput(e);
        };
        this.field = this.container.querySelector('.param-input');

        this.container.querySelector('.param-label').textContent = this.parameter['name'];
        this.field.placeholder = this.parameter['name'];

        return this.container;
    }

    getField() {
        return this.container;
    }

    changedFromEmptyToValue() {
        const evaluation = (this.field ? this.field.value.length === 1 : true) || this.selectedDropdownItem; // Selecting Something does not trigger === 1
        this.selectedDropdownItem = false;
        return evaluation;
    }


    // Device Dropdown

    /** Hides the Device Dropdown*/
    hideDropdown() {
        // do nothing - deselection happens automatically
    }

    /** Shows the Device Dropdown*/
    showDropdown() {
        this.dropdown.show();
    }

    // Setup
    afterCreatingField() {
        super.afterCreatingField();

        // Dropdown can only be initialized after the input field is loaded into the document
        this.dropdown = new bootstrap.Dropdown(this.field, {
            autoClose: 'outside' // 'outside' prevents it from re-focusing on the toggle
        });

        this.field.addEventListener("blur", this.hideDropdown.bind(this));
        this.field.addEventListener("keydown", this.handleDropdownKeyDown.bind(this));

        this.searchResults.addEventListener('mousedown', (e) => {
            if (e.target.tagName === 'LI') this.selectItem(e.target.textContent);
        });
    }

    onFocus(callback) {
        this.field.addEventListener('focus', (event) => {
            callback(event);
            if (this.dropdown) {
                this.showDropdown();
                this.handleDropdownInput(new Event("input", {bubbles: true})); // Trigger Dropdown as if an input was made
            }
        });
    }

    /** Takes all Devices and puts them into the dropdown. */
    async insertDevicesIntoResults() {
        this.uninitializedDeviceList = true;
        await updateDevices(); // fetch devices
        allDevices.forEach(this.addDeviceToDropdown, this);
        this.uninitializedDeviceList = false;

        this.dropdownItems = this.searchResults.querySelectorAll('li');
    }

    // Logic
    /** Resets the Pointer to determine what Dropdown Element is currently Selected. */
    resetPointer() {
        this.selectedIndex = -1;
        this.searchResults.querySelectorAll('li').forEach(li => li.classList.remove('active'));
    }

    /**
     * Adds a device to the dropdown content.
     * @param device Device as string.
     */
    addDeviceToDropdown(device) {
        const li = document.createElement('li');      // create li element
        li.className = 'list-group-item hoverable';
        li.textContent = device;
        this.searchResults.appendChild(li);
    }

    /** Called on input - Handles the Filter when searching. */
    handleDropdownInput(event) {
        // Escape Datatype Validation Trigger
        if ((this.uninitializedDeviceList) || this.isTriggeredByInputValidation(event)) return;

        this.resetPointer();
        const filter = this.getValue().toLowerCase();
        this.dropdown.show();

        const visibleItems = [];
        this.dropdownItems.forEach(item => {
            const text = item.textContent.toLowerCase();
            if (text.includes(filter)) {
                item.style.display = '';
                visibleItems.push(item);
            } else {
                item.style.display = 'none';
            }
        });

        this.visibleItems = visibleItems;
    }

    /** Handles Keyboard Navigation (in order to enable Arrow-Key Navigation). */
    handleDropdownKeyDown(e) {
        // Escape Datatype Validation Trigger
        if (this.uninitializedDeviceList || this.isTriggeredByInputValidation(e)) return;

        const items = this.visibleItems;
        if (!items.length) return;

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            let prevIndex = this.selectedIndex;
            this.selectedIndex = (this.selectedIndex + 1) % items.length;
            this.updateSelection(items, prevIndex);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            let prevIndex = this.selectedIndex;
            this.selectedIndex = (this.selectedIndex - 1 + items.length) % items.length;
            this.updateSelection(items, prevIndex);
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (this.selectedIndex >= 0) this.selectItem(items[this.selectedIndex].textContent);
        } else if (e.key === 'Tab') {
            this.dropdown.hide();
            this.resetPointer();
        } else if (e.key === 'Escape') {
            this.dropdown.hide();
            this.resetPointer();
        }
    }

    /** Selects an Item chosen by the Navigation. */
    selectItem(value) {
        if (this.uninitializedDeviceList) return;

        this.field.value = value;
        this.hideDropdown();
        this.resetPointer();

        this.selectedDropdownItem = true;
        this.triggerInputValidation();
    }

    /**
     * Checks what dropdown item is currently chosen and "selects" it.
     * @param items all items.
     * @param prev the previous selected Index.
     */
    updateSelection(items, prev) {
        items[this.selectedIndex].classList.add('active');
        if (prev >= 0) items[prev].classList.remove('active');
    }
}

/** Displays a single line input field. */
class SingleLineInputField extends ParameterField {
    async createField() {
        this.container = singleLineInputTemplate.content.cloneNode(true).querySelector('div');
        this.field = this.container.querySelector('.param-input');

        this.container.querySelector('.param-label').textContent = this.parameter['name'];
        this.field.placeholder = this.parameter['name'];

        return this.container;
    }

    getField() {
        return this.container;
    }

    onFocus(callback) {
        this.container.addEventListener('mousedown', callback);
    }
}

/** Displays a multiple choice input field. */
class ChoiceField extends ParameterField {
    async createField() {
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

    triggerInputValidation() {
        const event = new CustomEvent('change', {
            detail: {calledByInputValidation: true}
        });
        this.field.dispatchEvent(event);
    }

    onFocus(callback) {
        this.container.addEventListener('mousedown', callback);
    }

    /**
     * Checks if the current field's value matches the expected datatype.
     * @returns {Promise<string>} Result of the datatype validation.
     */
    async checkDatatype() {
        let value = this.getValue().trim();
        if (value.length === 0) {
            this.unknownDatatype();
            await uncacheValue(this);
            return DATATYPE_RESULT.UNKNOWN;
        } else {
            this.correctDatatype();
            await cacheValue(this, value);
            return DATATYPE_RESULT.SUCCESS;
        }
    }
}

/** Displays a list input field. */
class ListField extends ParameterField {
    /**
     * @param {Object.<string, any>} parameter - Metadata for the list.
     * @param {Object.<string, Array<ParameterField>>} dependencyMap - Stores what parameters are linked to each other.
     * @param {Object.<string, Array<ParameterField>>} activationDependencyMap Map of parameters that manages when a parameter is displayed.
     */
    constructor(parameter, dependencyMap, activationDependencyMap) {
        super(parameter, dependencyMap, activationDependencyMap);
        this.children = new Set();
    }

    // Field
    async createField() {
        this.items = [];

        this.container = listInputTemplate.content.cloneNode(true).querySelector('div');

        this.label = this.container.querySelector('.list-label');
        this.label.textContent = this.parameter['name'] + " List-View";

        this.countBadge = this.container.querySelector('.list-count');
        this.addButton = this.container.querySelector('.add-to-list-btn');
        this.countInfo = this.container.querySelector('.count-label');

        const requiredParams = this.parameter['required'] || [];
        const optionalParams = this.parameter['optional'] || [];
        this.allParameters = [...requiredParams, ...optionalParams];
        const mutually_exclusive_bindings = this.parameter['mutually_exclusive'];


        this.allParameters.forEach(value => value['parent_list'] = this);

        await showParameters(
            requiredParams,
            optionalParams,
            mutually_exclusive_bindings,
            this.container,
            this.container,
            this.addButton,
            this.getDatatypeDependencyMap(),
            this.activationDependencyMap,
            false,
            () => this.checkGlobalSubmitValidity(this)
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

        // Stop list mousedown behaviour when clicking the add button.
        this.addButton.addEventListener("mousedown", (event) => {
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
        if (this.parameter['constraints']) {
            for (const constraint of this.parameter['constraints']) {
                try {
                    const [key, value] = constraint.split("=");
                    this[key] = value;
                } catch (e) {
                    throwException("Failed to load constraint: " + constraint + " for parameter " + this.parameter['name']);
                }
            }
        }

        return this.container;
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

    /** Collects the Values of child elements and returns them. */
    getValue() {
        return [...this.items];
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
        for (const value of this.allParameters) {
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

    // Event Listeners
    onChange(callback) {
        this.callback = callback;
    }

    triggerInputValidation() {
        this.callback();
    }

    triggerFocus() {
        this.container.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
    }

    onFocus(callback) {
        this.container.addEventListener('mousedown', (e) => {
            callback(e);
        });
    }

    // Datatype
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
 * There are 4 options:
 * 1. Single Input Fields (default)
 * 1. Device Input Fields (type === "device")
 * 2. Multiple Choice (type === "choice")
 * 3. List Views (type === "list")
 *
 * @param parameter The parameter Object mapping.
 * @param dependencyMap The Object-Map describing what datatypes are linked with what parameter values.
 * @param activationDependencyMap Map of parameters that manages when a parameter is displayed.
 * @returns {ParameterField} The created ParameterField
 */
function createParameterFields(parameter, dependencyMap, activationDependencyMap) {
    switch (parameter['type']) {
        case "choice":
            return new ChoiceField(parameter, dependencyMap, activationDependencyMap);
        case "list":
            return new ListField(parameter, dependencyMap, activationDependencyMap);
        case "device":
            return new SingleLineDeviceField(parameter, dependencyMap, activationDependencyMap);
        default:
            return new SingleLineInputField(parameter, dependencyMap, activationDependencyMap);
    }
}
