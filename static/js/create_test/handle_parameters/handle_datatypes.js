/* Handles Datatype-Checks */

let allDevices = []

/**
 * Checks whether the value of a given input field matches the specified datatype.
 *
 * @async
 * @param {ParameterField} field The input field to validate.
 * @param {string} datatype_as_string Expected datatype as a string.
 * @returns {Promise<boolean|undefined>} Resolves to:
 *   - true if the field's value matches the datatype,
 *   - false if it does not match,
 *   - undefined if the field is empty.
 */
async function checkDatatype(field, datatype_as_string) {
    const value = field.getValue().trim();
    if (value.length === 0) {
        return undefined;
    }
    if (allDevices.length === 0 && datatype_as_string.trim().toLowerCase() === "device") {
        await updateDevices();
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

async function updateDevices() {
    if (allDevices.length === 0) {
        try {
            allDevices = await fetchAllDevices();
        } catch (error) {
            throwException(error.message);
        }
    }
}

/**
 * Simulates an Enum. Displays Datatype-checking-results.
 * @type {{UNKNOWN: string, SUCCESS: string, FAIL: string}}
 */
const DATATYPE_RESULT = {
    UNKNOWN: "unknown",
    SUCCESS: "success",
    FAIL: "fail"
};

/**
 * Checks whether the value of a given input field matches the specified datatype.
 *
 * @async
 * @param {ParameterField} field The input field to validate.
 * @param {string} datatype_as_string Expected datatype as a string.
 * @returns {Promise<string>} Resolves to true if the field's value matches the datatype, false otherwise.
 */
async function handleCheckDataType(field, datatype_as_string) {
    let result = await checkDatatype(field, datatype_as_string);
    if (result === undefined) {
        field.unknownDatatype();
        return DATATYPE_RESULT.UNKNOWN;
    } else if (result) {
        field.correctDatatype();
        return DATATYPE_RESULT.SUCCESS;
    } else {
        field.wrongDatatype();
        return DATATYPE_RESULT.FAIL;
    }
}