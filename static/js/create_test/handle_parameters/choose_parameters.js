/* Handles Parameters */

const paramTab = document.getElementById('parameters-tab');
const requiredContainer = document.getElementById("requiredContainer");
const optionalContainer = document.getElementById("optionalContainer");

/**
 * Checks if all parameters are valid and updates the submit button state.
 *
 * A parameter is considered valid if it is either valid in `validInputMap`
 * or currently blocked in `currentlyBlockedMap`.
 *
 * @param {Map<string, boolean>} validInputMap - Tracks each parameter's validity.
 * @param {Map<string, boolean>} currentlyBlockedMap - Tracks which parameters are currently blocked/disabled.
 * @param {HTMLElement} submitButton that "finishes" the parameter selection.
 */
function checkSubmitValidity(validInputMap, currentlyBlockedMap, submitButton) {
    for (const key in validInputMap) {
        const valueA = validInputMap[key];
        const valueB = currentlyBlockedMap[key] || false;
        if (!valueA && !valueB) disableSubmit(submitButton);
    }
    enableSubmit(submitButton);
}

/**
 * Attaches a submit validation handler to each parameter.
 *
 * Each parameter will trigger a check on the overall form validity
 * whenever its state changes, enabling or disabling the submit button accordingly.
 *
 * @param {Map<string, Map<string, any>>} parameters - Map of parameters to attach the handler to.
 * @param {Map<string, boolean>} validInputMap - Tracks current validity of each parameter.
 * @param {Map<string, boolean>} currentlyBlockedMap - Tracks which parameters are currently blocked/disabled.
 * @param {HTMLElement} submitButton that "finishes" the parameter selection
 */
function createSubmitHandler(parameters, validInputMap, currentlyBlockedMap, submitButton) {
    for (const parameterInfo of parameters) {
        parameterInfo['valid_submit_handler'] = () => {
            checkSubmitValidity(validInputMap, currentlyBlockedMap, submitButton);
        };
    }
}

/**
 * Appends parameter input fields to a DOM container.
 *
 * Iterates over each parameter in the map and adds its 'DOM_INPUT_FIELD' element
 * to the specified container.
 *
 * @param {Map<string, Map<string, any>>} parameters - Map of parameters, each containing
 *        a 'DOM_INPUT_FIELD' HTMLElement.
 * @param {HTMLElement} requiredContainer - The DOM element to append required parameter fields into.
 * @param {HTMLElement} optionalContainer - The DOM element to append optional parameter fields into.
 */
function loadParameterFieldsIntoDocument(parameters, requiredContainer, optionalContainer) {
    const fragmentRequired = document.createDocumentFragment();
    const fragmentOptional = document.createDocumentFragment();

    parameters.forEach(param => {
        const field = param['ParameterField'].getField();
        (param['requirement'] === "required" ? fragmentRequired : fragmentOptional).appendChild(field);
    });

    requiredContainer.appendChild(fragmentRequired);
    optionalContainer.appendChild(fragmentOptional);
}

/**
 * Creates DOM input fields for parameters and stores them in each parameter's map.
 *
 * Assigns each parameter a `DOM_INPUT_FIELD` and its `requirement` status ("required" or "optional").
 *
 * @param {Map<string, Map<string, any>>} requiredParams - Map of required parameters.
 * @param {Map<string, Map<string, any>>} optionalParams - Map of optional parameters.
 */
function createAndSaveParameterFields(requiredParams, optionalParams) {
    for (const [params, requirement] of [[requiredParams, "required"], [optionalParams, "optional"]]) {
        for (const parameterInfo of params) {
            let inputField = createParameterFields(parameterInfo, showParameters);
            inputField.createField();
            parameterInfo['ParameterField'] = inputField;
            parameterInfo['requirement'] = requirement;
        }
    }
}

/**
 * Sets up mutually exclusive behavior for form parameters.
 *
 * For each parameter in a mutually exclusive group, it attaches a handler
 * that disables all other fields in the group when the parameter is filled,
 * and re-enables them when the field is empty.
 *
 * @param {Map<string, Map<string, any>>} parameters - Map of parameters.
 * @param {Array<Array<string>>} mutually_exclusive_bindings - List of parameter groups
 *        where each group is an array of mutually exclusive parameter names.
 * @param {Map<string, boolean>} currentlyBlockedMap - Tracks which parameters are currently blocked/disabled.
 */

function createMutuallyExclusiveHandler(parameters, mutually_exclusive_bindings, currentlyBlockedMap) {
    /**
     * Activates the given field and disables all other fields in the group.
     *
     * @param {HTMLElement} activated The field to keep enabled.
     * @param {Iterable<HTMLElement>} allFields All fields in the mutually exclusive group.
     */
    function togglePair(activated, allFields) {
        for (const value of allFields.values()) {
            if (value === activated) continue;
            value.disable();
        }
    }

    /**
     * Enables all fields in the given collection.
     *
     * @param {Iterable<HTMLElement>} allFields Fields to enable.
     */
    function enableAllFields(allFields) {
        for (const value of allFields.values()) {
            value.enable();
        }
    }

    // Calculate all mutually exclusive neighbors
    let allMutuallyExclusiveParameters = new Set();
    let calculateMutNeighbors = {};
    mutually_exclusive_bindings.forEach(pair => {
        for (const param of pair) {
            allMutuallyExclusiveParameters.add(param);

            if (!(param in calculateMutNeighbors)) {
                calculateMutNeighbors[param] = new Set(pair);
            } else {
                const s = calculateMutNeighbors[param];
                pair.forEach(f => s.add(f));
            }
        }
    });

    /**
     * Searches for a ParameterField that has the given names
     * @param allParameterFields All ParameterFields to check
     * @param searchNames Names to search for
     * @returns {undefined|*} {name, ParameterField}
     */
    function getParameterFieldForNames(allParameterFields, searchNames) {
        const output = {};
        for (const param of allParameterFields) {
            const paramName = param['name'];
            if (searchNames.includes(paramName)) {
                output[paramName] = param;
            }
        }
        return output;
    }

    for (const param of allMutuallyExclusiveParameters) {
        const fieldNames = calculateMutNeighbors[param];
        fieldNames.add(param);
        const parameterNamesToParameterFields = getParameterFieldForNames(parameters, fieldNames)

        const field = parameterNamesToParameterFields[param]['ParameterField'];
        const fields = Array.from(fieldNames, neighbor => parameterNamesToParameterFields[neighbor]['ParameterField']);

        currentlyBlockedMap[param] = false;

        parameterNamesToParameterFields[param]['mutually_exclusive_handler'] = () => {
            if (field.isEmpty()) {
                enableAllFields(fields);
                fieldNames.forEach(fd => currentlyBlockedMap[fd] = false);
            } else if (field.changedFromEmptyToValue()) {
                togglePair(field, fields);
                fieldNames.forEach(fd => currentlyBlockedMap[fd] = true);
                currentlyBlockedMap[param] = false;
            }
        };
    }
}

/**
 * Attaches a datatype validation handler to each parameter.
 *
 * For each parameter, sets a `datatype_handler` function that validates
 * the parameter's value against its specified `type` when invoked.
 *
 * @param {Map<string, Map<string, any>>} parameters - Map of parameters, each containing
 *        at least 'DOM_INPUT_FIELD' and 'type' entries.
 * @param {Map<string, boolean>} validInputMap - Stores each parameter's current validity.
 */
function createDatatypeHandler(parameters, validInputMap) {
    for (const parameterInfo of parameters) {
        const parameterName = parameterInfo['name'];
        const field = parameterInfo['ParameterField'];
        const requirement = parameterInfo['requirement'];
        validInputMap[parameterName] = requirement === "optional";

        const validateResultBasedOnRequirement = {
            required: result => result === "success",
            optional: result => result === "success" || result === "unknown"
        };

        parameterInfo['datatype_handler'] = async () => {
            const result = await field.checkDatatype();
            console.log("DATATYPE VALID INPUT");
            console.log(validInputMap);
            validInputMap[parameterName] = validateResultBasedOnRequirement[requirement](result);
        };
    }
}

/**
 * Attaches input change listeners to parameter fields if needed.
 *
 * For each parameter, collects any defined handlers (`mutually_exclusive_handler`,
 * `datatype_handler`, etc.) and executes them whenever the field value changes.
 *
 * @param {Map<string, Map<string, any>>} parameters - Map of parameters, each containing
 *        at least 'DOM_INPUT_FIELD' and optional handler functions.
 */
function createInputListeners(parameters) {
    for (const parameterInfo of parameters) {
        const field = parameterInfo['ParameterField'];
        const handlerNames = ['mutually_exclusive_handler', 'datatype_handler', 'valid_submit_handler'];
        const handlers = handlerNames
            .map(name => parameterInfo[name])
            .filter(fn => typeof fn === 'function');

        if (handlers.length !== 0) {
            field.onChange(async () => {
                for (const handler of handlers) {
                    await handler();
                }
            });
        }
    }
}

/**
 * Dynamically creates input fields for all required and optional parameters of a test class.
 *
 * @param {Map<string, Map<string, any>>} requiredParams List of required parameters
 * @param {Map<string, Map<string, any>>} optionalParams List of optional parameters
 * @param {Array<Array<string>>} mutually_exclusive_bindings List of mutually exclusive bindings
 * @param {HTMLElement} requiredContainer - The DOM element to append required parameter fields into.
 * @param {HTMLElement} optionalContainer - The DOM element to append optional parameter fields into.
 * @param {HTMLElement} submitButton button that "finishes" the parameter selection
 */
function showParameters(requiredParams, optionalParams, mutually_exclusive_bindings, requiredContainer, optionalContainer, submitButton) {

    /**
     * Marks if a parameter's field currently has a valid input.
     * @type {Map<any, any>}
     */
    let validInputMap = new Map();

    /**
     * Marks if a parameter's field is currently blocked (unable to change value)
     */
    let currentlyBlockedMap = new Map();

    const allParameters = [...requiredParams, ...optionalParams];

    createAndSaveParameterFields(requiredParams, optionalParams);
    createMutuallyExclusiveHandler(allParameters, mutually_exclusive_bindings, currentlyBlockedMap);
    createDatatypeHandler(allParameters, validInputMap);
    createSubmitHandler(allParameters, validInputMap, currentlyBlockedMap, submitButton);
    createInputListeners(allParameters);
    loadParameterFieldsIntoDocument(allParameters, requiredContainer, optionalContainer);

    checkSubmitValidity(validInputMap, currentlyBlockedMap, submitButton);

    for (const parameterInfo of allParameters.values()) {
        parameterInfo['mutually_exclusive_handler']?.();
        parameterInfo['datatype_handler']?.();
    }
}


// Initialization
let previousTestClass = ""; // Store last TestClass to avoid recreating same parameter-fields
let settingUp = false; // Locks up TestClass selection while fields are being created
/**
 * "Selects" the given test class for further handling.
 *
 * @param {string} testClass The test class to select.
 * @param {HTMLElement} popup The popup.
 */
async function selectTestClass(testClass, popup) {
    if (settingUp) return; // Lock method from being used at the same time
    settingUp = true;

    popup.removeEventListener("keydown", onPopUpClickHandler); // remove focus from search Element in template tab

    if (previousTestClass === testClass) { // Already loaded
        paramTab.disabled = false;
        paramTab.click();
        settingUp = false;
        return;
    }

    previousTestClass = testClass;

    // Remove all previous parameter fields
    requiredContainer.innerHTML = "";
    optionalContainer.innerHTML = "";

    // Activate navigation towards parameter tab
    paramTab.classList.remove('disabled');
    paramTab.disabled = false;
    paramTab.click();

    // Fetch needed parameters
    let parameters = await fetchTestParameters(testClass);

    let requiredParameters = parameters.requiredParams;
    let optionalParameters = parameters.optionalParams;
    showParameters(
        requiredParameters,
        optionalParameters,
        parameters.mul,
        requiredContainer,
        optionalContainer,
        submitParametersButton);

    submitParametersButton.addEventListener("click", () => {
        selectParameters(requiredParameters, optionalParameters)
    });

    settingUp = false;
}

/**
 * Automatically sets focus to the search input when the popup is clicked.
 * Used in EventListeners between the Test-Class and Parameter tab.
 */
function onPopUpClickHandler(_) {
    searchInput.focus()
}