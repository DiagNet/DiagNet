/**
 * Simulates an Enum. Displays Datatype-checking-results.
 * @type {{UNKNOWN: string, SUCCESS: string, FAIL: string}}
 */
const DATATYPE_RESULT = {
    UNKNOWN: "unknown",
    SUCCESS: "success",
    FAIL: "fail"
};

/** Device Datatype */
class Device extends Datatype {
    /**
     * Checks if the given value matches the datatype.
     * @param value The value to be checked.
     */
    check(value) {
        return allDevices.includes(value);
    }

    getDescription() {
        return "Device Datatype - Work in Progress";
    }

    toString() {
        return "device";
    }

    displayName() {
        return "Device";
    }
}

let allDevices = [];

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