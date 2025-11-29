/** Cisco Interface Datatype */
class CiscoInterface extends Datatype {
    /**
     * Checks if the given value is a valid Cisco interface.
     * Supports short and long names for common types (GigabitEthernet, FastEthernet, Serial, Loopback, etc.)
     * @param {string} value The interface string to check
     */
    check(value) {
        if (typeof value !== "string") return false;

        const val = value.toLowerCase().trim();

        const interfaceRegex = /^(?:gi|gig|gigabitethernet|fa|fastethernet|se|serial|lo|loopback)\d+\/\d+(?:\/\d+)?$/;
        return interfaceRegex.test(val);
    }

    /**
     * Returns a description of this datatype
     */
    getDescription() {
        return "A Cisco interface identifier";
    }

    /**
     * Normalizes interface to long form
     * e.g., gi0/0 -> GigabitEthernet0/0
     * fa0/1 -> FastEthernet0/1
     */
    normalize(value) {
        if (!this.check(value)) {
            throw new Error(`Invalid Cisco interface: ${value}`);
        }

        const val = value.toLowerCase();
        if (val.startsWith("gi") || val.startsWith("gig")) {
            return val.replace(/^gi(g)?/, "GigabitEthernet");
        } else if (val.startsWith("fa")) {
            return val.replace(/^fa/, "FastEthernet");
        } else if (val.startsWith("se")) {
            return val.replace(/^se/, "Serial");
        } else if (val.startsWith("lo")) {
            return val.replace(/^lo/, "Loopback");
        } else {
            return value; // already long form
        }
    }

    toString() {
        return "cisco-interface";
    }

    displayName() {
        return "Cisco Interface";
    }
}
