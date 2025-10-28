const infoTab = document.getElementById('info-tab');

const description = document.getElementById('descriptionInput');
// Create Test
const createTestButton = document.getElementById('createTest')
createTestButton.addEventListener("click", async () => {
    if (setupParams || params === undefined) {
        return;
    }

    let expectedResult = document.querySelector('input[name="expectedResult"]:checked').value;
    try {

        await createTest(
            previousTestClass,
            params,
            labelInput.value,
            description.value,
            expectedResult === "PASS"
        );
    } catch (e) {
        throwException(e.message);
        return;
    }

    // Hide the popup
    const popupWindowBootstrap = bootstrap.Modal.getInstance(popupWindow) || new bootstrap.Modal(popupWindow);
    popupWindowBootstrap.hide();
});

// Label Input
const labelInput = document.getElementById('labelInput');

/** Enables the "Create Test" button. */
function enableCreateTest() {
    createTestButton.disabled = false;
}

/** Disables the "Create Test" button. */
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

labelInput.addEventListener("input", checkTestValueInputs);

// Select Parameters

let setupParams = false;
let params = undefined;

/**
 * Collects selected parameters from required and optional containers,
 * enables the info tab, and sets up the create test button to submit the test.
 * @async
 */
async function selectParameters(selectedParameters) {
    setupParams = true;

    params = readInputs(selectedParameters);

    infoTab.disabled = false;
    infoTab.click();
    updateTabContentAccessibility();

    setupParams = false;
}

/**
 * Read non-empty inputs from a container and collect device-type inputs separately.
 *
 * @param parameters all given Parameters.
 * @returns {Object<string, Object.<string, boolean>|[]>} Map of input names to values and list of device values.
 */
function readInputs(parameters) {
    const values = {};

    for (const params of parameters) {
        let field = params['parameter_info'];
        if (!field.isEmpty()) {
            let name = params['name'];
            let value = field.getValue();

            if (field instanceof ListField) {
                values[name] = value;
            } else {
                values[name] = {
                    'value': value,
                    "isDevice": field instanceof SingleLineDeviceField && allDevices.includes(value)
                };
            }
        }
    }
    return values;
}
