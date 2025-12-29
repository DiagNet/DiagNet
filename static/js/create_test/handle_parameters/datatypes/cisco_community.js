class CiscoCommunity extends Datatype {
    check(value) {
        if (typeof value !== 'string') return false;

        const aannRegex = /^([0-9]{1,5}):([0-9]{1,5})$/;
        if (aannRegex.test(value)) {
            const [aa, nn] = value.split(':').map(Number);
            return aa <= 65535 && nn <= 65535;
        }

        return false;
    }

    getDescription() {
        return "A BGP Community (AA:NN, decimal, or well-known alias)";
    }

    toString() {
        return "cisco-community";
    }

    displayName() {
        return "Cisco Community";
    }
}