from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import List, Optional, Literal as PydanticLiteral
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, OWL, XSD
import click # Keep for debug prints in validator for now

# Define Namespaces (Keep here or move to a constants.py if preferred)
NETWORK = Namespace("http://www.example.org/network-ontology#")
EX = Namespace("http://www.example.org/network-instance#")


class BaseEntity(BaseModel):
    """Base class for all network entities, providing common fields and RDF serialization logic."""
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
        entity_uri = self.to_uri() # Use the dedicated method
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
        entity_uri = self.to_uri() # Use the dedicated method
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
    """Represents a Virtual Local Area Network (VLAN)."""
    model_config = ConfigDict(
        populate_by_name=True
    )
    vlan_id: int = Field(..., alias="vlanId", description="The numeric ID of the VLAN (e.g., 10, 20).")
    name: Optional[str] = Field(default=None, alias="vlanName", description="An optional descriptive name for the VLAN (e.g., 'Users', 'Servers').")
    has_subnet_ids: List[str] = Field(default_factory=list, alias="hasSubnet", description="List of Subnet IDs associated with this VLAN.")

    def to_rdf(self, g: Graph) -> URIRef:
        """Serializes the VLAN attributes to RDF."""
        vlan_instance_uri = self.to_uri() # Use the dedicated method
        # Add base properties explicitly
        g.add((vlan_instance_uri, RDF.type, NETWORK.VLAN))
        g.add((vlan_instance_uri, RDFS.label, Literal(self.id)))
        if self.description:
            g.add((vlan_instance_uri, RDFS.comment, Literal(self.description)))

        # Add VLAN-specific properties
        g.add((vlan_instance_uri, NETWORK.vlanId, Literal(self.vlan_id, datatype=XSD.integer)))
        if self.name:
            g.add((vlan_instance_uri, NETWORK.vlanName, Literal(self.name)))

        # Add subnet relationships using Subnet's to_uri (assuming we have IDs)
        for subnet_id in self.has_subnet_ids:
            subnet_uri = EX[subnet_id] # Use the ID directly as it matches the target URI
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
        subnet_uri = self.to_uri() # Use the dedicated method
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
        populate_by_name=True
    )
    ip_value: str = Field(..., alias="ipValue", description="The literal IP address string (e.g., '192.168.1.100').")
    on_subnet_id: str = Field(..., alias="onSubnet", description="The ID of the Subnet this address belongs to.")

    def to_rdf(self, g: Graph) -> URIRef:
        """Serializes the AddressAssignment attributes to RDF."""
        assignment_uri = self.to_uri() # Use the dedicated method
        # Add base properties explicitly
        g.add((assignment_uri, RDF.type, NETWORK.AddressAssignment))
        g.add((assignment_uri, RDFS.label, Literal(self.id)))
        if self.description:
            g.add((assignment_uri, RDFS.comment, Literal(self.description)))

        # Add AddressAssignment-specific properties
        g.add((assignment_uri, NETWORK.ipValue, Literal(self.ip_value)))
        # Link to the subnet using the Subnet's ID (which matches its URI pattern)
        subnet_uri = EX[self.on_subnet_id]
        g.add((assignment_uri, NETWORK.onSubnet, subnet_uri))
        return assignment_uri


class Iface(HWNetEntity):
    """Represents a network interface on a hardware device."""
    model_config = ConfigDict(
        populate_by_name=True
    )
    has_address_assignments: List[AddressAssignment] = Field(
        default_factory=list, alias="hasAddressAssignment", description="List of IP address assignments for this interface."
    )
    connected_to_link_id: Optional[str] = Field(default=None, alias="ConnectedToLink", description="The ID of the Link this interface connects to.")
    belongs_to_node_id: Optional[str] = Field(default=None, alias="BelongsToNode", description="The ID of the Node this interface belongs to.")
    port_mode: PydanticLiteral["ACCESS", "TRUNK", "UNCONFIGURED"] = Field(
        default="UNCONFIGURED", alias="portMode", description="The switching mode of the port (ACCESS, TRUNK, or UNCONFIGURED)."
    )
    access_vlan_id: Optional[int] = Field(
        default=None, alias="accessVlan", description="The VLAN ID assigned when port_mode is ACCESS."
    )
    allowed_vlan_ids: List[int] = Field(
        default_factory=list, alias="allowedVlan", description="List of allowed VLAN IDs when port_mode is TRUNK."
    )

    @model_validator(mode="after")
    def check_vlan_mode_consistency(self) -> "Iface":
        """Validates that VLAN assignments are consistent with the port_mode."""
        mode = self.port_mode
        access_vlan = self.access_vlan_id
        allowed_vlans = self.allowed_vlan_ids

        if mode == "ACCESS":
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

    def to_rdf(self, g: Graph) -> URIRef:
        """Serializes the Interface attributes to RDF."""
        iface_uri = self.to_uri() # Use the dedicated method
        # Add base properties explicitly (including HWNetEntity)
        g.add((iface_uri, RDF.type, NETWORK.Iface))
        g.add((iface_uri, RDFS.label, Literal(self.id)))
        if self.description:
            g.add((iface_uri, RDFS.comment, Literal(self.description)))
        g.add((iface_uri, NETWORK.HWStatus, Literal(self.hw_status)))

        # Serialize and link AddressAssignments using their to_uri
        for assignment in self.has_address_assignments:
             assignment.to_rdf(g) # Ensure assignment is fully serialized first
             assignment_uri = assignment.to_uri()
             g.add((iface_uri, NETWORK.hasAddressAssignment, assignment_uri))

        # Link to connected Link and parent Node using their IDs
        if self.connected_to_link_id:
            link_uri = EX[self.connected_to_link_id] # Assume Link uses simple ID for URI
            g.add((iface_uri, NETWORK.ConnectedToLink, link_uri))
        if self.belongs_to_node_id:
            node_uri = EX[self.belongs_to_node_id] # Assume Node uses simple ID for URI
            g.add((iface_uri, NETWORK.BelongsToNode, node_uri))

        # Add port mode and VLAN details
        g.add((iface_uri, NETWORK.portMode, Literal(self.port_mode)))
        if self.port_mode == "ACCESS" and self.access_vlan_id is not None:
            # Link to the VLAN instance URI using its ID
            vlan_instance_uri = EX[f"VLAN{self.access_vlan_id}_obj"] # Match example ID pattern
            g.add((iface_uri, NETWORK.accessVlan, vlan_instance_uri))
        elif self.port_mode == "TRUNK":
            for vlan_id in self.allowed_vlan_ids:
                # Link to each allowed VLAN instance URI using its ID
                vlan_instance_uri = EX[f"VLAN{vlan_id}_obj"] # Match example ID pattern
                g.add((iface_uri, NETWORK.allowedVlan, vlan_instance_uri))

        return iface_uri


class Link(HWNetEntity):
    """Represents a physical or logical link connecting network interfaces."""
    bandwidth: Optional[int] = Field(default=None, alias="Bandwidth", description="The bandwidth capacity of the link (e.g., in Mbps).")
    technology: Optional[str] = Field(default=None, alias="Technology", description="The technology used by the link (e.g., 'Ethernet', 'WiFi').")
    cost: Optional[int] = Field(default=None, alias="Cost", description="An administrative cost associated with the link, used for routing protocols.")
    interface_ids: List[str] = Field(default_factory=list, description="List of IDs of Interfaces connected by this link.")

    def to_rdf(self, g: Graph) -> URIRef:
        """Serializes the Link attributes to RDF."""
        link_uri = self.to_uri() # Use the dedicated method
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

        # Link to connected interfaces using their IDs
        for iface_id in self.interface_ids:
            iface_uri = EX[iface_id] # Assume Iface uses simple ID for URI
            g.add((link_uri, NETWORK.hasInterface, iface_uri))
        return link_uri


class Node(HWNetEntity):
    """Represents a network node (device) like a router, switch, or host."""
    has_iface_ids: List[str] = Field(default_factory=list, alias="HasIFace", description="List of IDs of Interfaces belonging to this node.")
    has_neighbor_ids: List[str] = Field(default_factory=list, alias="HasNeighbor", description="List of IDs of neighboring Nodes (typically physically connected).")

    def to_rdf(self, g: Graph) -> URIRef:
        """Serializes the Node attributes to RDF."""
        node_uri = self.to_uri() # Use the dedicated method
        # Add base properties explicitly (including HWNetEntity)
        # Type needs to be specific to subclass (Host, Router, Switch)
        # This base method shouldn't add Node type if it's always subclassed
        # g.add((node_uri, RDF.type, NETWORK.Node)) # Avoid adding generic Node type
        g.add((node_uri, RDFS.label, Literal(self.id)))
        if self.description:
            g.add((node_uri, RDFS.comment, Literal(self.description)))
        g.add((node_uri, NETWORK.HWStatus, Literal(self.hw_status)))

        # Link to Interfaces and add inverse relationship
        for iface_id in self.has_iface_ids:
            iface_uri = EX[iface_id] # Assume Iface uses simple ID for URI
            g.add((node_uri, NETWORK.HasIFace, iface_uri))
            if (iface_uri, NETWORK.BelongsToNode, node_uri) not in g:
                g.add((iface_uri, NETWORK.BelongsToNode, node_uri))

        # Link to Neighbors and add symmetric relationship
        for neighbor_id in self.has_neighbor_ids:
            neighbor_uri = EX[neighbor_id] # Assume Node uses simple ID for URI
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
    routes_subnet_ids: List[str] = Field(default_factory=list, alias="routesSubnet", description="List of Subnet IDs that this router provides routes for.")

    def to_rdf(self, g: Graph) -> URIRef:
        """Serializes the Router attributes to RDF."""
        router_uri = self.to_uri()
        # Add specific type
        g.add((router_uri, RDF.type, NETWORK.Router))
        # Call Node's serialization logic (handles base props, interfaces, neighbors)
        super().to_rdf(g)

        # Add Router-specific properties (routesSubnet)
        for subnet_id in self.routes_subnet_ids:
            # Use the Subnet ID directly as it matches the Subnet URI pattern
            subnet_uri = EX[subnet_id]
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

