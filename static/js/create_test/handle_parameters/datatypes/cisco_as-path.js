class CiscoASPath extends Datatype {
  check(value) {
    if (typeof value !== "string") return false;
    if (value.trim() === "") return true;

    const asPathRegex = /^[0-9\s\.\_\*\+\?\|\(\)\[\]\^\$]+$/;

    if (!asPathRegex.test(value)) return false;

    const parts = value.split(/[\s\_\*\+\?\|\(\)\[\]\^\$]+/);
    for (let part of parts) {
      if (part && !isNaN(part)) {
        const asn = parseInt(part, 10);
        if (asn < 1 || asn > 4294967295) return false;
      }
    }
    return true;
  }

  getDescription() {
    return (
      "BGP AS-Path pattern. Supports numeric sequences (65001 65002) " +
      "and Cisco regex operators: _ (any delimiter), . (any character), " +
      "^ (start), $ (end), and multipliers (*, +, ?)."
    );
  }

  toString() {
    return "cisco-as-path";
  }
  displayName() {
    return "Cisco AS-Path / Regex";
  }
}
