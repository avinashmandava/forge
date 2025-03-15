from typing_extensions import TypedDict
from typing import List

class Node(TypedDict):
    type: str
    name: str

class Relationship(TypedDict):
    from_id: str
    to_id: str
    type: str

class ExtractedData(TypedDict):
    nodes: List[Node]
    relationships: List[Relationship]
