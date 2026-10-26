"""Validation of observed Modbus gateway conversations."""

from pathlib import Path

from pyshacl import validate
from rdflib import Graph

DATA = Path(__file__).resolve().parents[1] / "src/corona_network_standard/data"


def topology_graph() -> Graph:
    return Graph().parse(
        data="""
        @prefix net: <http://www.example.org/network-ontology#> .
        @prefix ex: <http://example.org/test/> .
        ex:client a net:ModbusTcpClient ; net:address "192.0.2.1" ;
            net:HWStatus "UNKNOWN" ; net:sentMessageCount 2 ;
            net:receivedMessageCount 0 ; net:hasNodeMessageObservation ex:client_read .
        ex:client_read a net:MessageObservation ; net:direction "sent" ;
            net:messageType "function_3_request" ; net:count 2 .
        ex:gateway a net:ModbusTcpGateway ; net:address "192.0.2.2" ;
            net:HWStatus "UNKNOWN" ; net:routesTo ex:unit .
        ex:unit a net:ModbusRtuUnit ; net:address "192.0.2.2/unit/7" ;
            net:HWStatus "UNKNOWN" .
        ex:edge a net:CommunicationEdge ; net:sourceDevice ex:client ;
            net:destinationDevice ex:unit ; net:protocol "modbus" ;
            net:messageCount 2 ; net:hasMessageObservation ex:read .
        ex:read a net:MessageObservation ; net:messageType "function_3_request" ; net:count 2 .
        """,
        format="turtle",
    )


def conforms(graph: Graph) -> bool:
    ontology = Graph().parse(DATA / "ontology/network-ontology.ttl", format="turtle")
    shapes = Graph().parse(DATA / "shapes/network-shapes.ttl", format="turtle")
    valid, _, _ = validate(graph, shacl_graph=shapes, ont_graph=ontology, inference="rdfs")
    return valid


def test_modbus_gateway_communication_conforms() -> None:
    assert conforms(topology_graph())


def test_communication_edge_requires_message_count() -> None:
    graph = topology_graph()
    from rdflib import Namespace

    net = Namespace("http://www.example.org/network-ontology#")
    ex = Namespace("http://example.org/test/")
    graph.remove((ex.edge, net.messageCount, None))
    assert not conforms(graph)


def test_device_requires_received_count() -> None:
    graph = topology_graph()
    from rdflib import Namespace

    net = Namespace("http://www.example.org/network-ontology#")
    ex = Namespace("http://example.org/test/")
    graph.remove((ex.client, net.receivedMessageCount, None))
    assert not conforms(graph)
