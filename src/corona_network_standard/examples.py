"""
Provides a function to create an example network topology using the Pydantic models.

This serves as a concrete example of how to instantiate and link the different
network entities defined in models.py.
"""
from typing import List
from .models import (
    BaseEntity,
    VLAN,
    Router,
    Switch,
    Host,
    Iface,
    Link,
    Subnet,
    AddressAssignment,
)


def create_example_network() -> List[BaseEntity]:
    """
    Creates a list of Pydantic model instances representing an example network.

    This network includes:
    - Subnets (Users, Servers, Management, Transit)
    - VLANs (Users, Servers, Management)
    - Address Assignments for key interfaces
    - Devices (Router, Switch, Host)
    - Interfaces with appropriate configurations (ACCESS, TRUNK, UNCONFIGURED)
    - Links connecting the devices

    Returns:
        A list containing all instantiated BaseEntity objects for the example network.
    """

    # Subnets - Corrected argument name: subnetCidr -> cidr
    subnet10 = Subnet(id="Subnet_10.0.10.0_24", cidr="10.0.10.0/24", description="Subnet for user devices")
    subnet20 = Subnet(id="Subnet_10.0.20.0_24", cidr="10.0.20.0/24", description="Subnet for servers")
    subnet99 = Subnet(id="Subnet_192.168.99.0_24", cidr="192.168.99.0/24", description="Management subnet")
    subnet_transit = Subnet(id="Subnet_10.0.0.0_30", cidr="10.0.0.0/30", description="Transit link between R1 and Sw1")  # Link subnet

    # VLANs - now linked to subnets
    vlan10 = VLAN(id="VLAN10_obj", vlan_id=10, name="Users", hasSubnet=[subnet10.id], description="VLAN for general user access")
    vlan20 = VLAN(id="VLAN20_obj", vlan_id=20, name="Servers", hasSubnet=[subnet20.id], description="VLAN for server infrastructure")
    vlan99 = VLAN(id="VLAN99_obj", vlan_id=99, name="Management", hasSubnet=[subnet99.id], description="VLAN for network device management")

    # Address Assignments - Corrected argument names: ipValue -> ip_value, onSubnet -> on_subnet_id
    assign_r1_eth0 = AddressAssignment(
        id="Assign_R1_Eth0_10.0.0.1",
        ip_value="10.0.0.1",
        on_subnet_id=subnet_transit.id,  # Link to Subnet ID
        description="IP address for Router1's interface on the transit link"
    )
    assign_h1_eth0 = AddressAssignment(
        id="Assign_H1_Eth0_10.0.10.50",
        ip_value="10.0.10.50",
        on_subnet_id=subnet10.id,  # Link to Subnet ID
    )
    # Example assignment for a server (not fully defined host)
    assign_server_eth0 = AddressAssignment(
        id="Assign_Server_Eth0_10.0.20.100",
        ip_value="10.0.20.100",
        on_subnet_id=subnet20.id,  # Link to Subnet ID
    )

    # Devices
    router1 = Router(
        id="Router1",
        HasIFace=["R1_Eth0"],
        routesSubnet=[subnet10.id, subnet20.id, subnet99.id, subnet_transit.id],
        description="Main campus router"
    )
    switch1 = Switch(id="Switch1", HasIFace=["Sw1_Fa0-1", "Sw1_Fa0-2", "Sw1_Gi0-1"], description="Access layer switch 1")
    host1 = Host(id="Host1", HasIFace=["H1_Eth0"], description="Example user workstation")

    # Interfaces - Address field removed, hasAddressAssignment added (linking to Assignment object)
    iface_r1_eth0 = Iface(
        id="R1_Eth0",
        BelongsToNode="Router1",
        ConnectedToLink="Link_R1_Sw1",
        port_mode="UNCONFIGURED",
        hasAddressAssignment=[assign_r1_eth0],  # Pass the Assignment object
        description="Router1 Ethernet0 - Connects to Switch1 Gi0/1"
    )
    iface_sw1_fa0_1 = Iface(
        id="Sw1_Fa0-1",
        BelongsToNode="Switch1",
        ConnectedToLink="Link_Sw1_H1",
        port_mode="ACCESS",
        access_vlan_id=10,
    )
    iface_sw1_fa0_2 = Iface(
        id="Sw1_Fa0-2",
        BelongsToNode="Switch1",
        port_mode="ACCESS",
        access_vlan_id=20,
    )
    iface_sw1_gi0_1 = Iface(
        id="Sw1_Gi0-1",
        BelongsToNode="Switch1",
        ConnectedToLink="Link_R1_Sw1",
        port_mode="TRUNK",
        allowed_vlan_ids=[10, 20, 99],
    )
    iface_h1_eth0 = Iface(
        id="H1_Eth0",
        BelongsToNode="Host1",
        ConnectedToLink="Link_Sw1_H1",
        hasAddressAssignment=[assign_h1_eth0],  # Pass the Assignment object
        port_mode="UNCONFIGURED",
    )

    # Links
    link_r1_sw1 = Link(
        id="Link_R1_Sw1", Technology="Ethernet", interface_ids=["R1_Eth0", "Sw1_Gi0-1"]
    )
    link_sw1_h1 = Link(
        id="Link_Sw1_H1", Technology="Ethernet", interface_ids=["Sw1_Fa0-1", "H1_Eth0"]
    )

    # Update neighbor relationships (Physical Neighbors based on Links)
    router1.has_neighbor_ids = ["Switch1"]
    switch1.has_neighbor_ids = ["Router1", "Host1"]
    host1.has_neighbor_ids = ["Switch1"]

    # List of all entities to add to the graph (valid ones)
    entities: List[BaseEntity] = [
        # Logical first
        subnet10,
        subnet20,
        subnet99,
        subnet_transit,
        vlan10,
        vlan20,
        vlan99,
        # Assignments (can go here or with interfaces)
        assign_r1_eth0,
        assign_h1_eth0,
        assign_server_eth0,
        # Hardware
        router1,
        switch1,
        host1,
        iface_r1_eth0,
        iface_sw1_fa0_1,
        iface_sw1_fa0_2,
        iface_sw1_gi0_1,
        iface_h1_eth0,
        link_r1_sw1,
        link_sw1_h1,
    ]

    return entities
