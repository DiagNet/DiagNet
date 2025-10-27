/** IPv4 Datatype */
class IPv4 extends Datatype {
    /**
     * Checks if the given value matches the datatype.
     * @param value The value to be checked.
     */
    check(value) {
        const ipv4Regex = /^(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}$/;
        return ipv4Regex.test(value);
        throw new Error("check() must be implemented in subclass");
    }

    getDescription() {
        return "Work in Progress";
    }

    toString() {
        return "ipv4";
        throw new Error("check() must be implemented in subclass");
    }

     displayName() {
        return "IPv4";
    }
}