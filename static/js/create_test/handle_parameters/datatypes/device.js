/** Device Datatype */
class Device extends Datatype {
    check(value) {
        return allDevices.includes(value);
    }

    getDescription() {
        return "Devices are machines that are created using the device page";
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