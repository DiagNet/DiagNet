class CiscoCommunity extends Datatype {
    check(value) {
        if (typeof value !== 'string') return false;

        const aannRegex = /^([0-9]{1,5}):([0-9]{1,5})$/;
        const extendedRegex = /^(rt|soo):.+:.+$/i;
        const largeRegex = /^([0-9]+):([0-9]+):([0-9]+)$/;

        if (aannRegex.test(value)) {
            const [aa, nn] = value.split(':').map(Number);
            return aa <= 65535 && nn <= 65535;
        }

        return extendedRegex.test(value) || largeRegex.test(value);
    }

    getDescription() {
        return "BGP Community (Standard AA:NN, Extended, Large)";
    }

    toString() {
        return "cisco-community";
    }

    displayName() {
        return "Cisco Community";
    }
}