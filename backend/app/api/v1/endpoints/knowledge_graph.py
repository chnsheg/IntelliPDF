"""
Knowledge Graph API Endpoints
Provides graph data for visualization
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ....core.dependencies import get_db
from ....models.db import DocumentModel, ChunkModel

router = APIRouter()


@router.get("/graph-data")
async def get_graph_data(
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get knowledge graph data including nodes and edges

    Returns:
        - nodes: List of document nodes
        - edges: List of relationships between documents
        - stats: Graph statistics
    """
    # Get documents as nodes
    result = await db.execute(
        select(DocumentModel)
        .where(DocumentModel.status == "completed")
        .order_by(DocumentModel.created_at.desc())
        .limit(limit)
    )
    documents = result.scalars().all()

    nodes = []
    for doc in documents:
        # Extract title from metadata JSON or use filename
        title = None
        if doc.doc_metadata and isinstance(doc.doc_metadata, dict):
            title = doc.doc_metadata.get("title")

        nodes.append({
            "id": doc.id,
            "label": title or doc.filename,
            "type": "document",
            "size": doc.file_size,
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
        })

    # Generate edges based on similarity (mock for now)
    edges = []
    for i, doc1 in enumerate(documents):
        for j, doc2 in enumerate(documents):
            if i < j and (i + j) % 3 == 0:  # Mock similarity condition
                edges.append({
                    "id": f"e{doc1.id}-{doc2.id}",
                    "source": doc1.id,
                    "target": doc2.id,
                    "type": "similar",
                    "weight": 0.75,
                })

    # Calculate stats
    total_nodes = len(nodes)
    total_edges = len(edges)
    avg_connections = total_edges / total_nodes if total_nodes > 0 else 0

    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "avg_connections": round(avg_connections, 2),
        }
    }


@router.get("/entities")
async def get_entities(
    document_id: str,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get extracted entities from a document

    TODO: Implement entity extraction from document chunks
    """
    # Verify document exists
    result = await db.execute(
        select(DocumentModel).where(DocumentModel.id == document_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Mock entity data
    entities = [
        {"id": "e1", "label": "机器学习", "type": "concept", "frequency": 15},
        {"id": "e2", "label": "深度学习", "type": "concept", "frequency": 12},
        {"id": "e3", "label": "神经网络", "type": "concept", "frequency": 10},
    ]

    return {
        "document_id": document_id,
        "entities": entities,
        "total": len(entities)
    }


@router.get("/relationships")
async def get_relationships(
    entity_id: str,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get relationships for a specific entity

    TODO: Implement relationship extraction
    """
    relationships = [
        {"from": entity_id, "to": "e2", "type": "related_to", "strength": 0.85},
        {"from": entity_id, "to": "e3", "type": "is_part_of", "strength": 0.70},
    ]

    return {
        "entity_id": entity_id,
        "relationships": relationships,
        "total": len(relationships)
    }


@router.post("/analyze")
async def analyze_document_graph(
    document_id: str,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Trigger graph analysis for a document

    TODO: Implement actual analysis with LLM
    """
    result = await db.execute(
        select(DocumentModel).where(DocumentModel.id == document_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "document_id": document_id,
        "status": "analysis_queued",
        "message": "Graph analysis started. This may take a few minutes."
    }
