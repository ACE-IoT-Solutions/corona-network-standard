import click
from typing import List
from rdflib import Graph, Literal, Namespace
from rdflib.namespace import RDF, RDFS
import sys
from pyshacl import validate

# Local imports
from .models import NETWORK, EX, BaseEntity # Import namespaces and BaseEntity
from .examples import create_example_network
from .utils import get_resource_path

# --- Click CLI Group ---
@click.group()
def cli():
    """Corona Network Standard Tool: Generate and Validate Network RDF Data."""
    pass

# --- Generate Command ---
@cli.command(name="generate")
@click.option('--output-file', '-o', default=None, help='Path to the output RDF file (Turtle format). If not provided, prints to stdout.')
def generate_network_rdf(output_file) -> None:
    """Generates an RDF graph representing the network topology."""

    # --- Get Example Network Entities ---
    entities: List[BaseEntity] = create_example_network()

    # Create an RDF graph
    g = Graph()

    # Bind namespaces
    g.bind("net", NETWORK)
    g.bind("ex", EX)
    g.bind("rdfs", RDFS)
    g.bind("rdf", RDF)

    # --- Define Ontology Structure in RDF (Optional - could be removed if ontology is stable) ---
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
