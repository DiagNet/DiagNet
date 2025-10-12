const submitParametersButton = document.getElementById("submitParameters");

function fieldIsEmpty(field) {
    return field.value.length === 0;
}

function fieldChangedFromEmptyToValue(field) {
    return field.value.length === 1;
}

function getFieldValue(field) {
    return field.value;
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


function executeOnInputChange(field, func) {
    if (!(field instanceof HTMLElement)) return;
    field.addEventListener('input', func);
}
/**
 * "Enables" the given input field. (used for mutually exclusive fields)
 *
 * @param {HTMLElement} field The field to enable.
 */
function enableField(field) {
    field.disabled = false;
    field.readOnly = false;
}

/**
 * "Disables" the given input field. (used for mutually exclusive fields)
 *
 * @param {HTMLElement} field The field to disable.
 */
function disableField(field) {
    field.disabled = true;
    field.readOnly = true;
}

/**
 * Creates a parameter field based on the specified type.
 *
 * @param {Map<string, Map<string, any>>} parameter - The parameter to handle
 * @param {function} showParameters Used to create more input fields when a list object is parsed.
 * @returns {Object} The parameter field object corresponding to the given type.
 */
function createParameterFields(parameter, showParameters) {

    let paramName = parameter.get('name');
    let datatype = parameter.get('type');
    let type = parameter.get('requirement');



    input = document.createElement("input");
    input.type = "text";
    input.className = "form-control mb-2";
    input.placeholder = paramName

    return input;
}