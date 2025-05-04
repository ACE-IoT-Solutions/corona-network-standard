from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import List, Optional, Literal as PydanticLiteral
from rdflib import Graph, Literal, Namespace
from rdflib.namespace import RDF, RDFS
import click # Keep for debug prints in validator for now

# Define Namespaces (Keep here or move to a constants.py if preferred)
NETWORK = Namespace("http://www.example.org/network-ontology#")
EX = Namespace("http://www.example.org/network-instance#")


class BaseEntity(BaseModel):
    id: str  # Unique identifier for the instance

    def to_rdf(self, g: Graph):
        entity_uri = EX[self.id]
        g.add((entity_uri, RDF.type, NETWORK[self.__class__.__name__]))
        g.add((entity_uri, RDFS.label, Literal(self.id)))
        return entity_uri


class HWNetEntity(BaseEntity):
    hw_status: PydanticLiteral["ON", "OFF", "ABN"] = Field(
        default="ON", alias="HWStatus"
    )

    def to_rdf(self, g: Graph):
        entity_uri = super().to_rdf(g)
        g.add((entity_uri, NETWORK.HWStatus, Literal(self.hw_status)))
        return entity_uri


class LogicalEntity(BaseEntity):
    pass


class VLAN(LogicalEntity):
    model_config = ConfigDict(
        populate_by_name=True
    )
    vlan_id: int = Field(alias="vlanId")
    name: Optional[str] = Field(default=None, alias="vlanName")

    def to_rdf(self, g: Graph):
        vlan_instance_uri = EX[f"VLAN{self.vlan_id}"]
        g.add((vlan_instance_uri, RDF.type, NETWORK.VLAN))
        label = f"VLAN {self.vlan_id}" + (f" ({self.name})" if self.name else "")
        g.add((vlan_instance_uri, RDFS.label, Literal(label)))
        g.add((vlan_instance_uri, NETWORK.vlanId, Literal(self.vlan_id)))
        if self.name:
            g.add((vlan_instance_uri, NETWORK.vlanName, Literal(self.name)))
        return vlan_instance_uri


class Iface(HWNetEntity):
    model_config = ConfigDict(
        populate_by_name=True
    )
    address: Optional[str] = Field(default=None, alias="Address")
    connected_to_link_id: Optional[str] = Field(default=None, alias="ConnectedToLink")
    belongs_to_node_id: Optional[str] = Field(default=None, alias="BelongsToNode")
    port_mode: PydanticLiteral["ACCESS", "TRUNK", "UNCONFIGURED"] = Field(
        default="UNCONFIGURED", alias="portMode"
    )
    access_vlan_id: Optional[int] = Field(
        default=None, alias="accessVlan"
    )
    allowed_vlan_ids: List[int] = Field(
        default_factory=list, alias="allowedVlan"
    )

    @model_validator(mode="after")
    def check_vlan_mode_consistency(self) -> "Iface":
        mode = self.port_mode
        access_vlan = self.access_vlan_id
        allowed_vlans = self.allowed_vlan_ids

        if mode == "ACCESS":
            if not access_vlan:
                pass
            if allowed_vlans:
                raise ValueError(
                    f"allowed_vlan_ids cannot be set when port_mode is ACCESS (Interface ID: {self.id})"
                )
        elif mode == "TRUNK":
            if access_vlan is not None:
                raise ValueError(
                    f"access_vlan_id cannot be set when port_mode is TRUNK (Interface ID: {self.id})"
                )
        else:  # UNCONFIGURED or other modes
            if access_vlan is not None:
                raise ValueError(
                    f"access_vlan_id cannot be set when port_mode is {mode} (Interface ID: {self.id})"
                )
            if allowed_vlans:
                raise ValueError(
                    f"allowed_vlan_ids cannot be set when port_mode is {mode} (Interface ID: {self.id})"
                )
        return self

    def to_rdf(self, g: Graph):
        iface_uri = super().to_rdf(g)
        if self.address:
            g.add((iface_uri, NETWORK.Address, Literal(self.address)))
        if self.connected_to_link_id:
            link_uri = EX[self.connected_to_link_id]
            g.add((iface_uri, NETWORK.ConnectedToLink, link_uri))
            g.add((link_uri, NETWORK.hasInterface, iface_uri))
        if self.belongs_to_node_id:
            node_uri = EX[self.belongs_to_node_id]
            g.add((iface_uri, NETWORK.BelongsToNode, node_uri))

        g.add((iface_uri, NETWORK.portMode, Literal(self.port_mode)))
        if self.port_mode == "ACCESS" and self.access_vlan_id is not None:
            vlan_uri = EX[f"VLAN{self.access_vlan_id}"]
            g.add((iface_uri, NETWORK.accessVlan, vlan_uri))
        elif self.port_mode == "TRUNK":
            for vlan_id in self.allowed_vlan_ids:
                vlan_uri = EX[f"VLAN{vlan_id}"]
                g.add((iface_uri, NETWORK.allowedVlan, vlan_uri))
        return iface_uri


class Link(HWNetEntity):
    bandwidth: Optional[int] = Field(default=None, alias="Bandwidth")
    technology: Optional[str] = Field(default=None, alias="Technology")
    cost: Optional[int] = Field(default=None, alias="Cost")
    interface_ids: List[str] = Field(default_factory=list)

    def to_rdf(self, g: Graph):
        link_uri = super().to_rdf(g)
        if self.bandwidth is not None:
            g.add((link_uri, NETWORK.Bandwidth, Literal(self.bandwidth)))
        if self.technology is not None:
            g.add((link_uri, NETWORK.Technology, Literal(self.technology)))
        if self.cost is not None:
            g.add((link_uri, NETWORK.Cost, Literal(self.cost)))
        return link_uri


class Node(HWNetEntity):
    has_iface_ids: List[str] = Field(default_factory=list, alias="HasIFace")
    has_neighbor_ids: List[str] = Field(default_factory=list, alias="HasNeighbor")

    def to_rdf(self, g: Graph):
        node_uri = super().to_rdf(g)
        for iface_id in self.has_iface_ids:
            iface_uri = EX[iface_id]
            g.add((node_uri, NETWORK.HasIFace, iface_uri))
            if (iface_uri, NETWORK.BelongsToNode, node_uri) not in g:
                g.add((iface_uri, NETWORK.BelongsToNode, node_uri))
        for neighbor_id in self.has_neighbor_ids:
            neighbor_uri = EX[neighbor_id]
            g.add((node_uri, NETWORK.HasNeighbor, neighbor_uri))
            if (neighbor_uri, NETWORK.HasNeighbor, node_uri) not in g:
                g.add((neighbor_uri, NETWORK.HasNeighbor, node_uri))
        return node_uri


class Host(Node):
    pass


class Router(Node):
    pass


class Switch(Node):
    pass

