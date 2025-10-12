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
 * @param {"list"|"singleChoice"|"multiChoice"} type - The type of parameter field to create.
 * @returns {Object} The parameter field object corresponding to the given type.
 */
function createParameterFields(parameter) {
    let input = null
    let paramName = parameter.get('name');
    let datatype = parameter.get('type');
    let type = parameter.get('requirement');

    input = document.createElement("input");
    input.type = "text";
    input.className = "form-control mb-2";
    input.placeholder = paramName

    input.name = paramName;
    input.id = paramName;
    input.dataset.datatype = datatype;
    input.dataset.paramName = paramName;

    input.dataset.type = type;
    if (type === "required") {
        requiredStatus.set(input, false);
    }
    datatypeStatus.set(input, true);

    return input;
}