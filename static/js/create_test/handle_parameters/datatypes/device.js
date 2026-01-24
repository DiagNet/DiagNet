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

let devicesAreUpdated = false;
let updateDevicesPromise = null;

/** Fetches the available devices. */
async function updateDevices() {
  if (devicesAreUpdated) {
    return; // already updated
  }

  if (updateDevicesPromise) {
    // fetch in progress, return the same promise
    return updateDevicesPromise;
  }

  // Start fetching
  updateDevicesPromise = (async () => {
    try {
      allDevices.length = 0;
      deviceIdAndName = await fetchAllDevices();
      deviceIdAndName.forEach((d) => allDevices.push(d[0]));
      deviceIdAndName = Object.fromEntries(deviceIdAndName);
      devicesAreUpdated = true;
    } catch (error) {
      throwException(error.message);
      devicesAreUpdated = false;
    } finally {
      // clear the promise so future calls can refetch if needed
      updateDevicesPromise = null;
    }
  })();

  return updateDevicesPromise;
}
