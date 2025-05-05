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
    # Pass the actual Subnet objects, not just their IDs
    vlan10 = VLAN(id="VLAN10_obj", vlan_id=10, name="Users", hasSubnet=[subnet10], description="VLAN for general user access")
    vlan20 = VLAN(id="VLAN20_obj", vlan_id=20, name="Servers", hasSubnet=[subnet20], description="VLAN for server infrastructure")
    vlan99 = VLAN(id="VLAN99_obj", vlan_id=99, name="Management", hasSubnet=[subnet99], description="VLAN for network device management")

    # Address Assignments - Corrected argument names: ipValue -> ip_value, onSubnet -> on_subnet_id
    # Pass the actual Subnet object to the on_subnet field
    assign_r1_eth0 = AddressAssignment(
        id="Assign_R1_Eth0_10.0.0.1",
        ip_value="10.0.0.1",
        on_subnet=subnet_transit,  # Pass the Subnet object
        description="IP address for Router1's interface on the transit link"
    )
    assign_h1_eth0 = AddressAssignment(
        id="Assign_H1_Eth0_10.0.10.50",
        ip_value="10.0.10.50",
        on_subnet=subnet10,  # Pass the Subnet object
    )
    # Example assignment for a server (not fully defined host)
    assign_server_eth0 = AddressAssignment(
        id="Assign_Server_Eth0_10.0.20.100",
        ip_value="10.0.20.100",
        on_subnet=subnet20,  # Pass the Subnet object
    )

    # Devices
    # Pass the actual Iface, Subnet, and Node objects instead of IDs
    router1 = Router(
        id="Router1",
        HasIFace=[],  # Will be updated later
        routesSubnet=[subnet10, subnet20, subnet99, subnet_transit],  # Pass Subnet objects
        description="Main campus router"
    )
    switch1 = Switch(
        id="Switch1",
        HasIFace=[],  # Will be updated later
        description="Access layer switch 1"
    )
    host1 = Host(
        id="Host1",
        HasIFace=[],  # Will be updated later
        description="Example user workstation"
    )

    # Interfaces - Address field removed, hasAddressAssignment added (linking to Assignment object)
    # Link interfaces back to their parent Node objects and VLAN objects
    iface_r1_eth0 = Iface(
        id="R1_Eth0",
        BelongsToNode=router1,  # Pass Node object
        ConnectedToLink=None,  # Will be updated later
        port_mode="UNCONFIGURED",
        hasAddressAssignment=[assign_r1_eth0],
        description="Router1 Ethernet0 - Connects to Switch1 Gi0/1"
    )
    iface_sw1_fa0_1 = Iface(
        id="Sw1_Fa0-1",
        BelongsToNode=switch1,  # Pass Node object
        ConnectedToLink=None,  # Will be updated later
        port_mode="ACCESS",
        access_vlan=vlan10,  # Pass VLAN object directly
    )
    iface_sw1_fa0_2 = Iface(
        id="Sw1_Fa0-2",
        BelongsToNode=switch1,  # Pass Node object
        port_mode="ACCESS",
        access_vlan=vlan20,  # Pass VLAN object directly
    )
    iface_sw1_gi0_1 = Iface(
        id="Sw1_Gi0-1",
        BelongsToNode=switch1,  # Pass Node object
        ConnectedToLink=None,  # Will be updated later
        port_mode="TRUNK",
        allowed_vlans=[vlan10, vlan20, vlan99],  # Pass list of VLAN objects
    )
    iface_h1_eth0 = Iface(
        id="H1_Eth0",
        BelongsToNode=host1,  # Pass Node object
        ConnectedToLink=None,  # Will be updated later
        hasAddressAssignment=[assign_h1_eth0],
        port_mode="UNCONFIGURED",
    )

    # Update devices with their interfaces
    router1.has_ifaces = [iface_r1_eth0]
    switch1.has_ifaces = [iface_sw1_fa0_1, iface_sw1_fa0_2, iface_sw1_gi0_1]
    host1.has_ifaces = [iface_h1_eth0]

    # Links
    # Pass the actual Iface objects instead of IDs
    link_r1_sw1 = Link(
        id="Link_R1_Sw1",
        Technology="Ethernet",
        interfaces=[iface_r1_eth0, iface_sw1_gi0_1]  # Pass Iface objects
    )
    link_sw1_h1 = Link(
        id="Link_Sw1_H1",
        Technology="Ethernet",
        interfaces=[iface_sw1_fa0_1, iface_h1_eth0]  # Pass Iface objects
    )

    # Update neighbor relationships (Physical Neighbors based on Links)
    # Pass the actual Node objects instead of IDs
    router1.has_neighbors = [switch1]
    switch1.has_neighbors = [router1, host1]
    host1.has_neighbors = [switch1]

    # Update interfaces with Link objects
    iface_r1_eth0.connected_to_link = link_r1_sw1
    iface_sw1_gi0_1.connected_to_link = link_r1_sw1
    iface_sw1_fa0_1.connected_to_link = link_sw1_h1
    iface_h1_eth0.connected_to_link = link_sw1_h1

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
