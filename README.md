# Ontology for OT Network Architecture

[![Python Tests & Coverage](https://github.com/ACE-IoT-Solutions/corona-network-standard/actions/workflows/python-test.yml/badge.svg)](https://github.com/ACE-IoT-Solutions/corona-network-standard/actions/workflows/python-test.yml)
[![codecov](https://codecov.io/gh/ACE-IoT-Solutions/corona-network-standard/graph/badge.svg)](https://codecov.io/gh/ACE-IoT-Solutions/corona-network-standard) 
<!-- TODO: Replace YOUR_CODECOV_TOKEN_HERE in the badge URL if your repo is private and requires tokens for badges -->

## Description

This project provides a Python script (`main.py`) that demonstrates how to model computer network components and their relationships using Pydantic classes, based on concepts from a network management ontology. It then uses the RDFLib library to translate instances of these Pydantic models into an RDF graph, representing a sample network topology including Layer 1, Layer 2 (Switches, VLANs), and basic Layer 3 elements.

This project is intended to provide additional context and a reference ontology for network architecture to support the [Corona Framework](https://github.com/ACE-IoT-Solutions/corona-framework) which provides an interoperable model for OT Network Performance Metrics.

The ontology concepts are primarily inspired by the work described in the paper referenced below.

## Based On

The modeling concepts are derived from the ontology presented in:

* De Paola, A., Gatani, L., Lo Re, G., Pizzitola, A., & Urso, A. (2003). *A Network Ontology for Computer Network Management* (Technical Report RT-ICAR-PA-03-22). ICAR-CNR.
    *(The user provided `NetworkOntologyForComputerNetworkManagement.pdf`)*

While this script doesn't implement the entire extensive ontology from the paper, it focuses on core structural and Layer 2 elements as a practical example.

## Features

* Uses **Pydantic** for clear, validated data modeling of network entities.
* Uses **RDFLib** to generate RDF graphs based on the model instances.
* Models core network hardware entities: `Node`, `Router`, `Switch`, `Host`, `Iface`, `Link`.
* Includes Layer 2 concepts: `VLAN`, Interface `portMode` (ACCESS/TRUNK), `accessVlan`, `allowedVlan` relationships.
* Includes Layer 3 concepts: `Subnet`, `AddressAssignment`, `routesSubnet`.
* Supports adding human-readable `description` fields to models, serialized as `rdfs:comment`.
* Defines basic RDF Schema (RDFS) for the modeled classes and properties within the generated graph.
* Includes a concrete example network demonstrating the usage.
* Outputs the resulting network representation as an RDF graph in **Turtle (.ttl)** format.
* Provides a CLI command to **validate** RDF data against packaged SHACL shapes and ontology.

## Requirements

* Python 3.8+
* Pydantic
* RDFLib
* Click

Dependencies are listed in `pyproject.toml` and can be installed using pip:
```bash
pip install .
# Or using uv:
# uv pip install .
```

## Usage

1.  **Clone the repository:**
    ```bash
    # Replace with actual repository URL
    git clone <repository-url>
    cd corona-network-standard
    ```
2.  **Install dependencies (including the tool itself):**
    ```bash
    pip install .
    # Or for development (including test dependencies):
    # pip install -e .[dev]
    # Or using uv:
    # uv pip install .
    # uv pip install -e .[dev]
    ```
3.  **Run the tool:**

    The tool provides two main commands: `generate` and `validate`.

    *   **Generate Example Network Data:**
        *   To print the generated RDF graph (Turtle format) to the console:
            ```bash
            corona-network-tool generate
            ```
        *   To save the output to a file (e.g., `example-network-data.ttl`):
            ```bash
            corona-network-tool generate -o example-network-data.ttl
            ```
            or
            ```bash
            corona-network-tool generate --output-file example-network-data.ttl
            ```

    *   **Validate Network Data:**
        *   To validate an existing RDF file (e.g., the one generated above) against the packaged SHACL shapes and ontology:
            ```bash
            corona-network-tool validate example-network-data.ttl
            ```
        *   To validate using custom shapes or ontology files:
            ```bash
            corona-network-tool validate your-data.ttl -s path/to/your-shapes.ttl -t path/to/your-ontology.ttl
            ```

## Ontology Concepts Modeled (in Script)

The script currently models and generates RDF for the following main concepts:

* **Classes:**
    * `net:HWNetEntity` (Base for hardware)
    * `net:Node` (Superclass for devices)
    * `net:Router`
    * `net:Switch`
    * `net:Host`
    * `net:Iface` (Network Interface)
    * `net:Link` (Physical Link)
    * `net:LogicalEntity` (Base for logical constructs)
    * `net:VLAN` (Virtual LAN)
    * `net:Subnet`
    * `net:AddressAssignment`
* **Key Properties:**
    * `rdf:type`, `rdfs:label`, `rdfs:comment` (for descriptions)
    * `net:HWStatus` (ON, OFF, ABN)
    * `net:HasIFace` / `net:BelongsToNode` (Node <-> Iface)
    * `net:ConnectedToLink` / `net:hasInterface` (Iface <-> Link)
    * `net:HasNeighbor` (Node <-> Node)
    * `net:ipValue` (Literal IP on AddressAssignment)
    * `net:onSubnet` (AddressAssignment -> Subnet)
    * `net:hasAddressAssignment` (Iface -> AddressAssignment)
    * `net:subnetCidr` (Literal CIDR on Subnet)
    * `net:routesSubnet` (Router -> Subnet)
    * `net:Bandwidth`, `net:Technology`, `net:Cost` (Link properties)
    * `net:portMode` (ACCESS, TRUNK, UNCONFIGURED on Iface)
    * `net:vlanId`, `net:vlanName` (VLAN properties)
    * `net:hasSubnet` (VLAN -> Subnet)
    * `net:accessVlan` (Iface -> VLAN relationship for access ports)
    * `net:allowedVlan` (Iface -> VLAN relationship for trunk ports)

*(Note: `net:` corresponds to the namespace `http://www.example.org/network-ontology#` and `ex:` to `http://www.example.org/network-instance#` in the script).*

## Example Output Snippet (Turtle)

```turtle
@prefix ex: <http://www.example.org/network-instance#> .
@prefix net: <http://www.example.org/network-ontology#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

# ... Ontology Definitions (Classes, Properties) ...

ex:Subnet_10.0.10.0_24 a net:Subnet ;
    rdfs:label "Subnet 10.0.10.0/24" ;
    rdfs:comment "Subnet for user devices" ;
    net:subnetCidr "10.0.10.0/24"^^xsd:string .

ex:VLAN10_obj a net:VLAN ;
    rdfs:label "VLAN10_obj" ;
    rdfs:comment "VLAN for general user access" ;
    net:hasSubnet ex:Subnet_10.0.10.0_24 ;
    net:vlanId 10 ;
    net:vlanName "Users" .

ex:Switch1 a net:Switch ;
    rdfs:label "Switch1" ;
    rdfs:comment "Access layer switch 1" ;
    net:HWStatus "ON" ;
    net:HasIFace ex:Sw1_Fa0-1,
        ex:Sw1_Fa0-2,
        ex:Sw1_Gi0-1 ;
    net:HasNeighbor ex:Host1,
        ex:Router1 .

ex:Sw1_Fa0-1 a net:Iface ;
    rdfs:label "Sw1_Fa0-1" ;
    net:HWStatus "ON" ;
    net:BelongsToNode ex:Switch1 ;
    net:ConnectedToLink ex:Link_Sw1_H1 ;
    net:accessVlan ex:VLAN10_obj ;
    net:portMode "ACCESS" .

# ... other entities and relationships ...