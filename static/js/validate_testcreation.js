const submit = document.getElementById("submitParameters");

submit.addEventListener("click", read_parameter_input);

/** Reads values from input container */
function readInputs(containerId) {
    const container = document.getElementById(containerId);
    const inputs = container.querySelectorAll("input");
    const values = {};

    inputs.forEach(input => {
        values[input.name] = input.value; // store name: value
    });

    return values;
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

    // Merge them into a single object
    const payload = {
        test: selectedTestClass,
        required: requiredParams,
        optional: optionalParams
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