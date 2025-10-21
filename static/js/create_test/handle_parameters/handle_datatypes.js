/* Handles Datatype-Checks */

let allDevices = []
let cacheParameterValues = {}

/**
 * Checks whether the value of a given input field matches the specified datatype.
 *
 * @async
 * @param {string} value The value to validate.
 * @param {string} datatype_as_string Expected datatype as a string.
 * @returns {Promise<boolean|undefined>} Resolves to:
 *   - true if the field's value matches the datatype,
 *   - false if it does not match,
 *   - undefined if the field is empty.
 */
async function checkDatatype(value, datatype_as_string) {
    if (allDevices.length === 0 && datatype_as_string.trim().toLowerCase() === "device") {
        await updateDevices();
    }
    datatype_as_string = insertCachedValuesIntoDatatypeIfNeeded(datatype_as_string);
    console.log("checking datatype: " + datatype_as_string);
    console.log("currect cache: " + cacheParameterValues);
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
 * If the datatype needs a previously cached value it is inserted here.
 * @param datatype datatype to check for cached values.
 */
function insertCachedValuesIntoDatatypeIfNeeded(datatype) {
    const match = datatype.match(/value\(([^)]+)\)/);
    if (match) {
        const toBeLookedUp = match[1];
        if (toBeLookedUp in cacheParameterValues) {
            return datatype.replace(/value\([^)]+\)/, cacheParameterValues[toBeLookedUp]);
        }
    }
    return datatype;
}

// Methods for caching Values
async function cacheValue(name, value) {
    cacheParameterValues[name] = value;
}

async function uncacheValue(name) {
    delete cacheParameterValues[name];
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
    let value = field.getValue().trim();
    if (value.length === 0) {
        field.unknownDatatype();
        await uncacheValue(field.parameter['name']);
        return DATATYPE_RESULT.UNKNOWN;
    }

    let result = await checkDatatype(value, datatype_as_string);
    if (result) {
        console.log("put in cache");
        console.log(field.parameter['name']);
        console.log(value);
        await cacheValue(field.parameter['name'], value);
        field.correctDatatype();
        return DATATYPE_RESULT.SUCCESS;
    } else {
        await uncacheValue(field.parameter['name']);
        field.wrongDatatype();
        return DATATYPE_RESULT.FAIL;
    }
}