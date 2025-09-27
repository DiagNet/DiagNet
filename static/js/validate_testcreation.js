const submit = document.getElementById("submitParameters");

submit.addEventListener("click", read_parameter_input);

/**
 * Read non-empty inputs from a container and collect device-type inputs separately.
 *
 * @param {string} containerId - ID of the container element.
 * @returns {{values: Object, device_parameters: string[]}} Map of input names to values and list of device values.
 */
function readInputs(containerId) {
    const container = document.getElementById(containerId);
    const inputs = container.querySelectorAll("input");
    const values = {};        // map of all non-empty inputs
    const device_parameters = [];       // list of inputs with data-type="device"

    inputs.forEach(input => {
        if (input.value.length !== 0) {
            values[input.name] = input.value;

            if (input.dataset.datatype.trim().toLowerCase() === "device") {
                device_parameters.push(input.dataset.param_name);
            }
        }
    });

    return {values, device_parameters};
}


/** Needed for Django in order to not get a 403 Forbidden Error and to prevent CSRF Attacks. */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/** Reads the parameter inputs and returns them as a map. */
async function read_parameter_input() {
    const requiredParams = readInputs("requiredParamsContainer");
    const optionalParams = readInputs("optionalParamsContainer");

    const allDeviceParameters = [...requiredParams.device_parameters, ...optionalParams.device_parameters];

    const payload = {
        test_class: selectedTestClass,
        required_parameters: requiredParams.values,
        optional_parameters: optionalParams.values,
        device_parameters: allDeviceParameters
    };

    try {
        const response = await fetch("/networktests/api/create/test", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken")
            },
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (response.ok && result.status === "success") {
            alert("Submission successful!");
        } else {
            console.error("Error:", result.message || "Unknown error");
        }
    } catch (err) {
        console.error("Error sending parameters:", err);
    }
}