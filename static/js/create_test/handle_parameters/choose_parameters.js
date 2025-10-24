/* Handles Parameters */

const paramTab = document.getElementById('parameters-tab');
const requiredContainer = document.getElementById("requiredContainer");
const optionalContainer = document.getElementById("optionalContainer");
const submitParametersButton = document.getElementById("submitParameters");

/**
 * Checks if all parameters are valid and updates the submit button state.
 *
 * A parameter is considered valid if it is either valid in `validInputMap`
 * or currently blocked in `currentlyBlockedMap`.
 *
 * @param {Array<Object.<string, any>>} parameters - Map of parameters
 * @param {Object.<string, boolean>} validInputMap - Tracks each parameter's validity.
 * @param {Object.<string, boolean>} currentlyBlockedMap - Tracks which parameters are currently blocked/disabled.
 * @param {Object.<string, Array<ParameterField>|Object.<string, boolean>>} activationMap Maps what parameters are effected when changing one specific Parameter
 * @param {HTMLElement} submitButton that "finishes" the parameter selection.
 * @param {function} extraSubmitValidity Function that is called for validating further submit requirements.
 */
function checkSubmitValidity(parameters, validInputMap, currentlyBlockedMap, activationMap, submitButton, extraSubmitValidity) {
    if (extraSubmitValidity && !extraSubmitValidity()) {
        disableSubmit(submitButton);
        return;
    }

    for (const key in validInputMap) {
        const valueA = validInputMap[key];
        const valueB = currentlyBlockedMap[key] || false;
        let valueC = true; // default is true
        if (activationMap["ACTIVATION_STATE"]) {
            let activationState = activationMap["ACTIVATION_STATE"][key];
            if (activationState === undefined) activationState = ParameterField.ACTIVATION_RESULT.ACTIVATE;
            else valueC = (activationState === ParameterField.ACTIVATION_RESULT.ACTIVATE) || (activationState === ParameterField.ACTIVATION_RESULT.UNKNOWN);
        }

        if (valueC && !valueA && !valueB) {
            disableSubmit(submitButton);
            return;
        }
    }

    if (!parameters.every(item => item['parameter_info'].checkFieldSubmitValidity())) {
        disableSubmit(submitButton);
        return;
    }

    enableSubmit(submitButton);
}

/**
 * Attaches a submit validation handler to each parameter.
 *
 * Each parameter will trigger a check on the overall form validity
 * whenever its state changes, enabling or disabling the submit button accordingly.
 *
 * @param {Array<Object.<string, any>>} parameters - Map of parameters to attach the handler to.
 * @param {Object.<string, boolean>} validInputMap - Tracks current validity of each parameter.
 * @param {Object.<string, boolean>} currentlyBlockedMap - Tracks which parameters are currently blocked/disabled.
 * @param {Object.<string, Array<ParameterField>|Object.<string, boolean>>} activationMap Maps what parameters are effected when changing one specific Parameter
 * @param {HTMLElement} submitButton that "finishes" the parameter selection
 * @param {function} extraSubmitValidity Function that is called for validating further submit requirements.
 */
function createSubmitHandler(parameters, validInputMap, currentlyBlockedMap, activationMap, submitButton, extraSubmitValidity) {
    for (const parameterInfo of parameters) {
        parameterInfo['valid_submit_handler'] = (e) => {
            if (validInputMap[parameterInfo['name']] || (e && e.detail && e.detail.calledByInputValidation)) {
                checkSubmitValidity(parameters, validInputMap, currentlyBlockedMap, activationMap, submitButton, extraSubmitValidity);
            }
        };
    }
}

/**
 * Appends parameter input fields to a DOM container.
 *
 * @param {Array<Object.<string, any>>} parameters - Map of parameters
 * @param {HTMLElement} requiredContainer - The DOM element to append required parameter fields into.
 * @param {HTMLElement} optionalContainer - The DOM element to append optional parameter fields into.
 */
function loadParameterFieldsIntoDocument(parameters, requiredContainer, optionalContainer) {
    const fragmentRequired = document.createDocumentFragment();
    const fragmentOptional = document.createDocumentFragment();

    parameters.forEach(param => {
        const field = param['parameter_info'].getField();
        (param['requirement'] === "required" ? fragmentRequired : fragmentOptional).appendChild(field);
    });

    requiredContainer.appendChild(fragmentRequired);
    optionalContainer.appendChild(fragmentOptional);

    parameters.forEach(param => {
        param['parameter_info'].afterCreatingField();
    });
}

/**
 * Creates DOM input fields for parameters and stores them in each parameter's map.
 *
 * @param {Array<Object.<string, any>>} requiredParams - Map of required parameters.
 * @param {Array<Object.<string, any>>} optionalParams - Map of optional parameters.
 * @param {Object.<string, Array<ParameterField>>} datatypeDependencyMap Map of parameters that depend on each other.
 * @param {Object.<string, Array<ParameterField>>} activationDependencyMap Map of parameters that manages when a parameter is displayed.
 * */
async function createAndSaveParameterFields(requiredParams, optionalParams, datatypeDependencyMap, activationDependencyMap) {
    for (const [params, requirement] of [[requiredParams, "required"], [optionalParams, "optional"]]) {
        for (const parameterInfo of params) {
            let inputField = createParameterFields(parameterInfo, datatypeDependencyMap, activationDependencyMap);
            await inputField.createField();
            parameterInfo['parameter_info'] = inputField;
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
 * @param {Array<Object.<string, any>>} parameters - Map of parameters.
 * @param {Array<Array<string>>} mutually_exclusive_bindings - List of parameter groups
 *        where each group is an array of mutually exclusive parameter names.
 * @param {Object.<string, boolean>} currentlyBlockedMap - Tracks which parameters are currently blocked/disabled.
 */

function createMutuallyExclusiveHandler(parameters, mutually_exclusive_bindings, currentlyBlockedMap) {
    /**
     * Activates the given field and disables all other fields in the group.
     *
     * @param {ParameterField} activated The field to keep enabled.
     * @param {Array<ParameterField>} allFields All fields in the mutually exclusive group.
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
     * @param {Array<ParameterField>} allFields Fields to enable.
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
     * @param {Array<Object.<string, any>>} allParameterFields All ParameterFields to check
     * @param {Set<string>} searchNames Names to search for
     * @returns {Object.<string, ParameterField>} {name, ParameterField}
     */
    function getParameterFieldForNames(allParameterFields, searchNames) {
        const output = {};
        let foundNamesCount = 0;
        for (const param of allParameterFields) {
            const paramName = param['name'];
            if (searchNames.has(paramName)) {
                output[paramName] = param;
                foundNamesCount += 1;
            }
        }
        if (foundNamesCount !== searchNames.size) {
            throwException("Mutually-Exclusive-Binding Parameter not found as an actual Parameter");
        }
        return output;
    }

    for (const param of allMutuallyExclusiveParameters) {
        const fieldNames = calculateMutNeighbors[param];
        fieldNames.add(param);
        const parameterNamesToParameterFields = getParameterFieldForNames(parameters, fieldNames)

        const field = parameterNamesToParameterFields[param]['parameter_info'];
        const fields = Array.from(fieldNames, neighbor => parameterNamesToParameterFields[neighbor]['parameter_info']);

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
 * @param {Array<Object.<string, any>>} parameters - Map of parameters.
 * @param {Object.<string, boolean>} validInputMap - Stores each parameter's current validity.
 */
function createDatatypeHandler(parameters, validInputMap) {
    for (const parameterInfo of parameters) {
        const parameterName = parameterInfo['name'];
        const parameterType = parameterInfo['type'];
        const field = parameterInfo['parameter_info'];
        const requirement = parameterInfo['requirement'];
        validInputMap[parameterName] = requirement === "optional";

        if (!parameterName) {
            throwException(`No name found for given parameter - Consider adding the 'name' field in the test definition`);
        }
        if (!parameterType) {
            throwException(`No datatype found for parameter ${parameterName} - Consider adding the 'type' field in the test definition`);
        }

        const validateResultBasedOnRequirement = {
            required: result => result === DATATYPE_RESULT.SUCCESS,
            optional: result => result === DATATYPE_RESULT.SUCCESS || result === DATATYPE_RESULT.UNKNOWN
        };

        parameterInfo['datatype_handler'] = async () => {
            const result = await field.checkDatatype();
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
 * @param {Array<Object.<string, any>>} parameters - Map of parameters
 */
function createInputListeners(parameters) {
    for (const parameterInfo of parameters) {
        const field = parameterInfo['parameter_info'];
        const handlerNames = ['mutually_exclusive_handler', 'datatype_handler', 'activation_handler', 'valid_submit_handler', 'datatype_dropdown_handler'];
        const handlers = handlerNames
            .map(name => parameterInfo[name])
            .filter(fn => typeof fn === 'function');

        if (handlers.length !== 0) {
            field.onChange(async (e) => {
                if (e) e.stopPropagation();
                for (const handler of handlers) {
                    await handler(e);
                }
            });
        }

        field.onFocus(async (event) => {
            if (event) event.stopPropagation();
            displayParameterInfo(field);
        });
    }
}

/**
 * Attaches an activation handler to needed parameters.
 * This covers required_if and forbidden_if keywords.
 *
 * @param allParameters Map of parameters.
 * @param {Object.<string, Array<ParameterField>|Object.<string, boolean>>} activationMap Maps what parameters are effected when changing one specific Parameter
 * @param {boolean} createActivationDependencyHandlers decides if the handler should be assigned. (Should only be true if the global layer is reached)
 */
function createActivationHandler(allParameters, activationMap, createActivationDependencyHandlers) {
    for (const parameter of allParameters) {
        const field = parameter['parameter_info'];
        const paramTriggers = field.getActivationTriggers();
        for (const trigger of paramTriggers) {
            if (trigger in activationMap) {
                activationMap[trigger].push(field);
            } else {
                activationMap[trigger] = [field];
            }
        }
    }

    if (createActivationDependencyHandlers) {
        activationMap["ACTIVATION_STATE"] = {}; // Store what parameters are considered "active"
        for (const parameter of allParameters) {
            const parameterName = parameter['name'];
            const toTrigger = activationMap[parameterName];
            const field = parameter['parameter_info'];
            if (toTrigger) {
                parameter['activation_handler'] = async () => {
                    toTrigger.forEach(item => {
                        let isShownBefore = item.isShown();
                        activationMap["ACTIVATION_STATE"][item.parameter['name']] = item.handleActivationTrigger(parameterName, field.getValue());
                        if (isShownBefore !== item.isShown()) item.refreshSubmitValidity();
                    });
                };
            }
        }
    }
}

/**
 * Dynamically creates input fields for all required and optional parameters of a test class.
 *
 * @param {Array<Object.<string, any>>} requiredParams List of required parameters
 * @param {Array<Object.<string, any>>} optionalParams List of optional parameters
 * @param {Array<Array<string>>} mutually_exclusive_bindings List of mutually exclusive bindings
 * @param {HTMLElement} requiredContainer - The DOM element to append required parameter fields into.
 * @param {HTMLElement} optionalContainer - The DOM element to append optional parameter fields into.
 * @param {HTMLElement} submitButton button that "finishes" the parameter selection
 * @param {Object.<string, Array<ParameterField>>} datatypeDependencyMap Map of parameters whose datatypes depend on each other.
 * @param {Object.<string, Array<ParameterField>>} activationDependencyMap Map of parameters that manages when a parameter is displayed.
 * @param {boolean} createActivationDependencyHandlers decides if the handler should be assigned. (Should only be true if the global layer is reached)
 * @param {function} extraSubmitValidity Function that is called for validating further submit requirements.
 */
async function showParameters(requiredParams, optionalParams, mutually_exclusive_bindings, requiredContainer, optionalContainer, submitButton, datatypeDependencyMap, activationDependencyMap, createActivationDependencyHandlers, extraSubmitValidity) {

    /**
     * Marks if a parameter's field currently has a valid input.
     * @type {Object.<any, any>}
     */
    let validInputMap = {};

    /** Marks if a parameter's field is currently blocked (unable to change value) */
    let currentlyBlockedMap = {};

    const allParameters = [...requiredParams, ...optionalParams];

    await createAndSaveParameterFields(requiredParams, optionalParams, datatypeDependencyMap, activationDependencyMap);
    createMutuallyExclusiveHandler(allParameters, mutually_exclusive_bindings, currentlyBlockedMap);
    createDatatypeHandler(allParameters, validInputMap);
    createSubmitHandler(allParameters, validInputMap, currentlyBlockedMap, activationDependencyMap, submitButton, extraSubmitValidity);
    createActivationHandler(allParameters, activationDependencyMap, createActivationDependencyHandlers);
    createInputListeners(allParameters);

    for (const parameterInfo of allParameters.values()) {
        parameterInfo['mutually_exclusive_handler']?.();
        await parameterInfo['datatype_handler']();
    }

    loadParameterFieldsIntoDocument(allParameters, requiredContainer, optionalContainer);


    checkSubmitValidity(allParameters, validInputMap, currentlyBlockedMap, activationDependencyMap, submitButton, extraSubmitValidity);
}


// Initialization
let previousTestClass = ""; // Store last TestClass to avoid recreating same parameter-fields
let settingUp = false; // Locks up TestClass selection while fields are being created

/**
 * "Selects" the given test class for further handling.
 *
 * @param {string} testClass The test class to select.
 */
async function selectTestClass(testClass) {
    if (settingUp) return; // Lock method from being used at the same time
    settingUp = true;
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
    let parameters;
    try {
        parameters = await fetchTestParameters(testClass);
    } catch (error) {
        throwException(error.message);
    }

    let requiredParameters = parameters.requiredParams;
    let optionalParameters = parameters.optionalParams;

    await showParameters(
        requiredParameters,
        optionalParameters,
        parameters.mul,
        requiredContainer,
        optionalContainer,
        submitParametersButton,
        {},
        {},
        true,
        undefined
    );

    submitParametersButton.addEventListener("click", () => {
        selectParameters(requiredParameters, optionalParameters)
    });

    settingUp = false;
}


/**
 * Throws an Exception
 * @param message The message to display
 */
function throwException(message) {
    throw new Error(message);
}

/** Enables the given button */
function enableSubmit(button) {
    button.disabled = false;
}

/** Disables the given button */
function disableSubmit(button) {
    button.disabled = true;
}