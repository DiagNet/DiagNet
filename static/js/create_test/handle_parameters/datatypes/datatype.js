/**
 * Simulates an Enum. Displays Datatype-checking-results.
 * @type {{UNKNOWN: string, SUCCESS: string, FAIL: string}}
 */
const DATATYPE_RESULT = {
    UNKNOWN: "unknown",
    SUCCESS: "success",
    FAIL: "fail"
};

/** Abstract base class representing a datatype. */
class Datatype {
    /**
     * Creates a datatype.
     * @param {Object.<ParameterField, string>} conditions (Optional) The condition that has to be met in order for this datatype to be active.
     */
    constructor(conditions = undefined) {
        this.conditions = conditions;
    }

    /**
     * Returns the associated datatype for the given string.
     * @param datatype The datatype as string.
     * @param {ParameterField} parentParameter the parent parameter that uses this Datatype Object.
     * @param {Object.<string, string>} conditions (Optional) The condition that has to be met in order for this datatype to be active.
     * @param {Array<Object.<string, any>>} allParameters all other parameters.
     * @returns {Datatype} the datatype for the given parameters.
     */
    static toDatatype(datatype, parentParameter = undefined, conditions = undefined, allParameters = undefined) {
        if (conditions !== undefined) {
            const conditionsWithParameterFields = {};
            const needed_parameters = Object.keys(conditions);

            for (const parameter of allParameters) {
                if (needed_parameters.includes(parameter['name'])) {
                    const field = parameter['parameter_info'];
                    conditionsWithParameterFields[parameter['name']] = {
                        "value": conditions[parameter['name']],
                        "field": field
                    }
                    field.insertDependentParameter(parentParameter);
                }
            }

            conditions = conditionsWithParameterFields;
        }

        switch (datatype.trim().toLowerCase()) {
            case "device":
                return new Device(conditions);
            case "ipv4":
                return new IPv4(conditions);

            case "str":
            case "string":
            case "text":
                return new Text(conditions);

            case "list":
            case "choice":
                // do nothing
                break;

            default:
                throw new Error("Datatype not found. (Class Definition seems to be wrong?) " + datatype.trim().toLowerCase());
        }
    }

    // Checks

    /**
     * Returns all ParameterFields that are found in the conditions map.
     * @return {Array<ParameterField>} All ParameterFields that are found in this datatype's condition.
     */
    getConditionFields() {
        return this.conditions ? this.conditions.keys() : [];
    }

    /** Checks if this Datatype is valid based on the given conditions.*/
    checkValidity() {
        if (this.conditions === undefined) return true;
        for (const parameterName in this.conditions) {
            const value = this.conditions[parameterName]["value"];
            const field = this.conditions[parameterName]['field'];
            if (field.getValue() !== value) return false;
        }
        return true;
    }

    /**
     * Checks if the given value matches the datatype.
     * @param value The value to be checked.
     */
    check(value) {
        throw new Error("check() must be implemented in subclass");
    }

    // Info
    /** Returns a description about this Datatype. */
    getDescription() {
        throw new Error("getDescription() must be implemented in subclass");
    }

    toString() {
        throw new Error("toString() must be implemented in subclass");
    }

    displayName() {
        throw new Error("displayName() must be implemented in subclass");
    }
}