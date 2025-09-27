let selectedTestClass = "";
const paramTab = document.getElementById('parameters-tab')
const templateTab = document.getElementById('template-tab')
const requiredContainer = document.getElementById("requiredParamsContainer");
const optionalContainer = document.getElementById("optionalParamsContainer");

/** "Selects" the given Class for further handling. */
function selectTestClass(testClass, popup) {
    selectedTestClass = testClass;
    paramTab.disabled = false;
    paramTab.click();
    popup.removeEventListener("keydown", onPopUpClickHandler);
    templateTab.addEventListener("click", (e) => {
        selectedTestClass = "";
        paramTab.disabled = true;
        popup.addEventListener("keydown", onPopUpClickHandler);
    })
    show_parameters(testClass);
}

function parseOptions(datatype) {
    try {
        return datatype
            .substring(1, datatype.length - 1)
            .split(",")
            .map(opt => opt.trim());
    } catch {
        return [];
    }
}

/** Helper: create a single input field */
function createInputField(paramName, datatype, isOptional = false) {
    if (datatype.includes("[")) {
        // Multiple Choice
        const input = document.createElement("select");
        input.name = paramName;
        input.id = paramName;
        input.className = "form-select mb-2";
        input.dataset.datatype = datatype;
        input.dataset.param_name = paramName

        const options = parseOptions(datatype);
        options.unshift("");
        options.forEach(opt => {
            const option = document.createElement("option");
            option.value = opt.toLowerCase();
            option.textContent = opt;
            input.appendChild(option);
        });
        return input;
    } else {
        const input = document.createElement("input");
        input.type = "text";
        input.name = paramName;
        input.id = paramName
        input.placeholder = isOptional ? `${paramName} (optional)` : paramName;
        input.className = "form-control mb-2";
        input.dataset.datatype = datatype;
        input.dataset.param_name = paramName
        return input;
    }
}


/** "Enables" the given field. */
function enable_field(field) {
    field.disabled = false;
    field.readOnly = false;
}

/** "Disables" the given field. */
function disable_field(field) {
    field.disabled = true;
    field.readOnly = true;
}

/** Responsible to block all mutually exclusive group members except the selected one. */
async function create_mutually_exclusive_datatype_bindings(param_fields, mutually_exclusive_groups, param_datatypes) {
    /** Activates the first field and deactivates the other ones. */
    function toggle_pair(activated, all_fields) {
        // enable_field(activated); - Redundant
        for (const value of all_fields.values()) {
            if (value === activated) continue;
            disable_field(value);
        }
    }

    /** Enables all fields given. */
    function enable_all_fields(all_fields) {
        for (const value of all_fields.values()) {
            enable_field(value);
        }
    }

    let calculate_mut_neighbors = new Map()
    mutually_exclusive_groups.forEach(pair => {
        const all_fields = pair.map(v => param_fields.get(v));

        for (const field of all_fields) {
            if (!calculate_mut_neighbors.has(field)) {
                calculate_mut_neighbors.set(field, new Set(all_fields));
            } else {
                const s = calculate_mut_neighbors.get(field);
                all_fields.forEach(f => s.add(f));
            }
        }
    });

    for (const [field, all_fields_set] of calculate_mut_neighbors.entries()) {
        if (field.tagName.toLowerCase() === "select") {
            field.addEventListener("change", () => {
                const all_fields = [...all_fields_set];
                if (field.value.length === 0) {
                    enable_all_fields(all_fields);
                    handle_check_datatype(field, null);
                } else {
                    toggle_pair(field, all_fields);
                    handle_check_datatype(field, param_datatypes.get(field.id));
                }
            });
        } else {
            field.addEventListener("input", () => {
                const all_fields = [...all_fields_set];
                if (field.value.length === 0) {
                    enable_all_fields(all_fields);
                    handle_check_datatype(field, null);
                } else if (field.value.length === 1) { // Could be improved, length from 2 to 1 is a redundant operation here, but this is simple
                    toggle_pair(field, all_fields);
                    handle_check_datatype(field, param_datatypes.get(field.id));
                } else {
                    handle_check_datatype(field, param_datatypes.get(field.id));
                }
            });
        }
    }

    for (const [param, field] of param_fields.entries()) {
        if (calculate_mut_neighbors.has(field)) continue; // Mutually Exclusive candidate
        field.addEventListener("input", () => {
            if (field.value.length === 0) {
                handle_check_datatype(field, null);
            } else {
                handle_check_datatype(field, param_datatypes.get(param));
            }
        });
    }

}

/**
 * Dynamically creates input fields for all required and optional parameters of a test class.
 *
 * @async
 * @param {string} test_class The name of the test class to generate inputs for.
 */
async function show_parameters(test_class) {
    const test_parameters = await fetch_test_parameters(test_class);

    // Clear previous inputs
    requiredContainer.innerHTML = "";
    optionalContainer.innerHTML = "";

    const required_parameters = new Map(test_parameters.required_params.map(item => {
        const [part1, part2] = item.split(":");
        return [part1, part2];
    }));

    const optional_parameters = new Map(test_parameters.optional_params.map(item => {
        const [part1, part2] = item.split(":");
        return [part1, part2];
    }));

    // stores what input field corresponds to what param for mutually exclusive bindings.
    let mutually_exclusive_params_fields = new Map();

    // Create inputs for required parameters
    for (const [param, datatype] of required_parameters) {
        const new_input_field = createInputField(param, datatype);
        mutually_exclusive_params_fields.set(param, new_input_field);
        requiredContainer.appendChild(new_input_field);
    }

    // Create inputs for required parameters
    for (const [param, datatype] of optional_parameters) {
        const new_input_field = createInputField(param, datatype);
        mutually_exclusive_params_fields.set(param, new_input_field);
        optionalContainer.appendChild(new_input_field);
    }

    create_mutually_exclusive_datatype_bindings(mutually_exclusive_params_fields, test_parameters.mul, new Map([...required_parameters, ...optional_parameters]));
}


/**
 * Automatically sets focus to the search input when the popup is clicked.
 * Used in EventListeners between the Test-Class and Parameter tab.
 *
 * @param {Event} e event Object
 */
function onPopUpClickHandler(e) {
    searchInput.focus()
}