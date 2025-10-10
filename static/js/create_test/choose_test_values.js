const createTestButton = document.getElementById('createTest')
const labelInput = document.getElementById('labelInput');
const expectedResult = document.getElementById('expectedResult');
const infoTab = document.getElementById('info-tab');

submitParametersButton.addEventListener("click", selectParameters);

labelInput.addEventListener("input", checkTestValueInputs);

let setupParams = false;
let currentRequiredParams = []
let currentOptionalParams = []
let allDevicesParameters = []

createTestButton.addEventListener("click", async () => {
    if (setupParams) {
        return;
    }
    await createTest(
        previousTestClass,
        currentRequiredParams,
        currentOptionalParams,
        allDevicesParameters,
        labelInput.value,
        expectedResult.value === "PASS"
    );

    // Hide the popup
    const popupWindowBootstrap = bootstrap.Modal.getInstance(popupWindow) || new bootstrap.Modal(popupWindow);
    popupWindowBootstrap.hide();
});

/**
 * Collects selected parameters from required and optional containers,
 * enables the info tab, and sets up the create test button to submit the test.
 * @async
 */
async function selectParameters() {
    setupParams = true;
    const requiredParams = readInputs(requiredContainer);
    const optionalParams = readInputs(optionalContainer)

    const allDeviceParameters = [...requiredParams.device_parameters, ...optionalParams.device_parameters];

    infoTab.disabled = false;
    infoTab.click();

    currentRequiredParams = requiredParams.values;
    currentOptionalParams = optionalParams.values;
    allDevicesParameters = allDeviceParameters;
    setupParams = false;
}

/**
 * Enables the "Create Test" button.
 */
function enableCreateTest() {
    createTestButton.disabled = false;
}

/**
 * Disables the "Create Test" button.
 */
function disableCreateTest() {
    createTestButton.disabled = true;
}

/**
 * Checks if the label input has a value and enables or disables the "Create Test" button accordingly.
 */
function checkTestValueInputs() {
    if (labelInput.value.length === 0) {
        disableCreateTest();
    } else {
        enableCreateTest();
    }
}

/**
 * Read non-empty inputs from a container and collect device-type inputs separately.
 *
 * @param {HTMLElement} container - the container element.
 * @returns {{values: Object, device_parameters: string[]}} Map of input names to values and list of device values.
 */
function readInputs(container) {
    const inputs = container.querySelectorAll("input");
    const values = {};
    const device_parameters = [];

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

