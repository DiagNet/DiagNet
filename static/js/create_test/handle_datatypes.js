/* Handles Datatype-Checks */

let allDevices = []
let datatypeStatus = new Map();

/**
 * Checks whether the value of a given input field matches the specified datatype.
 *
 * @async
 * @param {HTMLElement} field The input field to validate.
 * @param {string} datatype_as_string Expected datatype as a string.
 * @returns {Promise<boolean>} Resolves to true if the field's value matches the datatype, false otherwise.
 */
async function checkDatatype(field, datatype_as_string) {
    const value = field.value.trim();
    if (allDevices.length === 0 && datatype_as_string.trim().toLowerCase() === "device") {
        allDevices = await fetchAllDevices();
    }
    switch (datatype_as_string.toLowerCase()) {
        case "device":
            return allDevices.includes(value);

        case "string":
        case "str":
            return true

        case "number":
        case "int":
        case "float":
            return !isNaN(value) && value !== "";

        case "ipv4address":
        case "ipv4":
            const ipv4Regex = /^(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}$/;
            return ipv4Regex.test(value);

        default:
            return true
    }
}

/**
 * Marks an input field as having an unknown datatype.
 *
 * @param {HTMLElement} field The input field to update.
 */
function unknownDatatype(field) {
    field.style.border = "";
    datatypeStatus.set(field, true);
}

/**
 * Marks an input field as having a correct datatype.
 *
 * @param {HTMLElement} field The input field to update.
 */
function correctDatatype(field) {
    field.style.border = "2px solid green";
    datatypeStatus.set(field, true);
}

/**
 * Marks an input field as having an incorrect datatype by setting a red border.
 *
 * @param {HTMLElement} field The input field to update.
 */
function wrongDatatype(field) {
    field.style.border = "2px solid red";
    datatypeStatus.set(field, false);
}

/**
 * Handles a DOM field's value by checking its datatype and updating its visual state.
 *
 * @async
 * @param {HTMLElement} field The input field or DOM element to check.
 * @param {string|null} datatype_as_string The expected datatype as a string. If null, treated as unknown.
 */
async function handleCheckDataType(field, datatype_as_string) {
    if (datatype_as_string == null) {
        unknownDatatype(field);
        return "unknown";
    } else if (await checkDatatype(field, datatype_as_string)) {
        correctDatatype(field);
        return "success";
    } else {
        wrongDatatype(field);
        return "fail";
    }
}