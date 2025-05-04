import click
from rdflib import Graph, Literal, Namespace
from rdflib.namespace import RDF, RDFS
import importlib.resources
import sys

# Updated import for Pydantic V2 validator
from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import List, Optional, Literal as PydanticLiteral

# Import pyshacl
from pyshacl import validate

# Define Namespaces
NETWORK = Namespace("http://www.example.org/network-ontology#")
EX = Namespace("http://www.example.org/network-instance#")

# --- Pydantic Models based on Ontology (Extended with V2 Validators) ---


class BaseEntity(BaseModel):
    id: str  # Unique identifier for the instance

    def to_rdf(self, g: Graph):
        entity_uri = EX[self.id]
        g.add((entity_uri, RDF.type, NETWORK[self.__class__.__name__]))
        g.add((entity_uri, RDFS.label, Literal(self.id)))
        return entity_uri


class HWNetEntity(BaseEntity):
    # Use Field default for Pydantic V2 compatibility if needed, or keep as is
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
    )  # Pydantic V2 config for field aliasing
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
        populate_by_name=True # Ensure aliases are used during validation
    )
    address: Optional[str] = Field(default=None, alias="Address")
    connected_to_link_id: Optional[str] = Field(default=None, alias="ConnectedToLink")
    belongs_to_node_id: Optional[str] = Field(default=None, alias="BelongsToNode")

    # Layer 2 Additions - Restore aliases
    port_mode: PydanticLiteral["ACCESS", "TRUNK", "UNCONFIGURED"] = Field(
        default="UNCONFIGURED", alias="portMode"
    )
    access_vlan_id: Optional[int] = Field(
        default=None, alias="accessVlan"
    )  # VLAN ID if mode is ACCESS
    allowed_vlan_ids: List[int] = Field(
        default_factory=list, alias="allowedVlan"
    )  # List of VLAN IDs if mode is TRUNK

    # --- Pydantic V2 Model Validator (cleaned up) ---
    @model_validator(mode="after")
    def check_vlan_mode_consistency(self) -> "Iface":
        # ... validator logic remains the same ...
        mode = self.port_mode
        access_vlan = self.access_vlan_id
        allowed_vlans = self.allowed_vlan_ids

        if mode == "ACCESS":
            if not access_vlan:
                # Technically an access port *should* have a VLAN, but maybe default is allowed
                # Depending on strictness, you could raise ValueError("Access port must have an access_vlan_id")
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
            # Optionally check if allowed_vlan_ids is empty, though an empty trunk might be valid
            # if not allowed_vlans:
            #     raise ValueError("Trunk port must have at least one allowed_vlan_id")
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

    # --- End V2 Validator ---

    def to_rdf(self, g: Graph):
        iface_uri = super().to_rdf(g)
        if self.address:
            g.add((iface_uri, NETWORK.Address, Literal(self.address)))
        if self.connected_to_link_id:
            link_uri = EX[self.connected_to_link_id]
            g.add((iface_uri, NETWORK.ConnectedToLink, link_uri))
            g.add((link_uri, NETWORK.hasInterface, iface_uri))  # Inverse from Link
        if self.belongs_to_node_id:
            node_uri = EX[self.belongs_to_node_id]
            g.add((iface_uri, NETWORK.BelongsToNode, node_uri))

        # Use aliases (via model_config) when adding triples
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
        # Inverse relationship added via Iface.to_rdf
        return link_uri


class Node(HWNetEntity):
    has_iface_ids: List[str] = Field(default_factory=list, alias="HasIFace")
    has_neighbor_ids: List[str] = Field(default_factory=list, alias="HasNeighbor")

    def to_rdf(self, g: Graph):
        node_uri = super().to_rdf(g)
        for iface_id in self.has_iface_ids:
            iface_uri = EX[iface_id]
            g.add((node_uri, NETWORK.HasIFace, iface_uri))
            # Add inverse BelongsToNode - make sure Iface object also adds it or handle here
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


# --- Helper function to get package data path ---
def get_resource_path(package: str, resource: str) -> str:
    """Gets the path to a resource within the package."""
    try:
        # Use files() for modern Python (returns Traversable)
        # The path needs to be resolved within the context manager
        with importlib.resources.files(package) as package_path:
            resource_path = package_path / resource
            if resource_path.is_file():
                # Ensure the path is resolved to a string before exiting the context
                resolved_path = str(resource_path.resolve())
                return resolved_path
            else:
                raise FileNotFoundError(f"Resource not found or not a file: {resource} in {package}")
    except (ImportError, AttributeError, FileNotFoundError, TypeError) as e:
        # Fallback for older Python or if files() fails
        click.echo(f"Using fallback importlib.resources.path due to error: {e}", err=True)
        try:
            with importlib.resources.path(package, resource) as p:
                 return str(p)
        except Exception as fallback_e:
            click.echo(f"Error finding resource {resource} in package {package} using fallback: {fallback_e}", err=True)
            sys.exit(1)

# --- Click CLI Group ---
@click.group()
def cli():
    """Corona Network Standard Tool: Generate and Validate Network RDF Data."""
    pass

# --- Generate Command ---
@cli.command(name="generate")
@click.option('--output-file', '-o', default=None, help='Path to the output RDF file (Turtle format). If not provided, prints to stdout.')
def generate_network_rdf(output_file):
    """Generates an RDF graph representing the network topology."""

    # --- Example Network Construction (Moved inside the function) ---

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
    # --- End Example Network Construction ---

    # Create an RDF graph
    g = Graph()

    # Bind namespaces
    g.bind("net", NETWORK)
    g.bind("ex", EX)
    g.bind("rdfs", RDFS)
    g.bind("rdf", RDF)

    # --- Define Ontology Structure in RDF ---
    # Classes
    g.add((NETWORK.NetEntity, RDFS.subClassOf, RDFS.Resource))
    g.add((NETWORK.HWNetEntity, RDFS.subClassOf, NETWORK.NetEntity))
    g.add((NETWORK.SWNetEntity, RDFS.subClassOf, NETWORK.NetEntity))  # If needed
    g.add(
        (NETWORK.LogicalEntity, RDFS.subClassOf, RDFS.Resource)
    )  # Base for logical things
    g.add((NETWORK.Node, RDFS.subClassOf, NETWORK.HWNetEntity))
    g.add((NETWORK.Router, RDFS.subClassOf, NETWORK.Node))
    g.add((NETWORK.Host, RDFS.subClassOf, NETWORK.Node))
    g.add((NETWORK.Switch, RDFS.subClassOf, NETWORK.Node))
    g.add((NETWORK.Iface, RDFS.subClassOf, NETWORK.HWNetEntity))
    g.add((NETWORK.Link, RDFS.subClassOf, NETWORK.HWNetEntity))
    g.add((NETWORK.VLAN, RDFS.subClassOf, NETWORK.LogicalEntity))
    # Properties (Object Properties)
    g.add((NETWORK.HasIFace, RDF.type, RDF.Property))
    g.add((NETWORK.BelongsToNode, RDF.type, RDF.Property))
    g.add((NETWORK.ConnectedToLink, RDF.type, RDF.Property))
    g.add((NETWORK.HasNeighbor, RDF.type, RDF.Property))
    g.add((NETWORK.hasInterface, RDF.type, RDF.Property))
    g.add((NETWORK.accessVlan, RDF.type, RDF.Property))
    g.add((NETWORK.accessVlan, RDFS.range, NETWORK.VLAN))
    g.add((NETWORK.accessVlan, RDFS.domain, NETWORK.Iface))
    g.add((NETWORK.allowedVlan, RDF.type, RDF.Property))
    g.add((NETWORK.allowedVlan, RDFS.range, NETWORK.VLAN))
    g.add((NETWORK.allowedVlan, RDFS.domain, NETWORK.Iface))
    # Properties (Datatype Properties)
    g.add((NETWORK.HWStatus, RDF.type, RDF.Property))
    g.add((NETWORK.Address, RDF.type, RDF.Property))
    g.add((NETWORK.Bandwidth, RDF.type, RDF.Property))
    g.add((NETWORK.Technology, RDF.type, RDF.Property))
    g.add((NETWORK.Cost, RDF.type, RDF.Property))
    g.add((NETWORK.portMode, RDF.type, RDF.Property))
    g.add((NETWORK.vlanId, RDF.type, RDF.Property))
    g.add((NETWORK.vlanName, RDF.type, RDF.Property))

    # --- Populate Graph ---
    for entity in entities:
        try:
            entity.to_rdf(g)
        except Exception as e:
            # Use click.echo for consistency and stderr for errors
            click.echo(f"Error processing entity {entity.id}: {e}", file=sys.stderr)

    # --- Output ---
    rdf_output = g.serialize(format="turtle")

    if output_file:
        with open(output_file, "w") as f:
            f.write(rdf_output)
        click.echo(f"--- RDF Graph saved to {output_file} ---")
    else:
        click.echo("--- RDF Graph (Turtle) ---")
        click.echo(rdf_output)

    click.echo("\n--- Generation Complete ---")

# --- Validate Command ---
@cli.command(name="validate")
@click.argument('data-graph-file', type=click.Path(exists=True, dir_okay=False))
@click.option('--shapes-file', '-s', default=None, help='Path to the SHACL shapes file (Turtle format). Defaults to the packaged shapes file.')
@click.option('--ontology-file', '-t', default=None, help='Path to the ontology file (Turtle format). Defaults to the packaged ontology file.')
def validate_network_rdf(data_graph_file, shapes_file, ontology_file):
    """Validates a network RDF data graph against SHACL shapes."""

    # Determine shapes file path
    if shapes_file:
        shacl_graph_path = shapes_file
    else:
        shacl_graph_path = get_resource_path("corona_network_standard.data.shapes", "network-shapes.ttl")
        click.echo(f"Using packaged shapes file: {shacl_graph_path}")

    # Determine ontology file path (optional, for inference)
    ont_graph_path = None
    if ontology_file:
        ont_graph_path = ontology_file
    else:
        # Optionally load the packaged ontology for inference
        try:
            ont_graph_path = get_resource_path("corona_network_standard.data.ontology", "network-ontology.ttl")
            click.echo(f"Using packaged ontology file for inference: {ont_graph_path}")
        except FileNotFoundError:
            click.echo("Packaged ontology file not found, proceeding without ontology inference.")
            ont_graph_path = None

    click.echo(f"Validating data graph: {data_graph_file}")

    try:
        # Load graphs
        data_graph = Graph().parse(data_graph_file, format="turtle")
        shacl_graph = Graph().parse(shacl_graph_path, format="turtle")
        ont_graph = Graph().parse(ont_graph_path, format="turtle") if ont_graph_path else None

        # Perform validation
        conforms, results_graph, results_text = validate(
            data_graph,
            shacl_graph=shacl_graph,
            ont_graph=ont_graph,  # Pass ontology graph for potential inference
            meta_shacl=False,
            advanced=True,
            js=False, # Set to True if using SHACL-JS extensions
            debug=False,
            inference='rdfs' if ont_graph else 'none' # Use RDFS inference if ontology provided
        )

        # Print results
        click.echo("\n--- Validation Results ---")
        if conforms:
            click.secho("Data graph conforms to the SHACL shapes.", fg="green")
        else:
            click.secho("Data graph does NOT conform to the SHACL shapes.", fg="red")
            click.echo("Validation Report:")
            click.echo(results_text)
            sys.exit(1) # Exit with error code if validation fails

    except Exception as e:
        click.secho(f"Error during validation: {e}", fg="red")
        sys.exit(1)


if __name__ == "__main__":
    cli()
