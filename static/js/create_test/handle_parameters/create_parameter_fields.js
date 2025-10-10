
/**
 * Creates a parameter field based on the specified type.
 *
 * @param {"list"|"singleChoice"|"multiChoice"} type - The type of parameter field to create.
 * @returns {Object} The parameter field object corresponding to the given type.
 */
function createParameterFields(paramName, datatype, type) {
    let input = null

    if (datatype.includes("[")) {
        // Multiple Choice
        input = document.createElement("select");
        input.className = "form-select mb-2";

        const options = datatype
            .substring(1, datatype.length - 1)
            .split(",")
            .map(opt => opt.trim());
        options.unshift(""); // Add empty option (for deselecting)
        options.forEach(opt => {
            const option = document.createElement("option");
            option.value = opt.toLowerCase();
            option.textContent = opt;
            input.appendChild(option);
        });

    } else {
        input = document.createElement("input");
        input.type = "text";
        input.className = "form-control mb-2";

        input.placeholder = paramName
    }
    input.name = paramName;
    input.id = paramName;
    input.dataset.datatype = datatype;
    input.dataset.paramName = paramName;

    input.dataset.type = type;
    if (type === "required") {
        requiredStatus.set(input, false);
    }
    datatypeStatus.set(input, true);

    return input;
}