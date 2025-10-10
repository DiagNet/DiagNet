/* Handles Parameters */

let previousTestClass = "";
let settingUp = false;

const paramTab = document.getElementById('parameters-tab');
let requiredContainer = document.getElementById("requiredParamsContainer");
let optionalContainer = document.getElementById("optionalParamsContainer");
let submitParametersButton = document.getElementById("submitParameters");

let requiredStatus = new Map();

// Set-up parameter fields
/**
 * "Enables" the given input field.
 *
 * @param {HTMLElement} field The field to enable.
 */
function enableField(field) {
    field.disabled = false;
    field.readOnly = false;
}

/**
 * "Disables" the given input field.
 *
 * @param {HTMLElement} field The field to disable.
 */
function disableField(field) {
    field.disabled = true;
    field.readOnly = true;
}


/**
 * Sets up mutually exclusive behavior for parameter input fields.
 *
 * @async
 * @param {Map<string, HTMLElement>} paramFields Map of parameter names to their input elements.
 * @param {Array<Array<string>>} mutuallyExclusiveGroups Array of mutually exclusive parameter groups.
 * @param {Map<string, string>} paramDatatypes Map of parameter names to datatypes.
 */
async function createMutuallyExclusiveDatatypeBindings(paramFields, mutuallyExclusiveGroups, paramDatatypes) {

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

    let calculateMutNeighbors = new Map()
    mutuallyExclusiveGroups.forEach(pair => {
        const allFields = pair.map(v => paramFields.get(v));

        for (const field of allFields) {
            if (!calculateMutNeighbors.has(field)) {
                calculateMutNeighbors.set(field, new Set(allFields));
            } else {
                const s = calculateMutNeighbors.get(field);
                allFields.forEach(f => s.add(f));
            }
        }
    });

    // Datatype and group handling for mutually exclusive group fields.
    for (const [field, allFieldsSet] of calculateMutNeighbors.entries()) {
        if (field.tagName.toLowerCase() === "select") {
            field.addEventListener("change", async () => {
                const allFields = [...allFieldsSet];
                if (field.value.length === 0) {
                    enableAllFields(allFields);
                    await handleCheckDataType(field, null);
                } else {
                    togglePair(field, allFields);
                    await handleCheckDataType(field, paramDatatypes.get(field.id));
                }
                checkRequiredParameters(allFields);
                checkSubmitLegality();
            });
        } else {
            field.addEventListener("input", async () => {
                const allFields = [...allFieldsSet];
                if (field.value.length === 0) {
                    enableAllFields(allFields);
                    await handleCheckDataType(field, null);
                } else if (field.value.length === 1) { // Could be improved, length from 2 to 1 is a redundant operation here, but this is simple
                    togglePair(field, allFields);
                    await handleCheckDataType(field, paramDatatypes.get(field.id));
                } else {
                    await handleCheckDataType(field, paramDatatypes.get(field.id));
                }
                checkRequiredParameters(allFields);
                checkSubmitLegality();
            });
        }
    }

    // Datatype handling for non mutually exclusive group fields.
    for (const [param, field] of paramFields.entries()) {
        if (calculateMutNeighbors.has(field)) continue; // Mutually Exclusive candidate
        if (field.tagName.toLowerCase() === "select") {
            field.addEventListener("change", async () => {
                if (field.value.length === 0) {
                    await handleCheckDataType(field, null);
                } else {
                    await handleCheckDataType(field, paramDatatypes.get(param));
                }
                checkRequiredParameters([field]);
                checkSubmitLegality();
            });
        } else {
            field.addEventListener("input", async () => {
                if (field.value.length === 0) {
                    await handleCheckDataType(field, null);
                } else {
                    await handleCheckDataType(field, paramDatatypes.get(param));
                }
                checkRequiredParameters([field]);
                checkSubmitLegality();
            });
        }
    }
}

/**
 * Dynamically creates input fields for all required and optional parameters of a test class.
 *
 * @async
 * @param {string} testClass The name of the test class to generate inputs for.
 */
async function showParameters(testClass) {
    const testParameters = await fetchTestParameters(testClass);

    // Clear previous inputs
    requiredContainer.innerHTML = "";
    optionalContainer.innerHTML = "";

    const requiredParameters = new Map(testParameters.requiredParams.map(item => {
        const [part1, part2] = item.split(":");
        return [part1, part2];
    }));

    const optionalParameters = new Map(testParameters.optionalParams.map(item => {
        const [part1, part2] = item.split(":");
        return [part1, part2];
    }));

    // stores what input field corresponds to what param for mutually exclusive bindings.
    let paramFields = new Map();

    // Create inputs for required parameters
    for (const [param, datatype] of requiredParameters) {
        const newInputField = createParameterFields(param, datatype, "required");
        paramFields.set(param, newInputField);
        requiredContainer.appendChild(newInputField);
    }

    // Create inputs for required parameters
    for (const [param, datatype] of optionalParameters) {
        const newInputField = createParameterFields(param, datatype, "optional");
        paramFields.set(param, newInputField);
        optionalContainer.appendChild(newInputField);
    }

    await createMutuallyExclusiveDatatypeBindings(paramFields, testParameters.mul, new Map([...requiredParameters, ...optionalParameters]));
}

// Check if required parameters are parsed
/**
 * Checks the required input fields to determine if they meet the expected conditions.
 * Updates a global `requiredStatus` map with a boolean indicating legality for each field.
 *
 * @param {HTMLElement[]} fields - Array of input elements to check. The first element's dataset.type
 *                                 must be "required" for the check to proceed.
 */
function checkRequiredParameters(fields) {
    if (fields[0].dataset.type !== "required") return;

    let parsedParameters = Array.from(fields).filter(input => input.value.length !== 0).length;

    let legal = parsedParameters === 1;
    fields.forEach(input => requiredStatus.set(input, legal));
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
 * Checks if all required and datatype fields are valid and
 * enables or disables the submit button accordingly.
 */
function checkSubmitLegality() {
    if (Array.from(requiredStatus.values()).every(value => value === true) &&
        Array.from(datatypeStatus.values()).every(value => value === true
        )) {
        enableSubmit();
    } else {
        disableSubmit();
    }
}

// Initialization
/**
 * "Selects" the given test class for further handling.
 *
 * @param {string} testClass The test class to select.
 * @param {HTMLElement} popup The popup.
 */
async function selectTestClass(testClass, popup) {
    if (settingUp) return;
    popup.removeEventListener("keydown", onPopUpClickHandler);
    settingUp = true;
    requiredStatus.clear();
    datatypeStatus.clear();
    if (previousTestClass === testClass) { // Already loaded
        paramTab.disabled = false;
        paramTab.click();
        settingUp = false;
        return;
    }

    previousTestClass = testClass;

    while (requiredContainer.firstChild) {
        requiredContainer.removeChild(requiredContainer.firstChild);
    }
    while (optionalContainer.firstChild) {
        optionalContainer.removeChild(optionalContainer.firstChild);
    }

    paramTab.classList.remove('disabled');
    paramTab.disabled = false;
    paramTab.click();

    _ = await showParameters(testClass);
    checkSubmitLegality();
    settingUp = false;
}

/**
 * Automatically sets focus to the search input when the popup is clicked.
 * Used in EventListeners between the Test-Class and Parameter tab.
 *
 * @param {Event} e event Object
 */
function onPopUpClickHandler(e) {
    searchInput.focus()
}