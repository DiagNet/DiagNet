/** Cisco Interface Datatype */
class CiscoInterface extends Datatype {
  constructor(conditions = undefined) {
    super(conditions);
    this._targets = {
      fastethernet: "FastEthernet",
      gigabitethernet: "GigabitEthernet",
      loopback: "Loopback",
      tunnel: "Tunnel",
      vlan: "Vlan",
      "port-channel": "Port-Channel",
      serial: "Serial",
    };

    this._shortMap = {
      fa: "fastethernet",
      gig: "gigabitethernet",
      lo: "loopback",
      tu: "tunnel",
      vl: "vlan",
      po: "port-channel",
      se: "serial",
    };

    this.pattern = /^([a-zA-Z\-]+)\s*(\d.*)$/;
  }

  _getMatches(prefixInput) {
    const input = prefixInput.toLowerCase();
    const matches = new Set();

    for (const [key, formalName] of Object.entries(this._targets)) {
      if (key.startsWith(input)) {
        matches.add(formalName);
      }
    }

    for (const [short, targetKey] of Object.entries(this._shortMap)) {
      if (short.startsWith(input)) {
        matches.add(this._targets[targetKey]);
      }
    }

    return Array.from(matches);
  }

  canBeExpanded(interfaceStr) {
    if (!interfaceStr) return false;
    const match = interfaceStr.trim().match(this.pattern);
    if (!match) return false;

    return this._getMatches(match[1]).length === 1;
  }

  canonicalize(interfaceStr) {
    if (!interfaceStr) return "";
    const trimmed = interfaceStr.trim();
    const match = trimmed.match(this.pattern);

    if (!match) return trimmed;

    const prefix = match[1];
    const identifier = match[2];
    const matches = this._getMatches(prefix);

    return matches.length === 1 ? `${matches[0]}${identifier}` : trimmed;
  }

  check(value) {
    return this.canBeExpanded(value);
  }

  getDescription() {
    return "A Cisco interface identifier";
  }

  toString() {
    return "cisco-interface";
  }

  displayName() {
    return "Cisco Interface";
  }

  before_submit(value) {
    if (this.canBeExpanded(value)) {
      return this.canonicalize(value);
    }
    return value;
  }
}
