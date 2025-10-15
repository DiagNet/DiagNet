const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;

/**
 * Fetches the required and optional parameters for a given test class from the API.
 *
 * @async
 * @param {string} testClass The name of the test class to fetch parameters for.
 * @returns {Promise<{requiredParams: Array<Object.<string, any>>, optionalParams: Array<Object.<string, any>>, mul: Array<Array<string>>}>}
 *   Resolves to an object containing arrays of required and optional parameters,
 *   and mutually exclusive parameter groups (`mul`).
 */
async function fetchTestParameters(testClass) {
    if (!testClass) return {requiredParams: [], optionalParams: [], mul: null};

    const res = await fetch(`/networktests/api/search/test/parameters?test_class=${encodeURIComponent(testClass)}`);
    const data = await res.json();

    return {
        requiredParams: data.required,
        optionalParams: data.optional,
        mul: data.mul_exclusive || []
    };
}

/**
 * Fetches all available test classes from the backend API once
 * and stores them locally in `allTestClasses`.
 */
async function fetchAllTestClasses() {
    try {
        const res = await fetch(`/networktests/api/get/tests`);
        const data = await res.json();
        allTestClasses = data.results || [];
    } catch (err) {
        console.error("Search API error:", err);
        return [];
    }
}

/**
 * Fetches the list of all devices from the API.
 *
 * @async
 * @returns {Promise<string[]>} An array of device names. Returns an empty array if the request fails or no results are returned.
 */
async function fetchAllDevices() {
    try {
        const res = await fetch(`/devices/all`);
        const data = await res.json();

        return data.results || []
    } catch (err) {
        console.error("Search API error:", err);
        return []
    }
}

function mapToObj(input) {
    if (input instanceof Map) {
        const obj = {};
        for (const [k, v] of input) {
            obj[k] = mapToObj(v); // recursive
        }
        return obj;
    } else if (Array.isArray(input)) {
        return input.map(mapToObj);
    } else if (input && input.constructor === Object) {
        const obj = {};
        for (const key in input) {
            obj[key] = mapToObj(input[key]);
        }
        return obj;
    }
    return input;
}

/**
 * Sends a test creation request to the backend API.
 *
 * @async
 * @param {string} testClass The name of the test class.
 * @param {Object} requiredParams Map of required parameter names to values.
 * @param {Object} optionalParams Map of optional parameter names to values.
 * @param {string[]} deviceParams List of device parameter names.
 * @param {string} label The label associated with the test class.
 * @param {boolean} expectedResult If the test class is supposed to pass (true) or fail (false).
 */
async function createTest(testClass, requiredParams, optionalParams, deviceParams, label, expectedResult) {
    const payload = {
        test_class: testClass,
        required_parameters: requiredParams,
        optional_parameters: optionalParams,
        device_parameters: deviceParams,
        label: label,
        expected_result: expectedResult
    };

    try {
        const response = await fetch("/networktests/api/create/test", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken
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


/**
 * Fetches information for a given test class from the API.
 *
 * @async
 * @param {string} testClassName - The name of the test class to fetch information for.
 * @returns {Promise<Object>} The results object from the API. Returns an empty object if the request fails.
 */
async function fetchTestClassInfoAPI(testClassName) {
    try {
        const res = await fetch(`/networktests/api/get/test/info?name=${encodeURIComponent(testClassName)}`);
        const data = await res.json();
        return data.results || {};
    } catch (err) {
        console.error("Failed to fetch test class info:", err);
        return {};
    }
}

/**
 * Returns a debounced version of a function that delays execution
 * until after `delay` milliseconds have passed since the last call.
 * (used for not having to search Test-Cases every input)
 *
 * @param fn Function to debounce.
 * @param delay Delay in milliseconds.
 * @returns Debounced function.
 */
function debounce(fn, delay) {
    let timeout;
    return (...args) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => fn(...args), delay);
    };
}

