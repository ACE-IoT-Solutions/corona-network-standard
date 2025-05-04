from typing import List
from .models import BaseEntity, VLAN, Router, Switch, Host, Iface, Link


def create_example_network() -> List[BaseEntity]:
    """Creates a list of Pydantic model instances representing an example network."""

    # VLANs
    vlan10 = VLAN(id="VLAN10_obj", vlan_id=10, name="Users")
    vlan20 = VLAN(id="VLAN20_obj", vlan_id=20, name="Servers")
    vlan99 = VLAN(id="VLAN99_obj", vlan_id=99, name="Management")

    # Devices
    router1 = Router(id="Router1", HasIFace=["R1_Eth0"])
    switch1 = Switch(id="Switch1", HasIFace=["Sw1_Fa0-1", "Sw1_Fa0-2", "Sw1_Gi0-1"])
    host1 = Host(id="Host1", HasIFace=["H1_Eth0"])

    # Interfaces
    iface_r1_eth0 = Iface(
        id="R1_Eth0",
        Address="10.0.0.1",
        BelongsToNode="Router1",
        ConnectedToLink="Link_R1_Sw1",
        port_mode="UNCONFIGURED",
    )
    iface_sw1_fa0_1 = Iface(
        id="Sw1_Fa0-1",
        BelongsToNode="Switch1",
        ConnectedToLink="Link_Sw1_H1",
        port_mode="ACCESS",
        access_vlan_id=10,
    )
    iface_sw1_fa0_2 = Iface(
        id="Sw1_Fa0-2", BelongsToNode="Switch1", port_mode="ACCESS", access_vlan_id=20
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
        Address="10.0.10.50",
        BelongsToNode="Host1",
        ConnectedToLink="Link_Sw1_H1",
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
        vlan10,
        vlan20,
        vlan99,
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
