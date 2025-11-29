/** IPv6 Datatype */
class IPv6 extends Datatype {
    /**
     * Checks if the given value matches the datatype.
     * Covers all valid IPv6 formats (compressed, full, with leading zeros, etc.)
     * @param value The value to be checked.
     */
    check(value) {
        // Matches full, compressed (::), and mixed IPv6 formats
        const ipv6Regex = /^(?:[A-Fa-f0-9]{1,4}:){7}[A-Fa-f0-9]{1,4}$|^(?:[A-Fa-f0-9]{1,4}:){1,7}:$|^(?:[A-Fa-f0-9]{1,4}:){1,6}:[A-Fa-f0-9]{1,4}$|^(?:[A-Fa-f0-9]{1,4}:){1,5}(?::[A-Fa-f0-9]{1,4}){1,2}$|^(?:[A-Fa-f0-9]{1,4}:){1,4}(?::[A-Fa-f0-9]{1,4}){1,3}$|^(?:[A-Fa-f0-9]{1,4}:){1,3}(?::[A-Fa-f0-9]{1,4}){1,4}$|^(?:[A-Fa-f0-9]{1,4}:){1,2}(?::[A-Fa-f0-9]{1,4}){1,5}$|^[A-Fa-f0-9]{1,4}:(?:(?::[A-Fa-f0-9]{1,4}){1,6})$|^:(?:(?::[A-Fa-f0-9]{1,4}){1,7}|:)$|^(?:[A-Fa-f0-9]{1,4}:){6}(?:[0-9]{1,3}\.){3}[0-9]{1,3}$/;
        return ipv6Regex.test(value);
    }

    getDescription() {
        return "An IPv6 address";
    }

    toString() {
        return "ipv6";
    }

    displayName() {
        return "IPv6";
    }
}

/** IPv6-Prefix Datatype (e.g., 2001:db8::/32) */
class IPv6CIDR extends Datatype {
    /**
     * Checks if the given value is a valid IPv6 prefix.
     * Matches full, compressed, or mixed IPv6 addresses with CIDR (0-128).
     * @param value The value to be checked.
     */
    check(value) {
        const [address, prefixLength] = value.split('/');
        if (!prefixLength || isNaN(prefixLength)) return false;
        const length = parseInt(prefixLength, 10);
        if (length < 0 || length > 128) return false;

        // Reuse IPv6 regex from IPv6 class
        const ipv6Regex = /^(?:[A-Fa-f0-9]{1,4}:){7}[A-Fa-f0-9]{1,4}$|^(?:[A-Fa-f0-9]{1,4}:){1,7}:$|^(?:[A-Fa-f0-9]{1,4}:){1,6}:[A-Fa-f0-9]{1,4}$|^(?:[A-Fa-f0-9]{1,4}:){1,5}(?::[A-Fa-f0-9]{1,4}){1,2}$|^(?:[A-Fa-f0-9]{1,4}:){1,4}(?::[A-Fa-f0-9]{1,4}){1,3}$|^(?:[A-Fa-f0-9]{1,4}:){1,3}(?::[A-Fa-f0-9]{1,4}){1,4}$|^(?:[A-Fa-f0-9]{1,4}:){1,2}(?::[A-Fa-f0-9]{1,4}){1,5}$|^[A-Fa-f0-9]{1,4}:(?:(?::[A-Fa-f0-9]{1,4}){1,6})$|^:(?:(?::[A-Fa-f0-9]{1,4}){1,7}|:)$|^(?:[A-Fa-f0-9]{1,4}:){6}(?:[0-9]{1,3}\.){3}[0-9]{1,3}$/;
        return ipv6Regex.test(address);
    }

    getDescription() {
        return "An IPv6 network prefix in CIDR notation";
    }

    toString() {
        return "ipv6-cidr";
    }

    displayName() {
        return "IPv6 CIDR";
    }
}