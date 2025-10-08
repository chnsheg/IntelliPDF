# 后端 API 实现方案

## 📅 创建时间
2025-10-08 20:30

---

## 🎯 API 设计概览

### 基础路径
```
/api/v1/documents/{document_id}/annotations
```

### 端点列表

| 方法   | 路径                       | 功能         | 状态     |
| ------ | -------------------------- | ------------ | -------- |
| POST   | `/annotations`             | 创建标注     | ⏳ 待实现 |
| GET    | `/annotations`             | 获取所有标注 | ⏳ 待实现 |
| GET    | `/annotations/{id}`        | 获取单个标注 | ⏳ 待实现 |
| PATCH  | `/annotations/{id}`        | 更新标注     | ⏳ 待实现 |
| DELETE | `/annotations/{id}`        | 删除标注     | ⏳ 待实现 |
| POST   | `/annotations/batch`       | 批量创建     | ⏳ 待实现 |
| DELETE | `/annotations/batch`       | 批量删除     | ⏳ 待实现 |
| GET    | `/annotations/export/xfdf` | 导出XFDF     | ⏳ 待实现 |
| POST   | `/annotations/import/xfdf` | 导入XFDF     | ⏳ 待实现 |

---

## 📋 数据库模型

### 文件: `backend/app/models/db/annotation_model.py`

```python
from sqlalchemy import Column, String, Integer, Float, Text, JSON, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from ..base import Base

class AnnotationModel(Base):
    """标注数据模型"""
    __tablename__ = "annotations"
    
    # 基础字段
    id = Column(String(36), primary_key=True)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, index=True)
    type = Column(String(20), nullable=False)  # text-markup, shape, ink, textbox, note, stamp, signature
    
    # 文本锚点 (仅文本标注)
    selected_text = Column(Text, nullable=True)
    prefix = Column(String(100), nullable=True)
    suffix = Column(String(100), nullable=True)
    page_number = Column(Integer, nullable=False, index=True)
    start_offset = Column(Integer, nullable=True)
    end_offset = Column(Integer, nullable=True)
    text_hash = Column(String(64), nullable=True)
    
    # PDF坐标 (JSON存储)
    quad_points = Column(JSON, nullable=True)  # Array of QuadPoint
    rotation = Column(Integer, default=0)
    page_width = Column(Float, nullable=True)
    page_height = Column(Float, nullable=True)
    
    # 几何数据 (图形、便签、画笔)
    geometry = Column(JSON, nullable=True)  # { rect, points, paths }
    
    # 样式 (JSON存储)
    style = Column(JSON, nullable=False)  # Complete style object
    
    # 批注内容 (可选)
    comment_text = Column(Text, nullable=True)
    comment_author = Column(String(100), nullable=True)
    comment_author_id = Column(String(36), nullable=True)
    
    # 元数据
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    user_id = Column(String(36), nullable=False, index=True)
    user_name = Column(String(100), nullable=False)
    locked = Column(Boolean, default=False)
    tags = Column(JSON, nullable=True)  # Array of strings
    
    # 关系
    # document = relationship("DocumentModel", back_populates="annotations")
    # replies = relationship("AnnotationReplyModel", back_populates="annotation")


class AnnotationReplyModel(Base):
    """标注回复模型"""
    __tablename__ = "annotation_replies"
    
    id = Column(String(36), primary_key=True)
    annotation_id = Column(String(36), ForeignKey("annotations.id"), nullable=False, index=True)
    
    text = Column(Text, nullable=False)
    author = Column(String(100), nullable=False)
    author_id = Column(String(36), nullable=False)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关系
    # annotation = relationship("AnnotationModel", back_populates="replies")
```

---

## 📦 Pydantic Schemas

### 文件: `backend/app/schemas/annotation.py`

```python
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

# ============================================================
# 基础类型
# ============================================================

class TextAnchor(BaseModel):
    selected_text: str
    prefix: str
    suffix: str
    page_number: int
    start_offset: int
    end_offset: int
    text_hash: str


class QuadPoint(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float
    x3: float
    y3: float
    x4: float
    y4: float


class PDFCoordinates(BaseModel):
    page_number: int
    quad_points: List[QuadPoint]
    rotation: int = 0
    page_width: float
    page_height: float


class Rectangle(BaseModel):
    x: float
    y: float
    width: float
    height: float


class Point(BaseModel):
    x: float
    y: float


class Path(BaseModel):
    points: List[Point]
    pressure: Optional[List[float]] = None


class Geometry(BaseModel):
    rect: Optional[Rectangle] = None
    points: Optional[List[Point]] = None
    paths: Optional[List[Path]] = None


# ============================================================
# 样式
# ============================================================

class AnnotationStyle(BaseModel):
    type: str
    color: str
    opacity: float
    stroke_width: Optional[float] = None
    fill_color: Optional[str] = None
    fill_opacity: Optional[float] = None
    line_style: Optional[str] = None
    arrow_type: Optional[str] = None
    font_family: Optional[str] = None
    font_size: Optional[int] = None
    font_weight: Optional[str] = None
    font_style: Optional[str] = None
    text_align: Optional[str] = None
    icon_type: Optional[str] = None
    stamp_type: Optional[str] = None
    image_url: Optional[str] = None


# ============================================================
# 批注和元数据
# ============================================================

class AnnotationComment(BaseModel):
    text: str
    author: str
    author_id: str
    created_at: str
    updated_at: str


class AnnotationMetadata(BaseModel):
    created_at: str
    updated_at: str
    user_id: str
    user_name: str
    locked: bool = False
    tags: Optional[List[str]] = None


# ============================================================
# 请求/响应模型
# ============================================================

class AnnotationCreate(BaseModel):
    """创建标注请求"""
    document_id: str
    type: str  # text-markup, shape, ink, textbox, note, stamp, signature
    
    # 文本标注字段
    text_anchor: Optional[TextAnchor] = None
    pdf_coordinates: Optional[PDFCoordinates] = None
    
    # 其他标注字段
    page_number: Optional[int] = None
    geometry: Optional[Geometry] = None
    
    # 通用字段
    style: AnnotationStyle
    comment: Optional[AnnotationComment] = None
    metadata: AnnotationMetadata


class AnnotationUpdate(BaseModel):
    """更新标注请求"""
    geometry: Optional[Geometry] = None
    style: Optional[AnnotationStyle] = None
    comment: Optional[AnnotationComment] = None
    tags: Optional[List[str]] = None
    locked: Optional[bool] = None


class AnnotationResponse(BaseModel):
    """标注响应"""
    id: str
    document_id: str
    type: str
    
    # 文本标注字段
    text_anchor: Optional[TextAnchor] = None
    pdf_coordinates: Optional[PDFCoordinates] = None
    
    # 其他标注字段
    page_number: Optional[int] = None
    geometry: Optional[Geometry] = None
    
    # 通用字段
    style: AnnotationStyle
    comment: Optional[AnnotationComment] = None
    metadata: AnnotationMetadata
    
    class Config:
        from_attributes = True


class AnnotationListResponse(BaseModel):
    """标注列表响应"""
    total: int
    annotations: List[AnnotationResponse]
    page: Optional[int] = None
    page_size: Optional[int] = None


class AnnotationFilter(BaseModel):
    """标注过滤条件"""
    types: Optional[List[str]] = None
    authors: Optional[List[str]] = None
    page_range: Optional[Dict[str, int]] = None
    date_range: Optional[Dict[str, str]] = None
    tags: Optional[List[str]] = None
    search_text: Optional[str] = None
```

---

## 🔧 Repository

### 文件: `backend/app/repositories/annotation_repository.py`

```python
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_, or_
from ..models.db.annotation_model import AnnotationModel
from ..repositories.base import BaseRepository

class AnnotationRepository(BaseRepository[AnnotationModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(AnnotationModel, session)
    
    async def get_by_document(
        self,
        document_id: str,
        page_number: Optional[int] = None
    ) -> List[AnnotationModel]:
        """获取文档的所有标注"""
        query = select(AnnotationModel).where(
            AnnotationModel.document_id == document_id
        )
        
        if page_number is not None:
            query = query.where(AnnotationModel.page_number == page_number)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_by_user(
        self,
        document_id: str,
        user_id: str
    ) -> List[AnnotationModel]:
        """获取用户的标注"""
        query = select(AnnotationModel).where(
            and_(
                AnnotationModel.document_id == document_id,
                AnnotationModel.user_id == user_id
            )
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def filter_annotations(
        self,
        document_id: str,
        filter_params: Dict[str, Any]
    ) -> List[AnnotationModel]:
        """高级过滤"""
        query = select(AnnotationModel).where(
            AnnotationModel.document_id == document_id
        )
        
        # 类型过滤
        if 'types' in filter_params and filter_params['types']:
            query = query.where(AnnotationModel.type.in_(filter_params['types']))
        
        # 作者过滤
        if 'authors' in filter_params and filter_params['authors']:
            query = query.where(AnnotationModel.user_id.in_(filter_params['authors']))
        
        # 页码范围
        if 'page_range' in filter_params and filter_params['page_range']:
            start = filter_params['page_range'].get('start', 1)
            end = filter_params['page_range'].get('end', 9999)
            query = query.where(
                and_(
                    AnnotationModel.page_number >= start,
                    AnnotationModel.page_number <= end
                )
            )
        
        # 日期范围
        if 'date_range' in filter_params and filter_params['date_range']:
            if 'start' in filter_params['date_range']:
                query = query.where(
                    AnnotationModel.created_at >= filter_params['date_range']['start']
                )
            if 'end' in filter_params['date_range']:
                query = query.where(
                    AnnotationModel.created_at <= filter_params['date_range']['end']
                )
        
        # 文本搜索
        if 'search_text' in filter_params and filter_params['search_text']:
            search = f"%{filter_params['search_text']}%"
            query = query.where(
                or_(
                    AnnotationModel.selected_text.like(search),
                    AnnotationModel.comment_text.like(search)
                )
            )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def batch_delete(
        self,
        annotation_ids: List[str]
    ) -> int:
        """批量删除"""
        query = delete(AnnotationModel).where(
            AnnotationModel.id.in_(annotation_ids)
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount
```

---

## 🚀 API 端点实现

### 文件: `backend/app/api/v1/endpoints/annotations.py`

```python
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from ....core.database import get_db
from ....schemas.annotation import (
    AnnotationCreate,
    AnnotationUpdate,
    AnnotationResponse,
    AnnotationListResponse,
    AnnotationFilter
)
from ....repositories.annotation_repository import AnnotationRepository
from ....models.db.annotation_model import AnnotationModel
import json

router = APIRouter()

# ============================================================
# 依赖注入
# ============================================================

async def get_annotation_repo(
    db: AsyncSession = Depends(get_db)
) -> AnnotationRepository:
    return AnnotationRepository(db)

# ============================================================
# 端点
# ============================================================

@router.post("/documents/{document_id}/annotations", response_model=AnnotationResponse)
async def create_annotation(
    document_id: str,
    annotation: AnnotationCreate,
    repo: AnnotationRepository = Depends(get_annotation_repo)
):
    """创建标注"""
    # 转换为数据库模型
    db_annotation = AnnotationModel(
        id=generate_uuid(),
        document_id=document_id,
        type=annotation.type,
        selected_text=annotation.text_anchor.selected_text if annotation.text_anchor else None,
        prefix=annotation.text_anchor.prefix if annotation.text_anchor else None,
        suffix=annotation.text_anchor.suffix if annotation.text_anchor else None,
        page_number=annotation.page_number or (annotation.text_anchor.page_number if annotation.text_anchor else 1),
        start_offset=annotation.text_anchor.start_offset if annotation.text_anchor else None,
        end_offset=annotation.text_anchor.end_offset if annotation.text_anchor else None,
        text_hash=annotation.text_anchor.text_hash if annotation.text_anchor else None,
        quad_points=json.dumps([qp.dict() for qp in annotation.pdf_coordinates.quad_points]) if annotation.pdf_coordinates else None,
        rotation=annotation.pdf_coordinates.rotation if annotation.pdf_coordinates else 0,
        page_width=annotation.pdf_coordinates.page_width if annotation.pdf_coordinates else None,
        page_height=annotation.pdf_coordinates.page_height if annotation.pdf_coordinates else None,
        geometry=annotation.geometry.dict() if annotation.geometry else None,
        style=annotation.style.dict(),
        comment_text=annotation.comment.text if annotation.comment else None,
        comment_author=annotation.comment.author if annotation.comment else None,
        comment_author_id=annotation.comment.author_id if annotation.comment else None,
        user_id=annotation.metadata.user_id,
        user_name=annotation.metadata.user_name,
        locked=annotation.metadata.locked,
        tags=annotation.metadata.tags
    )
    
    created = await repo.create(db_annotation)
    return AnnotationResponse.from_orm(created)


@router.get("/documents/{document_id}/annotations", response_model=AnnotationListResponse)
async def get_annotations(
    document_id: str,
    page_number: Optional[int] = Query(None),
    user_id: Optional[str] = Query(None),
    repo: AnnotationRepository = Depends(get_annotation_repo)
):
    """获取标注列表"""
    if user_id:
        annotations = await repo.get_by_user(document_id, user_id)
    else:
        annotations = await repo.get_by_document(document_id, page_number)
    
    return AnnotationListResponse(
        total=len(annotations),
        annotations=[AnnotationResponse.from_orm(a) for a in annotations]
    )


@router.get("/annotations/{annotation_id}", response_model=AnnotationResponse)
async def get_annotation(
    annotation_id: str,
    repo: AnnotationRepository = Depends(get_annotation_repo)
):
    """获取单个标注"""
    annotation = await repo.get_by_id(annotation_id)
    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")
    return AnnotationResponse.from_orm(annotation)


@router.patch("/annotations/{annotation_id}", response_model=AnnotationResponse)
async def update_annotation(
    annotation_id: str,
    update: AnnotationUpdate,
    repo: AnnotationRepository = Depends(get_annotation_repo)
):
    """更新标注"""
    annotation = await repo.get_by_id(annotation_id)
    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")
    
    # 更新字段
    if update.geometry:
        annotation.geometry = update.geometry.dict()
    if update.style:
        annotation.style = update.style.dict()
    if update.comment:
        annotation.comment_text = update.comment.text
    if update.tags is not None:
        annotation.tags = update.tags
    if update.locked is not None:
        annotation.locked = update.locked
    
    updated = await repo.update(annotation)
    return AnnotationResponse.from_orm(updated)


@router.delete("/annotations/{annotation_id}")
async def delete_annotation(
    annotation_id: str,
    repo: AnnotationRepository = Depends(get_annotation_repo)
):
    """删除标注"""
    success = await repo.delete(annotation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Annotation not found")
    return {"message": "Annotation deleted successfully"}


@router.post("/documents/{document_id}/annotations/filter", response_model=AnnotationListResponse)
async def filter_annotations(
    document_id: str,
    filter: AnnotationFilter,
    repo: AnnotationRepository = Depends(get_annotation_repo)
):
    """高级过滤"""
    annotations = await repo.filter_annotations(
        document_id,
        filter.dict(exclude_none=True)
    )
    
    return AnnotationListResponse(
        total=len(annotations),
        annotations=[AnnotationResponse.from_orm(a) for a in annotations]
    )


@router.delete("/documents/{document_id}/annotations/batch")
async def batch_delete_annotations(
    document_id: str,
    annotation_ids: List[str],
    repo: AnnotationRepository = Depends(get_annotation_repo)
):
    """批量删除"""
    count = await repo.batch_delete(annotation_ids)
    return {"message": f"Deleted {count} annotations"}


def generate_uuid() -> str:
    import uuid
    return str(uuid.uuid4())
```

---

## 📄 Alembic 迁移

### 文件: `backend/alembic/versions/xxxx_add_annotations.py`

```python
"""add annotations table

Revision ID: xxxx
Revises: yyyy
Create Date: 2025-10-08 20:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers
revision = 'xxxx'
down_revision = 'yyyy'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 创建标注表
    op.create_table(
        'annotations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('document_id', sa.String(36), sa.ForeignKey('documents.id'), nullable=False),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('selected_text', sa.Text, nullable=True),
        sa.Column('prefix', sa.String(100), nullable=True),
        sa.Column('suffix', sa.String(100), nullable=True),
        sa.Column('page_number', sa.Integer, nullable=False),
        sa.Column('start_offset', sa.Integer, nullable=True),
        sa.Column('end_offset', sa.Integer, nullable=True),
        sa.Column('text_hash', sa.String(64), nullable=True),
        sa.Column('quad_points', sa.JSON, nullable=True),
        sa.Column('rotation', sa.Integer, default=0),
        sa.Column('page_width', sa.Float, nullable=True),
        sa.Column('page_height', sa.Float, nullable=True),
        sa.Column('geometry', sa.JSON, nullable=True),
        sa.Column('style', sa.JSON, nullable=False),
        sa.Column('comment_text', sa.Text, nullable=True),
        sa.Column('comment_author', sa.String(100), nullable=True),
        sa.Column('comment_author_id', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('user_name', sa.String(100), nullable=False),
        sa.Column('locked', sa.Boolean, default=False),
        sa.Column('tags', sa.JSON, nullable=True),
    )
    
    # 创建索引
    op.create_index('ix_annotations_document_id', 'annotations', ['document_id'])
    op.create_index('ix_annotations_page_number', 'annotations', ['page_number'])
    op.create_index('ix_annotations_user_id', 'annotations', ['user_id'])
    op.create_index('ix_annotations_created_at', 'annotations', ['created_at'])


def downgrade() -> None:
    op.drop_table('annotations')
```

---

## ✅ 下一步

1. **创建数据库模型文件**
2. **运行Alembic迁移**
3. **实现API端点**
4. **前端集成API调用**
5. **测试完整流程**

预计时间: 2-3小时
预计代码: +800行

---

**后端API设计**: 完成 ✅  
**实现状态**: 待编码 ⏳  
**优先级**: 高 🔥
