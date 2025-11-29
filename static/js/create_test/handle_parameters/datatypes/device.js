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
let deviceIdAndName = {};
let devicesAreBeingUpdated = false;

/** Fetches the available devices. */
async function updateDevices() {
    if (!devicesAreBeingUpdated && allDevices.length === 0) {
        devicesAreBeingUpdated = true;
        try {
            allDevices.length = 0;
            deviceIdAndName = await fetchAllDevices();
            deviceIdAndName.forEach(d => allDevices.push(d[0]));
            deviceIdAndName = Object.fromEntries(deviceIdAndName);
        } catch (error) {
            throwException(error.message);
        }
        devicesAreBeingUpdated = false;
    }
}