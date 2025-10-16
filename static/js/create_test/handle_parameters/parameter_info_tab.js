const parameterInfoContainer = document.getElementById('parameterInfoContainer');

const parentName = document.getElementById("infoTabParentName");
const parentDescription = document.getElementById("infoTabParentDescription");

const datatypeName = document.getElementById("infoTabDatatypeName");

const inputDescription = document.getElementById("infoTabInputLabel");
const inputContainer = document.getElementById("infoTabInputContainer");


/**
 * Displays Info about the current Parameter in the info tab.
 * @param {ParameterField} parameter
 */
function displayParameterInfo(parameter) {
    switch (parameter.parameter['type']) {
        case 'list':
            displayListParameterInfo(parameter);
            break;
        default:
            displayParameterInfo(parameter);
    }
}


/**
 * Displays Info about a given List Parameter.
 * @param {ParameterField} parameter The Parameter
 */
function displayListParameterInfo(parameter) {

}

/**
 * Displays Info about a given Parameter.
 * @param {ParameterField} parameter The Parameter
 */
function displayDefaultParameterInfo(parameter) {

}