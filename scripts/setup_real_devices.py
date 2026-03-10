"""
Erstellt alle Devices und Switching-Testcases für die echten Geräte (DSW, ASW-1, ASW-2).

Ausführen mit:
    python manage.py shell < scripts/setup_real_devices.py

oder via Docker Compose:
    docker compose exec web python manage.py shell < scripts/setup_real_devices.py
"""

from devices.models import Device
from networktests.models import TestCase, TestDevice, TestGroup, TestParameter

GROUP_NAME = "Echte Geräte – Switching Audit"

# Schutz: Script nicht doppelt ausführen
if TestGroup.objects.filter(name=GROUP_NAME).exists():
    print(f"[!] Gruppe '{GROUP_NAME}' existiert bereits – abgebrochen.")
    print("    Lösche die Gruppe zuerst wenn du neu aufsetzen willst.")
else:
    # ─────────────────────────────────────────────────────────────────────────
    # 1. Devices
    # ─────────────────────────────────────────────────────────────────────────

    def get_or_create_device(name, ip):
        dev, created = Device.objects.get_or_create(
            name=name,
            defaults={
                "protocol": "ssh",
                "ip_address": ip,
                "port": 22,
                "device_type": "switch_iosxe",
                "username": "dnadmin",
                "password": "Juniorcisco123!",
                "enable_password": "Juniorcisco123!",
            },
        )
        print(f"  {'Erstellt' if created else 'Vorhanden'}: {name} ({ip})")
        return dev

    print("\n[Devices]")
    dsw = get_or_create_device("DSW", "10.0.99.1")
    asw1 = get_or_create_device("ASW-1", "10.0.99.2")
    asw2 = get_or_create_device("ASW-2", "10.0.99.3")

    # ─────────────────────────────────────────────────────────────────────────
    # 2. Helper
    # ─────────────────────────────────────────────────────────────────────────

    all_tcs = []

    def tc(label, module, device_obj, params: dict, expected=True):
        t = TestCase.objects.create(
            test_module=module,
            expected_result=expected,
            label=label,
        )
        TestDevice.objects.create(name="device", test_case=t, device=device_obj)
        for k, v in params.items():
            TestParameter.objects.create(name=k, test_case=t, value=str(v))
        all_tcs.append(t)
        print(f"  + {label}")
        return t

    # ─────────────────────────────────────────────────────────────────────────
    # 3. DSW
    # ─────────────────────────────────────────────────────────────────────────

    print("\n[DSW]")

    tc(
        "DSW: AAA RADIUS",
        "AAA_Radius_Configuration",
        dsw,
        {
            "radius_ip": "10.0.99.10",
            "verify_vty_mapping": "Yes",
            "expected_login_method": "SSH_AUTH",
        },
    )

    tc(
        "DSW: Device Identity",
        "Device_Identity_Crypto_Audit",
        dsw,
        {
            "expected_domain": "diagnet.at",
            "enforce_no_lookup": "Yes",
            "enforce_ssh_v2": "Yes",
            "min_rsa_modulus": "2048",
        },
    )

    tc(
        "DSW: Local Account",
        "Local_Account_Security",
        dsw,
        {
            "expected_username": "dnadmin",
            "require_privilege_15": "Yes",
            "fail_on_weak_hashes": "Yes",
            "required_algorithm": "scrypt",
        },
    )

    tc(
        "DSW: Management Plane",
        "Management_Plane_Security",
        dsw,
        {
            "require_ssh_v2": "Yes",
            "require_http_disabled": "Yes",
            "vty_transport_strict": "Yes",
            "min_rsa_modulus": "2048",
        },
    )

    tc(
        "DSW: SVI VLAN 99",
        "SVI_Management_Hardening_Audit",
        dsw,
        {
            "management_vlan": "99",
        },
    )

    for vlan in [1, 10, 99]:
        tc(
            f"DSW: STP Root VLAN {vlan}",
            "Rapid_PVST_Root_Audit",
            dsw,
            {
                "vlan_id": str(vlan),
                "should_be_root": "True",
            },
        )

    for gi, desc in [
        ("GigabitEthernet1/0/1", "FW1"),
        ("GigabitEthernet1/0/2", "FW2"),
        ("GigabitEthernet1/0/3", "ASW-1"),
        ("GigabitEthernet1/0/4", "ASW-2"),
    ]:
        tc(
            f"DSW: Trunk {gi} ({desc})",
            "Switchport_Trunk_Audit",
            dsw,
            {
                "interface": gi,
                "expected_native_vlan": "999",
                "required_vlans": "10,99,999",
            },
        )

    tc(
        "DSW: DHCP Snooping",
        "DHCP_Snooping_Security_Audit",
        dsw,
        {
            "protected_vlans": "10",
            "trusted_interfaces": (
                "GigabitEthernet1/0/1,GigabitEthernet1/0/2,"
                "GigabitEthernet1/0/3,GigabitEthernet1/0/4"
            ),
        },
    )

    tc(
        "DSW: LLDP Neighbor ASW-1",
        "LLDP_CDP_Infrastructure_Audit",
        dsw,
        {
            "required_neighbor": "ASW-1",
            "local_interface": "GigabitEthernet1/0/3",
        },
    )

    tc(
        "DSW: LLDP Neighbor ASW-2",
        "LLDP_CDP_Infrastructure_Audit",
        dsw,
        {
            "required_neighbor": "ASW-2",
            "local_interface": "GigabitEthernet1/0/4",
        },
    )

    tc(
        "DSW: MAC Table Stability",
        "MAC_Address_Table_Stability_Audit",
        dsw,
        {
            "expected_aging_time": "300",
        },
    )

    # ─────────────────────────────────────────────────────────────────────────
    # 4. ASW-1 & ASW-2 (identische Struktur, unterschiedliche Werte)
    # ─────────────────────────────────────────────────────────────────────────

    for name, dev, domain in [
        ("ASW-1", asw1, "diagnet.local"),
        ("ASW-2", asw2, "diagnet.at"),
    ]:
        print(f"\n[{name}]")

        tc(
            f"{name}: AAA RADIUS",
            "AAA_Radius_Configuration",
            dev,
            {
                "radius_ip": "10.0.99.10",
                "verify_vty_mapping": "Yes",
                "expected_login_method": "SSH_AUTH",
            },
        )

        tc(
            f"{name}: Device Identity",
            "Device_Identity_Crypto_Audit",
            dev,
            {
                "expected_domain": domain,
                "enforce_no_lookup": "Yes",
                "enforce_ssh_v2": "Yes",
                "min_rsa_modulus": "2048",
            },
        )

        tc(
            f"{name}: Local Account",
            "Local_Account_Security",
            dev,
            {
                "expected_username": "dnadmin",
                "require_privilege_15": "Yes",
                "fail_on_weak_hashes": "Yes",
                "required_algorithm": "scrypt",
            },
        )

        tc(
            f"{name}: Management Plane",
            "Management_Plane_Security",
            dev,
            {
                "require_ssh_v2": "Yes",
                "require_http_disabled": "Yes",
                "vty_transport_strict": "Yes",
                "min_rsa_modulus": "2048",
            },
        )

        tc(
            f"{name}: SVI VLAN 99",
            "SVI_Management_Hardening_Audit",
            dev,
            {
                "management_vlan": "99",
            },
        )

        for vlan in [1, 10, 99]:
            tc(
                f"{name}: STP nicht Root VLAN {vlan}",
                "Rapid_PVST_Root_Audit",
                dev,
                {
                    "vlan_id": str(vlan),
                    "should_be_root": "False",
                },
            )

        tc(
            f"{name}: Trunk Gi1/0/1",
            "Switchport_Trunk_Audit",
            dev,
            {
                "interface": "GigabitEthernet1/0/1",
                "expected_native_vlan": "999",
                "required_vlans": "10,99,999",
            },
        )

        tc(
            f"{name}: DHCP Snooping",
            "DHCP_Snooping_Security_Audit",
            dev,
            {
                "protected_vlans": "10,99",
                "trusted_interfaces": "GigabitEthernet1/0/1",
            },
        )

        tc(
            f"{name}: Access Port Gi1/0/2",
            "Access_Port_Compliance",
            dev,
            {
                "interface": "GigabitEthernet1/0/2",
                "expected_vlan": "10",
                "require_portfast": "True",
                "require_bpduguard": "True",
            },
        )

        tc(
            f"{name}: Port Security Gi1/0/2",
            "Port_Security_Audit",
            dev,
            {
                "interface": "GigabitEthernet1/0/2",
                "max_mac_addresses": "1",
                "violation_mode": "restrict",
            },
        )

        tc(
            f"{name}: Storm Control Gi1/0/2",
            "Storm_Control_Audit",
            dev,
            {
                "interface": "GigabitEthernet1/0/2",
                "broadcast_threshold": "1.00",
                "action_shutdown": "False",
            },
        )

        tc(
            f"{name}: LLDP Neighbor DSW",
            "LLDP_CDP_Infrastructure_Audit",
            dev,
            {
                "required_neighbor": "DSW",
                "local_interface": "GigabitEthernet1/0/1",
            },
        )

        tc(
            f"{name}: MAC Table Stability",
            "MAC_Address_Table_Stability_Audit",
            dev,
            {
                "expected_aging_time": "300",
            },
        )

    # ─────────────────────────────────────────────────────────────────────────
    # 5. TestGroup
    # ─────────────────────────────────────────────────────────────────────────

    print("\n[TestGroup]")
    group = TestGroup.objects.create(name=GROUP_NAME)
    group.testcases.set(all_tcs)
    group.save()

    print(f"\n✓ Fertig: '{GROUP_NAME}' – {len(all_tcs)} Testcases angelegt.")
