# Pydantic to RDF Network Ontology Mapper

## Description

This project provides a Python script (`main.py`) that demonstrates how to model computer network components and their relationships using Pydantic classes, based on concepts from a network management ontology. It then uses the RDFLib library to translate instances of these Pydantic models into an RDF graph, representing a sample network topology including Layer 1, Layer 2 (Switches, VLANs), and basic Layer 3 elements.

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
* Defines basic RDF Schema (RDFS) for the modeled classes and properties within the generated graph.
* Includes a concrete example network demonstrating the usage.
* Outputs the resulting network representation as an RDF graph in **Turtle (.ttl)** format.

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
2.  **Install dependencies:**
    ```bash
    pip install .
    ```
3.  **Run the script:**
    *   To print the generated RDF graph (Turtle format) to the console:
        ```bash
        python main.py
        ```
    *   To save the output to a file (e.g., `network_graph.ttl`):
        ```bash
        python main.py -o network_graph.ttl
        ```
        or
        ```bash
        python main.py --output-file network_graph.ttl
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
* **Key Properties:**
    * `rdf:type`, `rdfs:label`
    * `net:HWStatus` (ON, OFF, ABN)
    * `net:HasIFace` / `net:BelongsToNode` (Node <-> Iface)
    * `net:ConnectedToLink` / `net:hasInterface` (Iface <-> Link, simplified)
    * `net:HasNeighbor` (Node <-> Node)
    * `net:Address` (IP Address on Iface)
    * `net:Bandwidth`, `net:Technology`, `net:Cost` (Link properties)
    * `net:portMode` (ACCESS, TRUNK, UNCONFIGURED on Iface)
    * `net:vlanId`, `net:vlanName` (VLAN properties)
    * `net:accessVlan` (Iface -> VLAN relationship for access ports)
    * `net:allowedVlan` (Iface -> VLAN relationship for trunk ports)

*(Note: `net:` corresponds to the namespace `http://www.example.org/network-ontology#` and `ex:` to `http://www.example.org/network-instance#` in the script).*

## Example Output Snippet (Turtle)

```turtle
@prefix ex: [http://www.example.org/network-instance#](http://www.example.org/network-instance#) .
@prefix net: [http://www.example.org/network-ontology#](http://www.example.org/network-ontology#) .
@prefix rdf: [http://www.w3.org/1999/02/22-rdf-syntax-ns#](http://www.w3.org/1999/02/22-rdf-syntax-ns#) .
@prefix rdfs: [http://www.w3.org/2000/01/rdf-schema#](http://www.w3.org/2000/01/rdf-schema#) .

# ... Ontology Definitions (Classes, Properties) ...

ex:VLAN10 a net:VLAN ;
    rdfs:label "VLAN 10 (Users)" ;
    net:vlanId 10 ;
    net:vlanName "Users" .

ex:Switch1 a net:Switch ;
    rdfs:label "Switch1" ;
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
    net:accessVlan ex:VLAN10 ;
    net:portMode "ACCESS" .

ex:Sw1_Gi0-1 a net:Iface ;
    rdfs:label "Sw1_Gi0-1" ;
    net:HWStatus "ON" ;
    net:BelongsToNode ex:Switch1 ;
    net:ConnectedToLink ex:Link_R1_Sw1 ;
    net:allowedVlan ex:VLAN10,
        ex:VLAN20,
        ex:VLAN99 ;
    net:portMode "TRUNK" .

# ... other entities and relationships ...