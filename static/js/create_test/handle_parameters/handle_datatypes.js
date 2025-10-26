/* Handles Datatype-Checks */

let allDevices = []
let cacheParameterValues = {}

/**
 * Syntax used to describe a value being used by another datatype definition. <br>
 * For Example: type: CIDR-value(type) | Where type is the name of a parameter
 */
const parameterDatatypeDependencyRegex = /value\(([^)]+)\)/;

/**
 * Checks whether the value of a given input field matches the specified datatypes.
 *
 * @async
 * @param {string} value The value to validate.
 * @param {Array<string>} datatypes Expected datatypes as a list.
 * @returns {Promise<boolean|undefined>} Resolves to:
 *   - true if the field's value matches any of the datatypes
 *   - false if it does not match for any datatype
 */
async function beforeDatatypeCheck(value, datatypes) {
    for (const datatype of datatypes) {
        if (await checkDatatype(value, fetchDatatypeValueInfo(datatype))) {
        return true;
        }
    }
    return false;
}

/**
 * Checks if the value matches the given datatype.
 * @param {string} value The value to check.
 * @param {string} datatype The datatype used for checking.
 * @returns {Promise<boolean>} true, if they match, otherwise false.
 */
async function checkDatatype(value, datatype) {
    if (datatype.trim().toLowerCase() === "device") {
        await updateDevices();
    }

    switch (datatype.toLowerCase()) {
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

        case "cidr-ipv4":
            // z.B. 192.168.0.1/24
            const cidrIpv4Regex = /^(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}\/([0-9]|[1-2][0-9]|3[0-2])$/;
            return cidrIpv4Regex.test(value);

        case "ipv6address":
        case "ipv6":
            // einfache IPv6 Prüfung, volle und verkürzte Schreibweise
            const ipv6Regex = /^(([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|(::([0-9a-fA-F]{1,4}:){0,5}[0-9a-fA-F]{1,4}))$/;
            return ipv6Regex.test(value);

        case "cidr-ipv6":
            // IPv6 CIDR, z.B. 2001:db8::/32
            const cidrIpv6Regex = /^(([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|(::([0-9a-fA-F]{1,4}:){0,5}[0-9a-fA-F]{1,4}))\/([0-9]|[1-9][0-9]|1[0-1][0-9]|12[0-8])$/;
            return cidrIpv6Regex.test(value);

        default:
            return true
    }
}

/**
 * If the datatype needs a value that was previously cached it is inserted here.
 * @param datatype datatype to check for cached values.
 */
function fetchDatatypeValueInfo(datatype) {
    const match = datatype.match(parameterDatatypeDependencyRegex);
    if (match) {
        const toBeLookedUp = match[1];
        if (toBeLookedUp in cacheParameterValues) {
            return datatype.replace(parameterDatatypeDependencyRegex, cacheParameterValues[toBeLookedUp]);
        }
    }
    return datatype;
}

/**
 * For every field whose datatype dependents on the given field, this method calls triggerInputValidation().
 * @param field The given field.
 */
function triggerInputValidationForDependentFields(field) {
    for (const dependentField of field.datatypeDependencyMap[field.get('name')]) {
        dependentField.triggerInputValidation();
    }
}

/** Caches a value */
async function cacheValue(field, value) {
    const parameterName = field.get('name');
    cacheParameterValues[parameterName] = value;
    triggerInputValidationForDependentFields(field);
}

/** Uncaches a value */
async function uncacheValue(field) {
    const parameterName = field.get('name');
    if (parameterName in cacheParameterValues) {
        delete cacheParameterValues[parameterName];
        triggerInputValidationForDependentFields(field);
    }
}

/** Fetches the available devices. */
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
 * @param {Parameter_field} field The input field to validate.
 * @param {string} datatype Expected datatype(s) as a string.
 * @returns {Promise<string>} Resolves to true if the field's value matches the datatype, false otherwise.
 */
async function handleCheckDataType(field, datatype) {
    let value = field.getValue().trim();
    if (value.length === 0) {
        field.unknownDatatype();
        await uncacheValue(field);
        return DATATYPE_RESULT.UNKNOWN;
    }

    let result = await beforeDatatypeCheck(value, field.getType());
    if (result) {
        await cacheValue(field, value);
        field.correctDatatype();
        return DATATYPE_RESULT.SUCCESS;
    } else {
        await uncacheValue(field);
        field.wrongDatatype();
        return DATATYPE_RESULT.FAIL;
    }
}