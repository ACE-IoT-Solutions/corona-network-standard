# tests/test_models.py
import pytest
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, XSD
from pydantic import ValidationError
import pyshacl  # Added import

# Assuming models.py is in src/corona_network_standard
from src.corona_network_standard.models import (
    BaseEntity, HWNetEntity, LogicalEntity, VLAN, Subnet, AddressAssignment,
    Iface, Link, Node, Host, Router, Switch, NETWORK, EX
)
# Added import for resource loading
from src.corona_network_standard.utils import get_resource_path

# --- Fixtures ---

@pytest.fixture(scope="session")  # Load once per session
def shapes_graph() -> Graph:
    """Loads the SHACL shapes graph."""
    # Corrected package path including subdirectory
    shapes_path = get_resource_path("corona_network_standard.data.shapes", "network-shapes.ttl")
    g = Graph()
    g.parse(shapes_path, format="turtle")
    return g

@pytest.fixture(scope="session")  # Load once per session
def ontology_graph() -> Graph:
    """Loads the network ontology graph."""
    # Corrected package path including subdirectory
    ontology_path = get_resource_path("corona_network_standard.data.ontology", "network-ontology.ttl")
    g = Graph()
    g.parse(ontology_path, format="turtle")
    return g

@pytest.fixture
def empty_graph() -> Graph:
    """Provides an empty RDF graph with standard bindings."""
    g = Graph()
    g.bind("net", NETWORK)
    g.bind("ex", EX)
    g.bind("rdfs", RDFS)
    g.bind("rdf", RDF)
    g.bind("xsd", XSD)
    return g

@pytest.fixture
def subnet_1_1_1_0_24() -> Subnet:
    return Subnet(id="Subnet_1.1.1.0_24", cidr="1.1.1.0/24")

@pytest.fixture
def subnet_192_168_1_0_24() -> Subnet:
    return Subnet(id="Subnet_192.168.1.0_24", cidr="192.168.1.0/24")

@pytest.fixture
def subnet_10_0_0_0_30() -> Subnet:
    return Subnet(id="Subnet_10.0.0.0_30", cidr="10.0.0.0/30")

@pytest.fixture
def subnet_5_5_5_0_24() -> Subnet:
    return Subnet(id="Subnet_5.5.5.0_24", cidr="5.5.5.0/24")

@pytest.fixture
def subnet_1_2_3_0_24() -> Subnet:
    return Subnet(id="Subnet_1.2.3.0_24", cidr="1.2.3.0/24")

@pytest.fixture
def subnet_10_0_1_0_24() -> Subnet:
    return Subnet(id="Subnet_10.0.1.0_24", cidr="10.0.1.0/24")

@pytest.fixture
def subnet_10_0_2_0_24() -> Subnet:
    return Subnet(id="Subnet_10.0.2.0_24", cidr="10.0.2.0/24")

@pytest.fixture
def vlan10() -> VLAN:
    return VLAN(id="VLAN10_obj", vlan_id=10)

@pytest.fixture
def vlan20() -> VLAN:
    return VLAN(id="VLAN20_obj", vlan_id=20)

@pytest.fixture
def vlan30() -> VLAN:
    return VLAN(id="VLAN30_obj", vlan_id=30)

@pytest.fixture
def vlan100() -> VLAN:
    return VLAN(id="VLAN100_obj", vlan_id=100)

@pytest.fixture
def vlan5(subnet_5_5_5_0_24) -> VLAN:
    return VLAN(id="VLAN5_obj", vlan_id=5, name="Test", has_subnets=[subnet_5_5_5_0_24], description="VLAN Desc")

@pytest.fixture
def assign_1(subnet_10_0_0_0_30) -> AddressAssignment:
    return AddressAssignment(id="Assign_1", ip_value="10.0.0.1", on_subnet=subnet_10_0_0_0_30)

@pytest.fixture
def assign_test_ip(subnet_1_2_3_0_24) -> AddressAssignment:
    return AddressAssignment(id="Assign_TestIP", ip_value="1.2.3.4", on_subnet=subnet_1_2_3_0_24, description="Assign Desc")

@pytest.fixture
def assign_iface_ip(subnet_192_168_1_0_24) -> AddressAssignment:
    return AddressAssignment(id="Assign_IfaceIP", ip_value="192.168.1.10", on_subnet=subnet_192_168_1_0_24)

@pytest.fixture
def node1() -> Node:
    return Node(id="node-1")

@pytest.fixture
def link1() -> Link:
    return Link(id="link-1")

@pytest.fixture
def iface_a() -> Iface:
    return Iface(id="iface-a")

@pytest.fixture
def iface_b() -> Iface:
    return Iface(id="iface-b")

@pytest.fixture
def iface_h1() -> Iface:
    return Iface(id="iface-h1")

@pytest.fixture
def iface_r1() -> Iface:
    return Iface(id="iface-r1")

@pytest.fixture
def iface_s1a() -> Iface:
    return Iface(id="iface-s1a")

@pytest.fixture
def iface_s1b() -> Iface:
    return Iface(id="iface-s1b")

@pytest.fixture
def switch_1() -> Switch:
    return Switch(id="switch-1")

@pytest.fixture
def host_1(iface_h1, switch_1) -> Host:
    return Host(id="host-1", description="Host Desc", has_ifaces=[iface_h1], has_neighbors=[switch_1])

@pytest.fixture
def router_1(iface_r1, switch_1, subnet_10_0_1_0_24, subnet_10_0_2_0_24) -> Router:
    return Router(
        id="router-1",
        description="Router Desc",
        has_ifaces=[iface_r1],
        has_neighbors=[switch_1],
        routes_subnets=[subnet_10_0_1_0_24, subnet_10_0_2_0_24]
    )

# --- Pydantic Validation Tests ---

def test_base_entity_validation():
    """Tests basic BaseEntity validation."""
    entity = BaseEntity(id="test-id", description="A test entity.")
    assert entity.id == "test-id"
    assert entity.description == "A test entity."
    with pytest.raises(ValidationError):
        BaseEntity()  # Missing id

def test_hw_net_entity_validation():
    """Tests HWNetEntity validation."""
    entity = HWNetEntity(id="hw-id", hw_status="OFF")
    assert entity.hw_status == "OFF"
    entity_default = HWNetEntity(id="hw-id2")
    assert entity_default.hw_status == "ON"
    with pytest.raises(ValidationError):
        HWNetEntity(id="bad-hw", hw_status="INVALID")

def test_vlan_validation(subnet_1_1_1_0_24):
    """Tests VLAN validation."""
    # Use fixture for subnet
    vlan = VLAN(id="VLAN100_obj", vlan_id=100, name="TestVLAN", has_subnets=[subnet_1_1_1_0_24])
    assert vlan.vlan_id == 100
    assert vlan.name == "TestVLAN"
    assert vlan.has_subnets == [subnet_1_1_1_0_24]
    with pytest.raises(ValidationError):
        VLAN(id="bad-vlan")  # Missing vlan_id

def test_subnet_validation(subnet_192_168_1_0_24):
    """Tests Subnet validation."""
    # Use fixture
    subnet = subnet_192_168_1_0_24
    assert subnet.cidr == "192.168.1.0/24"
    assert subnet.id == "Subnet_192.168.1.0_24"
    with pytest.raises(ValidationError):
        Subnet(id="bad-subnet")  # Missing cidr

def test_address_assignment_validation(subnet_10_0_0_0_30):
    """Tests AddressAssignment validation."""
    # Use fixtures
    assign = AddressAssignment(id="Assign_1", ip_value="10.0.0.1", on_subnet=subnet_10_0_0_0_30)
    assert assign.ip_value == "10.0.0.1"
    assert assign.on_subnet == subnet_10_0_0_0_30
    with pytest.raises(ValidationError):
        AddressAssignment(id="bad-assign", ip_value="1.1.1.1")  # Missing on_subnet
    with pytest.raises(ValidationError):
        AddressAssignment(id="bad-assign", on_subnet=subnet_10_0_0_0_30)  # Missing ip_value

def test_iface_validation_modes(vlan10, vlan20, vlan30):
    """Tests Iface Pydantic validation for port modes and VLANs."""
    # Use VLAN fixtures
    # Valid ACCESS
    iface_acc = Iface(id="if-acc", port_mode="ACCESS", access_vlan=vlan10)
    assert iface_acc.port_mode == "ACCESS"
    assert iface_acc.access_vlan == vlan10

    # Valid TRUNK
    iface_trunk = Iface(id="if-trunk", port_mode="TRUNK", allowed_vlans=[vlan20, vlan30])
    assert iface_trunk.port_mode == "TRUNK"
    assert iface_trunk.allowed_vlans == [vlan20, vlan30]

    # Valid UNCONFIGURED
    iface_unconf = Iface(id="if-unconf", port_mode="UNCONFIGURED")
    assert iface_unconf.port_mode == "UNCONFIGURED"
    assert iface_unconf.access_vlan is None
    assert not iface_unconf.allowed_vlans

    # Invalid: ACCESS with allowed_vlans
    with pytest.raises(ValueError, match="allowed_vlans cannot be set when port_mode is ACCESS"):
        Iface(id="if-bad-acc", port_mode="ACCESS", access_vlan=vlan10, allowed_vlans=[vlan20])

    # Invalid: TRUNK with access_vlan
    with pytest.raises(ValueError, match="access_vlan cannot be set when port_mode is TRUNK"):
        Iface(id="if-bad-trunk", port_mode="TRUNK", allowed_vlans=[vlan20], access_vlan=vlan10)

    # Invalid: UNCONFIGURED with access_vlan
    with pytest.raises(ValueError, match="access_vlan cannot be set when port_mode is UNCONFIGURED"):
        Iface(id="if-bad-unconf-acc", port_mode="UNCONFIGURED", access_vlan=vlan10)

    # Invalid: UNCONFIGURED with allowed_vlans
    with pytest.raises(ValueError, match="allowed_vlans cannot be set when port_mode is UNCONFIGURED"):
        Iface(id="if-bad-unconf-trunk", port_mode="UNCONFIGURED", allowed_vlans=[vlan20])

# --- RDF Generation and SHACL Validation Tests ---

def validate_graph(data_graph: Graph, shapes_graph: Graph, ontology_graph: Graph):
    """Helper function to run SHACL validation."""
    conforms, results_graph, results_text = pyshacl.validate(
        data_graph,
        shacl_graph=shapes_graph,
        ont_graph=ontology_graph,
        inference='rdfs',  # Use RDFS inference based on the ontology
        abort_on_first=False,
        allow_infos=True,
        allow_warnings=True,
        meta_shacl=False,
        advanced=True,
        js=False,
        debug=False
    )
    assert conforms, f"SHACL validation failed:\n{results_text}"

def test_base_entity_rdf(empty_graph: Graph, shapes_graph: Graph, ontology_graph: Graph):
    """Tests BaseEntity RDF generation and SHACL conformance."""
    entity = BaseEntity(id="base-1", description="Base Desc")
    uri = entity.to_rdf(empty_graph)
    assert uri == EX["base-1"]
    assert (uri, RDF.type, NETWORK.BaseEntity) in empty_graph
    assert (uri, RDFS.label, Literal("base-1")) in empty_graph
    assert (uri, RDFS.comment, Literal("Base Desc")) in empty_graph
    validate_graph(empty_graph, shapes_graph, ontology_graph)

def test_hw_net_entity_rdf(empty_graph: Graph, shapes_graph: Graph, ontology_graph: Graph):
    """Tests HWNetEntity RDF generation and SHACL conformance."""
    entity = HWNetEntity(id="hw-1", description="HW Desc", hw_status="OFF")
    uri = entity.to_rdf(empty_graph)
    assert uri == EX["hw-1"]
    assert (uri, RDF.type, NETWORK.HWNetEntity) in empty_graph
    assert (uri, NETWORK.HWStatus, Literal("OFF")) in empty_graph
    validate_graph(empty_graph, shapes_graph, ontology_graph)

def test_vlan_rdf(empty_graph: Graph, shapes_graph: Graph, ontology_graph: Graph, vlan5):
    """Tests VLAN RDF generation and SHACL conformance."""
    # Use vlan5 fixture which includes the subnet
    subnet = vlan5.has_subnets[0] # Get the subnet from the fixture
    subnet_uri = subnet.to_rdf(empty_graph) # Ensure subnet is in graph and get its URI
    uri = vlan5.to_rdf(empty_graph)
    assert uri == EX["VLAN5_obj"]
    assert (uri, NETWORK.hasSubnet, subnet_uri) in empty_graph # Check link using URI
    validate_graph(empty_graph, shapes_graph, ontology_graph)

def test_subnet_rdf(empty_graph: Graph, shapes_graph: Graph, ontology_graph: Graph):
    """Tests Subnet RDF generation and SHACL conformance."""
    # Create instance directly as it's simple and specific to this test
    subnet = Subnet(id="IrrelevantID", cidr="10.1.1.0/24", description="Subnet Desc")
    uri = subnet.to_rdf(empty_graph)
    expected_uri = EX["Subnet_10.1.1.0_24"]
    assert uri == expected_uri
    assert (uri, NETWORK.subnetCidr, Literal("10.1.1.0/24", datatype=XSD.string)) in empty_graph
    validate_graph(empty_graph, shapes_graph, ontology_graph)

def test_address_assignment_rdf(empty_graph: Graph, shapes_graph: Graph, ontology_graph: Graph, assign_test_ip):
    """Tests AddressAssignment RDF generation and SHACL conformance."""
    # Use assign_test_ip fixture
    subnet = assign_test_ip.on_subnet # Get the subnet from the fixture
    subnet_uri = subnet.to_rdf(empty_graph)  # Ensure subnet is in graph and get its URI
    uri = assign_test_ip.to_rdf(empty_graph)
    assert uri == EX["Assign_TestIP"]
    assert (uri, NETWORK.onSubnet, subnet_uri) in empty_graph # Check link using URI
    validate_graph(empty_graph, shapes_graph, ontology_graph)

def test_iface_rdf(empty_graph: Graph, shapes_graph: Graph, ontology_graph: Graph, node1, link1, vlan100, assign_iface_ip):
    """Tests Iface RDF generation (ACCESS mode) and SHACL conformance."""
    # Get related objects from fixtures
    subnet = assign_iface_ip.on_subnet # Get subnet from assignment fixture

    # Serialize related objects first
    subnet_uri = subnet.to_rdf(empty_graph)
    assign_uri = assign_iface_ip.to_rdf(empty_graph)
    vlan100_uri = vlan100.to_rdf(empty_graph)
    node1_uri = node1.to_rdf(empty_graph)
    link1_uri = link1.to_rdf(empty_graph)

    # Instantiate Iface using fixtures
    iface = Iface(
        id="iface-1",
        description="Iface Desc",
        hw_status="ON",
        belongs_to_node=node1,
        connected_to_link=link1,
        port_mode="ACCESS",
        access_vlan=vlan100,
        has_address_assignments=[assign_iface_ip]
    )
    uri = iface.to_rdf(empty_graph)

    assert uri == EX["iface-1"]
    assert (uri, NETWORK.accessVlan, vlan100_uri) in empty_graph
    assert (uri, NETWORK.hasAddressAssignment, assign_uri) in empty_graph
    assert (uri, NETWORK.BelongsToNode, node1_uri) in empty_graph
    assert (uri, NETWORK.ConnectedToLink, link1_uri) in empty_graph
    assert (node1_uri, NETWORK.HasIFace, uri) in empty_graph
    assert (link1_uri, NETWORK.hasInterface, uri) in empty_graph

    validate_graph(empty_graph, shapes_graph, ontology_graph)

def test_link_rdf(empty_graph: Graph, shapes_graph: Graph, ontology_graph: Graph, iface_a, iface_b):
    """Tests Link RDF generation and SHACL conformance."""
    # Create dummy nodes for the interfaces
    node_a = Node(id="node-for-iface-a")
    node_b = Node(id="node-for-iface-b")

    # Associate interfaces with nodes
    iface_a.belongs_to_node = node_a
    iface_b.belongs_to_node = node_b

    # Serialize nodes first
    node_a_uri = node_a.to_rdf(empty_graph)
    node_b_uri = node_b.to_rdf(empty_graph)

    # Serialize interfaces (this will add BelongsToNode links)
    iface_a_uri = iface_a.to_rdf(empty_graph)
    iface_b_uri = iface_b.to_rdf(empty_graph)

    # Instantiate Link with Iface objects from fixtures
    link = Link(
        id="link-test",
        description="Link Desc",
        bandwidth=1000,
        technology="Ethernet",
        interfaces=[iface_a, iface_b]
    )
    uri = link.to_rdf(empty_graph) # Serializes link and links interfaces

    assert uri == EX["link-test"]
    assert (uri, NETWORK.hasInterface, iface_a_uri) in empty_graph
    assert (uri, NETWORK.hasInterface, iface_b_uri) in empty_graph
    assert (iface_a_uri, NETWORK.ConnectedToLink, uri) in empty_graph
    assert (iface_b_uri, NETWORK.ConnectedToLink, uri) in empty_graph
    # Check that BelongsToNode was added correctly by iface.to_rdf
    assert (iface_a_uri, NETWORK.BelongsToNode, node_a_uri) in empty_graph
    assert (iface_b_uri, NETWORK.BelongsToNode, node_b_uri) in empty_graph
    # Check inverse added by Node.to_rdf
    assert (node_a_uri, NETWORK.HasIFace, iface_a_uri) in empty_graph
    assert (node_b_uri, NETWORK.HasIFace, iface_b_uri) in empty_graph


    validate_graph(empty_graph, shapes_graph, ontology_graph)

def test_host_rdf(empty_graph: Graph, shapes_graph: Graph, ontology_graph: Graph, host_1):
    """Tests Host RDF generation and SHACL conformance."""
    # Use host_1 fixture
    iface_h1 = host_1.has_ifaces[0]
    switch_1 = host_1.has_neighbors[0]

    # Serialize related objects first (from fixture)
    iface_h1_uri = iface_h1.to_rdf(empty_graph)
    switch_1_uri = switch_1.to_rdf(empty_graph)

    # Serialize host using fixture
    uri = host_1.to_rdf(empty_graph)

    assert uri == EX["host-1"]
    assert (uri, RDF.type, NETWORK.Host) in empty_graph
    assert (uri, NETWORK.HasIFace, iface_h1_uri) in empty_graph
    assert (iface_h1_uri, NETWORK.BelongsToNode, uri) in empty_graph
    assert (uri, NETWORK.HasNeighbor, switch_1_uri) in empty_graph
    assert (switch_1_uri, NETWORK.HasNeighbor, uri) in empty_graph

    validate_graph(empty_graph, shapes_graph, ontology_graph)

def test_router_rdf(empty_graph: Graph, shapes_graph: Graph, ontology_graph: Graph, router_1):
    """Tests Router RDF generation and SHACL conformance."""
    # Use router_1 fixture
    iface_r1 = router_1.has_ifaces[0]
    switch_1 = router_1.has_neighbors[0]
    subnet1 = router_1.routes_subnets[0]
    subnet2 = router_1.routes_subnets[1]

    # Serialize related objects first (from fixture)
    iface_r1_uri = iface_r1.to_rdf(empty_graph)
    switch_1_uri = switch_1.to_rdf(empty_graph)
    subnet1_uri = subnet1.to_rdf(empty_graph)
    subnet2_uri = subnet2.to_rdf(empty_graph)

    # Serialize router using fixture
    uri = router_1.to_rdf(empty_graph)

    assert uri == EX["router-1"]
    assert (uri, RDF.type, NETWORK.Router) in empty_graph
    assert (uri, RDFS.label, Literal("router-1")) in empty_graph
    assert (uri, RDFS.comment, Literal("Router Desc")) in empty_graph
    assert (uri, NETWORK.HWStatus, Literal("ON")) in empty_graph
    assert (uri, NETWORK.HasIFace, iface_r1_uri) in empty_graph
    assert (iface_r1_uri, NETWORK.BelongsToNode, uri) in empty_graph
    assert (uri, NETWORK.HasNeighbor, switch_1_uri) in empty_graph
    assert (switch_1_uri, NETWORK.HasNeighbor, uri) in empty_graph
    assert (uri, NETWORK.routesSubnet, subnet1_uri) in empty_graph
    assert (uri, NETWORK.routesSubnet, subnet2_uri) in empty_graph

    validate_graph(empty_graph, shapes_graph, ontology_graph)

def test_switch_rdf(empty_graph: Graph, shapes_graph: Graph, ontology_graph: Graph, iface_s1a, iface_s1b, router_1, host_1):
    """Tests Switch RDF generation and SHACL conformance."""
    # Use fixtures
    # Serialize related objects first
    iface_s1a_uri = iface_s1a.to_rdf(empty_graph)
    iface_s1b_uri = iface_s1b.to_rdf(empty_graph)
    # Ensure router/host dependencies are serialized *before* router/host
    router_1.has_ifaces[0].to_rdf(empty_graph)
    router_1.has_neighbors[0].to_rdf(empty_graph)
    router_1.routes_subnets[0].to_rdf(empty_graph)
    router_1.routes_subnets[1].to_rdf(empty_graph)
    router_1_uri = router_1.to_rdf(empty_graph)
    # Ensure host dependencies are serialized *before* host
    host_1.has_ifaces[0].to_rdf(empty_graph)
    host_1.has_neighbors[0].to_rdf(empty_graph)
    host_1_uri = host_1.to_rdf(empty_graph)

    # Instantiate Switch with objects from fixtures
    switch = Switch(
        id="switch-1",
        description="Switch Desc",
        has_ifaces=[iface_s1a, iface_s1b],
        has_neighbors=[router_1, host_1]
    )
    uri = switch.to_rdf(empty_graph)

    assert uri == EX["switch-1"]
    assert (uri, RDF.type, NETWORK.Switch) in empty_graph
    assert (uri, RDFS.label, Literal("switch-1")) in empty_graph
    assert (uri, RDFS.comment, Literal("Switch Desc")) in empty_graph
    assert (uri, NETWORK.HWStatus, Literal("ON")) in empty_graph
    assert (uri, NETWORK.HasIFace, iface_s1a_uri) in empty_graph
    assert (uri, NETWORK.HasIFace, iface_s1b_uri) in empty_graph
    assert (iface_s1a_uri, NETWORK.BelongsToNode, uri) in empty_graph
    assert (iface_s1b_uri, NETWORK.BelongsToNode, uri) in empty_graph
    assert (uri, NETWORK.HasNeighbor, router_1_uri) in empty_graph
    assert (uri, NETWORK.HasNeighbor, host_1_uri) in empty_graph
    assert (router_1_uri, NETWORK.HasNeighbor, uri) in empty_graph
    assert (host_1_uri, NETWORK.HasNeighbor, uri) in empty_graph

    validate_graph(empty_graph, shapes_graph, ontology_graph)
