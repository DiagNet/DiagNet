/** IPv4 Datatype */
class Text extends Datatype {
    /**
     * Checks if the given value matches the datatype.
     * @param value The value to be checked.
     */
    check(value) {
        return true;
    }

    getDescription() {
        return "A combination of characters";
    }

    toString() {
        return "text";
    }

     displayName() {
        return "Text";
    }
}