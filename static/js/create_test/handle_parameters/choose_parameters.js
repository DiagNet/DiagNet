/* Handles Parameters */

const paramTab = document.getElementById('parameters-tab');
const parameterContainer = document.getElementById("parameterContainer");
let submitParametersButton = document.getElementById("submitParameters");

/**
 * Checks if all parameters are valid and updates the submit button state.
 *
 * A parameter is considered valid if it is either valid in `validInputMap`
 * or currently blocked in `currentlyBlockedMap`.
 *
 * @param {Map<string, boolean>} validInputMap - Tracks each parameter's validity.
 * @param {Map<string, boolean>} currentlyBlockedMap - Tracks which parameters are currently blocked/disabled.
 */
function checkSubmitValidity(validInputMap, currentlyBlockedMap) {
    /**
     * Checks if all keys in mapA are valid based on values in mapA or mapB.
     *
     * A key is considered valid if its value is `true` in either mapA or mapB.
     *
     * @param {Map<string, boolean>} mapA - Primary validation map.
     * @param {Map<string, boolean>} mapB - Secondary fallback validation map.
     * @returns {boolean} - True if all keys pass validation, otherwise false.
     */
    function isEveryKeyValidOR(mapA, mapB) {
        for (const [key, valueA] of mapA) {
            const valueB = mapB.get(key) || false;
            if (!valueA && !valueB) {
                return false;
            }
        }
        return true;
    }

    if (isEveryKeyValidOR(validInputMap, currentlyBlockedMap)) {
        enableSubmit();
    } else {
        disableSubmit();
    }
}

function createSubmitHandler(parameters, validInputMap, currentlyBlockedMap) {
    for (const [_, parameterInfo] of parameters) {
        parameterInfo.set('valid_submit_handler', () => {
            checkSubmitValidity(validInputMap, currentlyBlockedMap);
        });
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
 * @param {HTMLElement} container - The DOM element to append parameter fields into.
 */
function loadParameterFieldsIntoDocument(parameters, container) {
    const fragment = document.createDocumentFragment();
    parameters.forEach(param => fragment.append(param.get('DOM_INPUT_FIELD')));
    container.appendChild(fragment);
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
        for (const [_, parameterInfo] of params) {
            parameterInfo.set('DOM_INPUT_FIELD', createParameterFields(parameterInfo));
            parameterInfo.set('requirement', requirement);
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
            disableField(value);
        }
    }

    /**
     * Enables all fields in the given collection.
     *
     * @param {Iterable<HTMLElement>} allFields Fields to enable.
     */
    function enableAllFields(allFields) {
        for (const value of allFields.values()) {
            enableField(value);
        }
    }

    // Calculate all mutually exclusive neighbors
    let allMutuallyExclusiveParameters = new Set();
    let calculateMutNeighbors = new Map();
    mutually_exclusive_bindings.forEach(pair => {
        for (const param of pair) {
            allMutuallyExclusiveParameters.add(param);

            if (!calculateMutNeighbors.has(param)) {
                calculateMutNeighbors.set(param, new Set(pair));
            } else {
                const s = calculateMutNeighbors.get(param);
                pair.forEach(f => s.add(f));
            }
        }
    });

    for (const param of allMutuallyExclusiveParameters) {
        const field = parameters.get(param).get('DOM_INPUT_FIELD');

        const fieldNames = calculateMutNeighbors.get(param);
        const fields = Array.from(fieldNames, neighbor => parameters.get(neighbor).get('DOM_INPUT_FIELD'));

        currentlyBlockedMap.set(param, false);

        parameters.get(param).set('mutually_exclusive_handler', () => {
            if (fieldIsEmpty(field)) {
                enableAllFields(fields);
                fieldNames.forEach(fd => currentlyBlockedMap.set(fd, false));
            } else if (fieldChangedFromEmptyToValue(field)) {
                togglePair(field, fields);
                fieldNames.forEach(fd => currentlyBlockedMap.set(fd, true));
                currentlyBlockedMap.set(param, false);
            }
        });
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
    for (const [parameter_name, parameterInfo] of parameters) {
        const field = parameterInfo.get('DOM_INPUT_FIELD');
        const requirement = parameterInfo.get('requirement');
        validInputMap.set(parameter_name, requirement === "optional");

        const validateResultBasedOnRequirement = {
            required: result => result === "success",
            optional: result => result === "success" || result === "unknown"
        };

        parameterInfo.set('datatype_handler', async () => {
            const result = await handleCheckDataType(field, parameterInfo.get('type'));

            validInputMap.set(parameter_name, validateResultBasedOnRequirement[requirement](result))
        });
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
    for (const [_, parameterInfo] of parameters) {
        const field = parameterInfo.get('DOM_INPUT_FIELD');
        const handlerNames = ['mutually_exclusive_handler', 'datatype_handler', 'valid_submit_handler'];
        const handlers = handlerNames
            .map(name => parameterInfo.get(name))
            .filter(fn => typeof fn === 'function');

        if (handlers.length !== 0) {
            executeOnInputChange(field, async () => {
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
 */
function showParameters(requiredParams, optionalParams, mutually_exclusive_bindings) {

    /**
     * Marks if a parameter's field currently has a valid input.
     * @type {Map<any, any>}
     */
    let validInputMap = new Map();

    /**
     * Marks if a parameter's field is currently blocked (unable to change value)
     */
    let currentlyBlockedMap = new Map();

    const allParameters = new Map([...requiredParams, ...optionalParams]);

    createAndSaveParameterFields(requiredParams, optionalParams);
    createMutuallyExclusiveHandler(allParameters, mutually_exclusive_bindings, currentlyBlockedMap);
    createDatatypeHandler(allParameters, validInputMap);
    createSubmitHandler(allParameters, validInputMap, currentlyBlockedMap);
    createInputListeners(allParameters);
    loadParameterFieldsIntoDocument(allParameters, parameterContainer);

    checkSubmitValidity(validInputMap, currentlyBlockedMap);
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

    parameterContainer.innerHTML = ""; // Remove all previous parameter fields

    // Activate navigation towards parameter tab
    paramTab.classList.remove('disabled');
    paramTab.disabled = false;
    paramTab.click();

    // Fetch needed parameters
    let parameters = await fetchTestParameters(testClass);
    showParameters(
        new Map(Array.from(parameters.requiredParams.values(), innerMap => [innerMap["name"], new Map(Object.entries(innerMap))])),
        new Map(Array.from(parameters.optionalParams.values(), innerMap => [innerMap["name"], new Map(Object.entries(innerMap))])),
        parameters.mul);

    settingUp = false;
}

/**
 * Automatically sets focus to the search input when the popup is clicked.
 * Used in EventListeners between the Test-Class and Parameter tab.
 */
function onPopUpClickHandler(_) {
    searchInput.focus()
}