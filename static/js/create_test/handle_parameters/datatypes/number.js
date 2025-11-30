/** Number Datatype */
class PositiveNumber extends Datatype {
    /**
     * Checks if the given value matches the datatype.
     * Allows: 0, 1, 2, 10, 9999
     * @param value The value to be checked.
     */
    check(value) {
        const nonNegativeIntRegex = /^(0|[1-9]\d*)$/;
        return nonNegativeIntRegex.test(value);
    }

    getDescription() {
        return "A whole number (0 or positive integer, e.g., 0, 1, 42)";
    }

    toString() {
        return "number";
    }

    displayName() {
        return "Number";
    }
}
