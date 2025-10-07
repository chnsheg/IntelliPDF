"""
Knowledge graph domain models.

This module defines models for knowledge graphs constructed from document content,
enabling semantic navigation and learning path recommendations.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class NodeType(str, Enum):
    """Type of knowledge node."""
    CONCEPT = "concept"
    TOPIC = "topic"
    DEFINITION = "definition"
    EXAMPLE = "example"
    CODE = "code"
    FORMULA = "formula"


class EdgeType(str, Enum):
    """Type of relationship between knowledge nodes."""
    PREREQUISITE = "prerequisite"  # A requires B
    RELATED = "related"  # A is related to B
    EXAMPLE_OF = "example_of"  # A is example of B
    PART_OF = "part_of"  # A is part of B
    EXPLAINS = "explains"  # A explains B
    CONTRASTS = "contrasts"  # A contrasts with B


class KnowledgeNode(BaseModel):
    """
    Node in the knowledge graph.

    Represents a discrete knowledge concept extracted from document chunks.
    """

    node_id: UUID = Field(
        default_factory=uuid4,
        description="Node unique identifier"
    )
    document_id: UUID = Field(
        ...,
        description="Source document ID"
    )
    chunk_ids: list[UUID] = Field(
        default_factory=list,
        description="Associated chunk IDs"
    )
    label: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Node label (concept name)"
    )
    node_type: NodeType = Field(
        ...,
        description="Type of knowledge node"
    )
    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Detailed description of the concept"
    )
    importance_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Importance score for prioritization"
    )
    difficulty_level: int = Field(
        default=1,
        ge=1,
        le=5,
        description="Difficulty level (1=basic, 5=advanced)"
    )
    keywords: list[str] = Field(
        default_factory=list,
        description="Associated keywords"
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Additional node metadata"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Creation timestamp (UTC)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "node_id": "123e4567-e89b-12d3-a456-426614174000",
                "document_id": "987fcdeb-51a2-43d7-9abc-123456789012",
                "chunk_ids": ["abc12345-1234-1234-1234-123456789abc"],
                "label": "Neural Networks",
                "node_type": "concept",
                "description": "Computational models inspired by biological neural networks",
                "importance_score": 0.9,
                "difficulty_level": 3,
                "keywords": ["deep learning", "neurons", "activation"]
            }
        }


class KnowledgeEdge(BaseModel):
    """
    Edge in the knowledge graph.

    Represents a relationship between two knowledge nodes.
    """

    edge_id: UUID = Field(
        default_factory=uuid4,
        description="Edge unique identifier"
    )
    source_node_id: UUID = Field(
        ...,
        description="Source node ID"
    )
    target_node_id: UUID = Field(
        ...,
        description="Target node ID"
    )
    edge_type: EdgeType = Field(
        ...,
        description="Type of relationship"
    )
    weight: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Edge weight (relationship strength)"
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Relationship description"
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Additional edge metadata"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Creation timestamp (UTC)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "edge_id": "234e5678-e89b-12d3-a456-426614174111",
                "source_node_id": "123e4567-e89b-12d3-a456-426614174000",
                "target_node_id": "345e6789-e89b-12d3-a456-426614174222",
                "edge_type": "prerequisite",
                "weight": 0.85,
                "description": "Understanding linear algebra is prerequisite for neural networks"
            }
        }


class KnowledgeGraph(BaseModel):
    """
    Complete knowledge graph for a document.

    Contains all nodes and edges representing the document's knowledge structure.
    """

    graph_id: UUID = Field(
        default_factory=uuid4,
        description="Graph unique identifier"
    )
    document_id: UUID = Field(
        ...,
        description="Source document ID"
    )
    nodes: list[KnowledgeNode] = Field(
        default_factory=list,
        description="All nodes in the graph"
    )
    edges: list[KnowledgeEdge] = Field(
        default_factory=list,
        description="All edges in the graph"
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Graph-level metadata"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Creation timestamp (UTC)"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update timestamp (UTC)"
    )

    @property
    def node_count(self) -> int:
        """Get total number of nodes."""
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        """Get total number of edges."""
        return len(self.edges)

    class Config:
        json_schema_extra = {
            "example": {
                "graph_id": "456e7890-e89b-12d3-a456-426614174333",
                "document_id": "987fcdeb-51a2-43d7-9abc-123456789012",
                "nodes": [],
                "edges": [],
                "metadata": {
                    "extraction_method": "llm",
                    "confidence_threshold": 0.7
                }
            }
        }


class GraphQueryRequest(BaseModel):
    """Request model for knowledge graph queries."""

    document_id: UUID = Field(
        ...,
        description="Document ID to query"
    )
    node_types: Optional[list[NodeType]] = Field(
        None,
        description="Filter by node types"
    )
    min_importance: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Minimum importance score"
    )
    max_depth: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum depth for traversal"
    )


class LearningPathRequest(BaseModel):
    """Request model for generating learning paths."""

    document_id: UUID = Field(
        ...,
        description="Document ID"
    )
    start_node_id: Optional[UUID] = Field(
        None,
        description="Starting node (if None, finds optimal start)"
    )
    target_node_id: Optional[UUID] = Field(
        None,
        description="Target node (if None, generates complete path)"
    )
    difficulty_preference: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Preferred difficulty level"
    )


class LearningPathResponse(BaseModel):
    """Response model for learning path generation."""

    path: list[UUID] = Field(
        ...,
        description="Ordered list of node IDs in learning path"
    )
    nodes: list[KnowledgeNode] = Field(
        ...,
        description="Full node details for path"
    )
    estimated_duration_minutes: int = Field(
        ...,
        description="Estimated time to complete path"
    )

    class Config:
        from_attributes = True
