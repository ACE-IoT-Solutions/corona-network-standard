from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import List, Optional, Literal as PydanticLiteral, TYPE_CHECKING
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, OWL, XSD
import click  # Keep for debug prints in validator for now

# Define Namespaces (Keep here or move to a constants.py if preferred)
NETWORK = Namespace("http://www.example.org/network-ontology#")
EX = Namespace("http://www.example.org/network-instance#")

# Forward references for type checking
if TYPE_CHECKING:
    from .models import Subnet, Link, Node, VLAN, Iface, AddressAssignment


class BaseEntity(BaseModel):
    """Base class for all network entities, providing common fields and RDF serialization logic."""
    model_config = ConfigDict(
        populate_by_name=True
    )
    id: str = Field(..., description="Unique identifier for the instance within the RDF graph.")
    description: Optional[str] = Field(default=None, description="A human-readable description of the entity.")

    def to_uri(self) -> URIRef:
        """Returns the RDF URI for this entity instance."""
        return EX[self.id]

    def to_rdf(self, g: Graph) -> URIRef:
        """
        Serializes the base entity attributes to RDF triples in the provided graph.
        Uses the to_uri() method for the subject URI.
        """
        entity_uri = self.to_uri()  # Use the dedicated method
        g.add((entity_uri, RDF.type, NETWORK[self.__class__.__name__]))
        g.add((entity_uri, RDFS.label, Literal(self.id)))
        if self.description:
            g.add((entity_uri, RDFS.comment, Literal(self.description)))
        return entity_uri


class HWNetEntity(BaseEntity):
    """Base class for hardware network entities, adding hardware status."""
    hw_status: PydanticLiteral["ON", "OFF", "ABN"] = Field(
        default="ON", alias="HWStatus", description="The operational status of the hardware entity."
    )

    def to_rdf(self, g: Graph) -> URIRef:
        """
        Serializes the hardware entity attributes to RDF, including hardware status.
        """
        entity_uri = self.to_uri()  # Use the dedicated method
        # Add base properties explicitly
        g.add((entity_uri, RDF.type, NETWORK[self.__class__.__name__]))
        g.add((entity_uri, RDFS.label, Literal(self.id)))
        if self.description:
            g.add((entity_uri, RDFS.comment, Literal(self.description)))
        # Add HWNetEntity specific property
        g.add((entity_uri, NETWORK.HWStatus, Literal(self.hw_status)))
        return entity_uri


class LogicalEntity(BaseEntity):
    """Base class for logical network entities (e.g., VLANs, Subnets)."""
    pass


class VLAN(LogicalEntity):
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )
    """Represents a Virtual Local Area Network (VLAN)."""
    vlan_id: int = Field(..., alias="vlanId", description="The numeric ID of the VLAN (e.g., 10, 20).")
    name: Optional[str] = Field(default=None, alias="vlanName", description="An optional descriptive name for the VLAN (e.g., 'Users', 'Servers').")
    has_subnets: List['Subnet'] = Field(default_factory=list, alias="hasSubnet", description="List of Subnets associated with this VLAN.")

    def to_rdf(self, g: Graph) -> URIRef:
        """Serializes the VLAN attributes to RDF."""
        vlan_instance_uri = self.to_uri()  # Use the dedicated method
        # Add base properties explicitly
        g.add((vlan_instance_uri, RDF.type, NETWORK.VLAN))
        g.add((vlan_instance_uri, RDFS.label, Literal(self.id)))
        if self.description:
            g.add((vlan_instance_uri, RDFS.comment, Literal(self.description)))

        # Add VLAN-specific properties
        g.add((vlan_instance_uri, NETWORK.vlanId, Literal(self.vlan_id, datatype=XSD.integer)))
        if self.name:
            g.add((vlan_instance_uri, NETWORK.vlanName, Literal(self.name)))

        # Add subnet relationships using Subnet object's URI
        for subnet in self.has_subnets:
            subnet_uri = subnet.to_uri()
            g.add((vlan_instance_uri, NETWORK.hasSubnet, subnet_uri))

        return vlan_instance_uri


class Subnet(LogicalEntity):
    """Represents a network subnet defined by a CIDR block."""
    model_config = ConfigDict(
        populate_by_name=True
    )
    cidr: str = Field(..., alias="subnetCidr", description="The CIDR notation for the subnet (e.g., '192.168.1.0/24').")

    def to_uri(self) -> URIRef:
        """Returns the RDF URI for this Subnet, based on its CIDR."""
        safe_cidr_id = self.cidr.replace('/', '_')
        return EX[f"Subnet_{safe_cidr_id}"]

    def to_rdf(self, g: Graph) -> URIRef:
        """Serializes the Subnet attributes to RDF."""
        subnet_uri = self.to_uri()  # Use the dedicated method
        # Add base properties explicitly
        g.add((subnet_uri, RDF.type, NETWORK.Subnet))
        # Use a more descriptive label than the potentially non-CIDR self.id
        g.add((subnet_uri, RDFS.label, Literal(f"Subnet {self.cidr}")))
        if self.description:
            g.add((subnet_uri, RDFS.comment, Literal(self.description)))

        # Add Subnet-specific properties
        g.add((subnet_uri, NETWORK.subnetCidr, Literal(self.cidr, datatype=XSD.string)))
        return subnet_uri


class AddressAssignment(BaseEntity):
    """Represents the assignment of a specific IP address to an interface within a subnet."""
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )
    ip_value: str = Field(..., alias="ipValue", description="The literal IP address string (e.g., '192.168.1.100').")
    on_subnet: 'Subnet' = Field(..., alias="onSubnet", description="The Subnet this address belongs to.")

    def to_rdf(self, g: Graph) -> URIRef:
        """Serializes the AddressAssignment attributes to RDF."""
        assignment_uri = self.to_uri()  # Use the dedicated method
        # Add base properties explicitly
        g.add((assignment_uri, RDF.type, NETWORK.AddressAssignment))
        g.add((assignment_uri, RDFS.label, Literal(self.id)))
        if self.description:
            g.add((assignment_uri, RDFS.comment, Literal(self.description)))

        # Add AddressAssignment-specific properties
        g.add((assignment_uri, NETWORK.ipValue, Literal(self.ip_value)))
        # Link to the subnet using the Subnet object's URI
        g.add((assignment_uri, NETWORK.onSubnet, self.on_subnet.to_uri()))
        return assignment_uri


class Iface(HWNetEntity):
    """Represents a network interface on a hardware device."""
    model_config = ConfigDict(
        populate_by_name=True
    )
    has_address_assignments: List['AddressAssignment'] = Field(
        default_factory=list, alias="hasAddressAssignment", description="List of IP address assignments for this interface."
    )
    connected_to_link: Optional['Link'] = Field(default=None, alias="ConnectedToLink", description="The Link this interface connects to.")
    belongs_to_node: Optional['Node'] = Field(default=None, alias="BelongsToNode", description="The Node this interface belongs to.")
    port_mode: PydanticLiteral["ACCESS", "TRUNK", "UNCONFIGURED"] = Field(
        default="UNCONFIGURED", alias="portMode", description="The switching mode of the port (ACCESS, TRUNK, or UNCONFIGURED)."
    )
    access_vlan: Optional['VLAN'] = Field(
        default=None, alias="accessVlan", description="The VLAN assigned when port_mode is ACCESS."
    )
    allowed_vlans: List['VLAN'] = Field(
        default_factory=list, alias="allowedVlan", description="List of allowed VLANs when port_mode is TRUNK."
    )

    @model_validator(mode="after")
    def check_vlan_mode_consistency(self) -> "Iface":
        """Validates that VLAN assignments are consistent with the port_mode."""
        mode = self.port_mode
        access_vlan = self.access_vlan
        allowed_vlans = self.allowed_vlans

        if mode == "ACCESS":
            if allowed_vlans:
                raise ValueError(
                    f"allowed_vlans cannot be set when port_mode is ACCESS (Interface ID: {self.id})"
                )
        elif mode == "TRUNK":
            if access_vlan is not None:
                raise ValueError(
                    f"access_vlan cannot be set when port_mode is TRUNK (Interface ID: {self.id})"
                )
        else:  # UNCONFIGURED or other modes
            if access_vlan is not None:
                raise ValueError(
                    f"access_vlan cannot be set when port_mode is {mode} (Interface ID: {self.id})"
                )
            if allowed_vlans:
                raise ValueError(
                    f"allowed_vlans cannot be set when port_mode is {mode} (Interface ID: {self.id})"
                )
        return self

    def to_rdf(self, g: Graph) -> URIRef:
        """Serializes the Interface attributes to RDF."""
        iface_uri = self.to_uri()  # Use the dedicated method
        # Add base properties explicitly (including HWNetEntity)
        g.add((iface_uri, RDF.type, NETWORK.Iface))
        g.add((iface_uri, RDFS.label, Literal(self.id)))
        if self.description:
            g.add((iface_uri, RDFS.comment, Literal(self.description)))
        g.add((iface_uri, NETWORK.HWStatus, Literal(self.hw_status)))

        # Serialize and link AddressAssignments using their to_uri
        for assignment in self.has_address_assignments:
            assignment.to_rdf(g)  # Ensure assignment is fully serialized first
            assignment_uri = assignment.to_uri()
            g.add((iface_uri, NETWORK.hasAddressAssignment, assignment_uri))

        # Link to connected Link and parent Node using their objects' URIs
        if self.connected_to_link:
            link_uri = self.connected_to_link.to_uri()
            g.add((iface_uri, NETWORK.ConnectedToLink, link_uri))
            if (link_uri, NETWORK.hasInterface, iface_uri) not in g:
                g.add((link_uri, NETWORK.hasInterface, iface_uri))

        if self.belongs_to_node:
            node_uri = self.belongs_to_node.to_uri()
            g.add((iface_uri, NETWORK.BelongsToNode, node_uri))
            if (node_uri, NETWORK.HasIFace, iface_uri) not in g:
                g.add((node_uri, NETWORK.HasIFace, iface_uri))

        # Add port mode and VLAN details
        g.add((iface_uri, NETWORK.portMode, Literal(self.port_mode)))
        if self.port_mode == "ACCESS" and self.access_vlan:
            vlan_instance_uri = self.access_vlan.to_uri()
            g.add((iface_uri, NETWORK.accessVlan, vlan_instance_uri))
        elif self.port_mode == "TRUNK":
            for vlan in self.allowed_vlans:
                vlan_instance_uri = vlan.to_uri()
                g.add((iface_uri, NETWORK.allowedVlan, vlan_instance_uri))

        return iface_uri


class Link(HWNetEntity):
    """Represents a physical or logical link connecting network interfaces."""
    bandwidth: Optional[int] = Field(default=None, alias="Bandwidth", description="The bandwidth capacity of the link (e.g., in Mbps).")
    technology: Optional[str] = Field(default=None, alias="Technology", description="The technology used by the link (e.g., 'Ethernet', 'WiFi').")
    cost: Optional[int] = Field(default=None, alias="Cost", description="An administrative cost associated with the link, used for routing protocols.")
    interfaces: List['Iface'] = Field(default_factory=list, description="List of Interfaces connected by this link.")

    def to_rdf(self, g: Graph) -> URIRef:
        """Serializes the Link attributes to RDF."""
        link_uri = self.to_uri()  # Use the dedicated method
        # Add base properties explicitly (including HWNetEntity)
        g.add((link_uri, RDF.type, NETWORK.Link))
        g.add((link_uri, RDFS.label, Literal(self.id)))
        if self.description:
            g.add((link_uri, RDFS.comment, Literal(self.description)))
        g.add((link_uri, NETWORK.HWStatus, Literal(self.hw_status)))

        # Add Link-specific properties
        if self.bandwidth is not None:
            g.add((link_uri, NETWORK.Bandwidth, Literal(self.bandwidth)))
        if self.technology is not None:
            g.add((link_uri, NETWORK.Technology, Literal(self.technology)))
        if self.cost is not None:
            g.add((link_uri, NETWORK.Cost, Literal(self.cost)))

        # Link to connected interfaces using their URIs
        for iface in self.interfaces:
            iface_uri = iface.to_uri()
            g.add((link_uri, NETWORK.hasInterface, iface_uri))
            if (iface_uri, NETWORK.ConnectedToLink, link_uri) not in g:
                g.add((iface_uri, NETWORK.ConnectedToLink, link_uri))
        return link_uri


class Node(HWNetEntity):
    """Represents a network node (device) like a router, switch, or host."""
    has_ifaces: List['Iface'] = Field(default_factory=list, alias="HasIFace", description="List of Interfaces belonging to this node.")
    has_neighbors: List['Node'] = Field(default_factory=list, alias="HasNeighbor", description="List of neighboring Nodes (typically physically connected).")

    def to_rdf(self, g: Graph) -> URIRef:
        """Serializes the Node attributes to RDF."""
        node_uri = self.to_uri()  # Use the dedicated method
        g.add((node_uri, RDFS.label, Literal(self.id)))
        if self.description:
            g.add((node_uri, RDFS.comment, Literal(self.description)))
        g.add((node_uri, NETWORK.HWStatus, Literal(self.hw_status)))

        # Link to Interfaces and add inverse relationship
        for iface in self.has_ifaces:
            iface_uri = iface.to_uri()
            g.add((node_uri, NETWORK.HasIFace, iface_uri))
            if (iface_uri, NETWORK.BelongsToNode, node_uri) not in g:
                g.add((iface_uri, NETWORK.BelongsToNode, node_uri))

        # Link to Neighbors and add symmetric relationship
        for neighbor in self.has_neighbors:
            neighbor_uri = neighbor.to_uri()
            g.add((node_uri, NETWORK.HasNeighbor, neighbor_uri))
            if (neighbor_uri, NETWORK.HasNeighbor, node_uri) not in g:
                g.add((neighbor_uri, NETWORK.HasNeighbor, node_uri))
        return node_uri


class Host(Node):
    """Represents an end-user device like a computer or server."""
    def to_rdf(self, g: Graph) -> URIRef:
        """Serializes the Host attributes to RDF."""
        host_uri = self.to_uri()
        # Add specific type
        g.add((host_uri, RDF.type, NETWORK.Host))
        # Call Node's serialization logic (handles base props, interfaces, neighbors)
        super().to_rdf(g)
        return host_uri


class Router(Node):
    """Represents a network router responsible for forwarding packets between networks."""
    routes_subnets: List['Subnet'] = Field(default_factory=list, alias="routesSubnet", description="List of Subnets that this router provides routes for.")

    def to_rdf(self, g: Graph) -> URIRef:
        """Serializes the Router attributes to RDF."""
        router_uri = self.to_uri()
        # Add specific type
        g.add((router_uri, RDF.type, NETWORK.Router))
        # Call Node's serialization logic (handles base props, interfaces, neighbors)
        super().to_rdf(g)

        # Add Router-specific properties (routesSubnet)
        for subnet in self.routes_subnets:
            subnet_uri = subnet.to_uri()
            g.add((router_uri, NETWORK.routesSubnet, subnet_uri))
        return router_uri


class Switch(Node):
    """Represents a network switch responsible for forwarding frames within a LAN."""
    def to_rdf(self, g: Graph) -> URIRef:
        """Serializes the Switch attributes to RDF."""
        switch_uri = self.to_uri()
        # Add specific type
        g.add((switch_uri, RDF.type, NETWORK.Switch))
        # Call Node's serialization logic (handles base props, interfaces, neighbors)
        super().to_rdf(g)
        return switch_uri

