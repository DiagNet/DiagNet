/* Handles Datatype-Checks */

let allDevices = []

/**
 * Checks whether the value of a given input field matches the specified datatype.
 *
 * @async
 * @param {HTMLElement} field The input field to validate.
 * @param {string} datatype_as_string Expected datatype as a string.
 * @returns {Promise<boolean|undefined>} Resolves to:
 *   - true if the field's value matches the datatype,
 *   - false if it does not match,
 *   - undefined if the field is empty.
 */
async function checkDatatype(field, datatype_as_string) {
    const value = field.value.trim();
    if (value.length === 0) {
        return undefined;
    }
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
}

/**
 * Marks an input field as having a correct datatype.
 *
 * @param {HTMLElement} field The input field to update.
 */
function correctDatatype(field) {
    field.style.border = "2px solid green";
}

/**
 * Marks an input field as having an incorrect datatype by setting a red border.
 *
 * @param {HTMLElement} field The input field to update.
 */
function wrongDatatype(field) {
    field.style.border = "2px solid red";
}

/**
 * Checks whether the value of a given input field matches the specified datatype.
 *
 * @async
 * @param {ParameterField} field The input field to validate.
 * @param {string} datatype_as_string Expected datatype as a string.
 * @returns {Promise<string>} Resolves to true if the field's value matches the datatype, false otherwise.
 */
async function handleCheckDataType(field, datatype_as_string) {
    let result = await checkDatatype(field.getField(), datatype_as_string);
    if (result === undefined) {
        field.unknownDatatype();
        return "unknown";
    } else if (result) {
        field.correctDatatype();
        return "success";
    } else {
        field.wrongDatatype();
        return "fail";
    }
}