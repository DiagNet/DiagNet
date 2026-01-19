/** IPv4 Datatype */
class IPv4 extends Datatype {
    /**
     * Checks if the given value matches the datatype.
     * @param value The value to be checked.
     */
    check(value) {
        const ipv4Regex = /^(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}$/;
        return ipv4Regex.test(value);
    }

    getDescription() {
        return gettext("An IPv4 address");
    }

    toString() {
        return "ipv4";
    }

     displayName() {
        return "IPv4";
    }
}

/** IPv4-Prefix Datatype (e.g., 192.168.0.0/24) */
class IPv4CIDR extends Datatype {
    /**
     * Checks if the given value is a valid IPv4 prefix.
     * Matches standard IPv4 addresses with CIDR notation (0-32).
     * @param value The value to be checked.
     */
    check(value) {
        const ipv4PrefixRegex = /^(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}\/([0-9]|[1-2][0-9]|3[0-2])$/;
        return ipv4PrefixRegex.test(value);
    }

    getDescription() {
        return gettext("An IPv4 network prefix in CIDR notation");
    }

    toString() {
        return "ipv4-cidr";
    }

    displayName() {
        return "IPv4 CIDR";
    }
}