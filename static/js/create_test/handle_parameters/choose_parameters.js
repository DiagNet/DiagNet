/* Handles Parameters */
const chooseParametersContainer = document.getElementById("chooseParametersContainer");
const submitParametersButton = document.getElementById("submitParameters");
const parameterInfoContainer = document.getElementById('parameterInfoContainer');

/**
 * Checks if all parameters are valid and updates the submit button state.
 *
 * A parameter is considered valid if it is either valid in `validInputMap`
 * or currently blocked in `currentlyBlockedMap`.
 *
 * @param {Array<Object.<string, any>>} parameters - Map of parameters
 * @param {Object.<string, boolean>} validInputMap - Tracks each parameter's validity.
 * @param {Object.<string, boolean>} currentlyBlockedMap - Tracks which parameters are currently blocked/disabled.
 * @param {HTMLElement} submitButton that "finishes" the parameter selection.
 * @param {function} extraSubmitValidity Function that is called for validating further submit requirements.
 */
function checkSubmitValidity(parameters, validInputMap, currentlyBlockedMap, submitButton, extraSubmitValidity) {
    if (extraSubmitValidity && !extraSubmitValidity()) {
        disableSubmit(submitButton);
        return;
    }

    for (const key in validInputMap) {
        const valueA = validInputMap[key];
        const valueB = currentlyBlockedMap[key] || false;
        let valueC = true; // default is true
        if (activationDependencyMap["ACTIVATION_STATE"]) {
            let activationState = activationDependencyMap["ACTIVATION_STATE"][key];
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
 * @param {HTMLElement} submitButton that "finishes" the parameter selection
 * @param {function} extraSubmitValidity Function that is called for validating further submit requirements.
 */
function createSubmitHandler(parameters, validInputMap, currentlyBlockedMap, submitButton, extraSubmitValidity) {
    for (const parameterInfo of parameters) {
        parameterInfo['valid_submit_handler'] = () => {
            checkSubmitValidity(parameters, validInputMap, currentlyBlockedMap, submitButton, extraSubmitValidity);
        };
    }
}


/**
 * Appends parameter input fields to a DOM container.
 *
 * @param {Array<Object.<string, any>>} parameters - Map of parameters
 * @param {HTMLElement} container - The DOM element to append parameter fields into.
 */
function loadParameterFieldsIntoDocument(parameters, container) {
    const fragment = document.createDocumentFragment();

    parameters.forEach(param => {
        const field = param['parameter_info'].getField();
        fragment.appendChild(field);
    });

    container.appendChild(fragment);
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
 * @returns {ParameterField} The created ParameterField
 */
function createParameterFields(parameter) {
    const datatypes = (Array.isArray(parameter['type']) ? parameter['type'] : [parameter['type']])
        .map(d => typeof d === "string" ? d.trim().toLowerCase() : d);

    if (datatypes.includes("choice")) return new ChoiceField(parameter);
    else if (datatypes.includes("list")) return new ListField(parameter);
    else if (datatypes.includes("device")) return new SingleLineDeviceField(parameter);
    else return new SingleLineInputField(parameter);
}

/**
 * Creates DOM input fields for parameters and stores them in each parameter's map.
 *
 * @param {Array<Object.<string, any>>} parameters - Map of parameters.
 * */
async function createAndSaveParameterFields(parameters) {
    for (const parameterInfo of parameters) {
        if (parameterInfo === null || typeof parameterInfo !== "object" || Array.isArray(parameterInfo)) {
            throw new Error("Parameters can only be defined as a map like structure: Consider changing the test definition");
        }
        let inputField = createParameterFields(parameterInfo);
        await inputField.createField();
        parameterInfo['parameter_info'] = inputField;
        if (parameterInfo['requirement'] !== "optional") {
            parameterInfo['requirement'] = "required";
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
            if (!paramName) throw new Error("No name found for given parameter: Consider adding the 'name' field in the test definition");
            if (typeof paramName !== "string") throw new Error("Parameter name has to be a string: Consider adding a valid 'name' field in the test definition");
            if (searchNames.has(paramName)) {
                output[paramName] = param;
                foundNamesCount += 1;
            }
        }
        if (foundNamesCount !== searchNames.size) {
            throw new Error("Mutually-Exclusive-Binding parameter not found as an actual Parameter");
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
            throw new Error("No name found for given parameter: Consider adding the 'name' field in the test definition");
        }
        if (!parameterType) {
            throw new Error(`No datatype found for parameter ${parameterName}: Consider adding the 'type' field in the test definition`);
        }

        const validateResultBasedOnRequirement = {
            required: result => result === DATATYPE_RESULT.SUCCESS,
            optional: result => result === DATATYPE_RESULT.SUCCESS || result === DATATYPE_RESULT.UNKNOWN
        };

        parameterInfo['datatype_handler'] = async (event) => {
            const result = await field.checkDatatype();
            const previousCheck = validInputMap[parameterName];
            validInputMap[parameterName] = validateResultBasedOnRequirement[requirement](result);
            if (event && previousCheck === validInputMap[parameterName]) event.validInputChanged = true;
        };
    }
}

/**
 * Displays Info about the current Parameter in the info tab.
 * @param {ParameterField|ListField} parameter The parameter to fetch the info from.
 * @param {HTMLElement} container The Container to put the information in.
 */
function displayParameterInfo(parameter, container) {
    container.classList.remove('hidden');
    container.innerHTML = "";
    parameter.getInfo(previousTestClass, container);
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
            if (event.noAction) return; // Stop parent elements to steal focus and display their info.
            event.noAction = true;
            displayParameterInfo(field, parameterInfoContainer);
        });
    }
}

/**
 * Attaches an activation handler to needed parameters.
 * This covers required_if and forbidden_if keywords.
 *
 * @param allParameters Map of parameters.
 */
function createActivationHandler(allParameters) {
    for (const parameter of allParameters) {
        const field = parameter['parameter_info'];
        const paramTriggers = field.getActivationTriggers();
        for (const trigger of paramTriggers) {
            if (trigger in activationDependencyMap) {
                activationDependencyMap[trigger].push(field);
            } else {
                activationDependencyMap[trigger] = [field];
            }
        }
    }

    activationDependencyMap["ACTIVATION_STATE"] = {}; // Store what parameters are considered "active"
    for (const parameter of allParametersDisplayed) {
        const parameterName = parameter['name'];
        const toTrigger = activationDependencyMap[parameterName];
        const field = parameter['parameter_info'];
        if (toTrigger) {
            parameter['activation_handler'] = async () => {
                toTrigger.forEach(item => {
                    let isShownBefore = item.isShown();
                    activationDependencyMap["ACTIVATION_STATE"][item.parameter['name']] = item.handleActivationTrigger(parameterName, field.getValue());
                    if (isShownBefore !== item.isShown()) item.refreshSubmitValidity();
                });
            };
        }
    }
}

/**
 * Transforms the datatype_strings of parameters into the Datatype Format.
 * @param parameters List of all parameters, used for checking conditions
 */
function loadDatatypes(parameters) {
    for (const parameter of parameters) {

        const datatypeObjects = [];

        const datatypes = Array.isArray(parameter['type']) ? parameter['type'] : [parameter['type']];
        for (let i = 0; i < datatypes.length; i++) {
            const datatype = datatypes[i];
            if (datatype && datatype.constructor === Object) {
                datatypeObjects.push(Datatype.toDatatype(datatype['name'], parameter['parameter_info'], datatype['condition'], parameters));
            } else if (typeof datatype === 'string') {
                datatypeObjects.push(Datatype.toDatatype(datatype));
            } else {
                throw new Error("Unknown datatype format. (Class definition seems to be wrong?) " + datatype);
            }
        }
        parameter['type'] = datatypeObjects;
    }
}

/**
 * Dynamically creates input fields for all required and optional parameters of a test class.
 *
 * @param {Array<Object.<string, any>>} parameters List of parameters
 * @param {Array<Array<string>>} mutually_exclusive_bindings List of mutually exclusive bindings
 * @param {HTMLElement} parameterContainer - The DOM element to append parameter fields into.
 * @param {HTMLElement} submitButton button that "finishes" the parameter selection
 * @param {function} extraSubmitValidity Function that is called for validating further submit requirements.
 */
async function showParameters(parameters, mutually_exclusive_bindings, parameterContainer, submitButton, extraSubmitValidity) {
    allParametersDisplayed.push(...parameters);

    /**
     * Marks if a parameter's field currently has a valid input.
     * @type {Object.<any, any>}
     */
    let validInputMap = {};

    /** Marks if a parameter's field is currently blocked (unable to change value) */
    let currentlyBlockedMap = {};

    await createAndSaveParameterFields(parameters);
    createMutuallyExclusiveHandler(parameters, mutually_exclusive_bindings, currentlyBlockedMap);
    createDatatypeHandler(parameters, validInputMap);
    createSubmitHandler(parameters, validInputMap, currentlyBlockedMap, submitButton, extraSubmitValidity);

    for (const parameterInfo of parameters.values()) {
        parameterInfo['mutually_exclusive_handler']?.();
        await parameterInfo['datatype_handler']();
    }

    loadParameterFieldsIntoDocument(parameters, parameterContainer);

    checkSubmitValidity(parameters, validInputMap, currentlyBlockedMap, submitButton, extraSubmitValidity);
}


// Initialization
let activationDependencyMap = {};
let allParametersDisplayed = [];
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
    chooseParametersContainer.innerHTML = "";

    // Fetch needed parameters
    let parameters;
    try {
        parameters = await fetchTestParameters(testClass);
    } catch (error) {
        reset();
        throw new Error("Could not fetch test parameters: " + error.message);
    }
    if (!Array.isArray(parameters.parameters)) {
        reset();
        throw new Error("Given parameters have to be contained in a list: Consider adding a valid test definition");
    }


    let allParameters = parameters.parameters;

    if (allParameters.length === 0) {
        reset();
        throw new Error("Test-Class needs to contain at least 1 parameter");
    }


    allParametersDisplayed = [];
    activationDependencyMap = {};
    try {
        await showParameters(
            allParameters,
            parameters.mul,
            chooseParametersContainer,
            submitParametersButton,
            undefined
        );

        // Creates Activation listeners for all Parameters
        createActivationHandler(allParametersDisplayed);

        // Creates the input listeners for all Parameters
        createInputListeners(allParametersDisplayed);

        // Convert string-datatypes into Datatypes
        loadDatatypes(allParametersDisplayed);
    } catch (e) {
        reset();
        throw e;
    }

    allParametersDisplayed.forEach(parameter => {
        parameter['parameter_info'].afterCreatingField();
    });

    submitParametersButton.addEventListener("click", () => {
        selectParameters(allParameters);
    });

    // Activate navigation towards parameter tab
    paramTab.classList.remove('disabled');
    paramTab.disabled = false;
    paramTab.click();
    paramTab.setAttribute('tabindex', '0');

    settingUp = false;
}

/** Function called upon Error. */
function reset() {
    settingUp = false;
    previousTestClass = "";
    paramTab.classList.add('disabled');
    paramTab.disabled = true;
    paramTab.setAttribute('tabindex', '-1');
}

/** Enables the given button */
function enableSubmit(button) {
    button.disabled = false;
}

/** Disables the given button */
function disableSubmit(button) {
    button.disabled = true;
}