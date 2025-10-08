/**
 * PDF 标注系统类型定义
 * 符合 PDF ISO 32000-2 标准和 PDF.js API
 */

// ============================================================
// 基础类型
// ============================================================

/**
 * 文本锚点 - 用于精确定位文本位置
 */
export interface TextAnchor {
  /** 选中的文本内容 */
  selectedText: string;
  /** 前文片段（50字符） */
  prefix: string;
  /** 后文片段（50字符） */
  suffix: string;
  /** 页码（从1开始） */
  pageNumber: number;
  /** 在页面文本中的起始字符位置 */
  startOffset: number;
  /** 在页面文本中的结束字符位置 */
  endOffset: number;
  /** 页面文本的 SHA-256 指纹 */
  textHash: string;
}

/**
 * PDF 四边形点（QuadPoint）
 * PDF 坐标系：原点在左下角，Y轴向上
 */
export interface QuadPoint {
  x1: number; y1: number;  // 左下角
  x2: number; y2: number;  // 右下角
  x3: number; y3: number;  // 左上角
  x4: number; y4: number;  // 右上角
}

/**
 * PDF 原生坐标
 */
export interface PDFCoordinates {
  /** 页码 */
  pageNumber: number;
  /** 四边形数组（支持跨行选择） */
  quadPoints: QuadPoint[];
  /** 旋转角度（0, 90, 180, 270） */
  rotation: number;
  /** 页面宽度（PDF点，1pt = 1/72 inch） */
  pageWidth: number;
  /** 页面高度（PDF点） */
  pageHeight: number;
}

/**
 * 矩形区域（用于图形标注）
 */
export interface Rectangle {
  x: number;
  y: number;
  width: number;
  height: number;
}

/**
 * 点坐标
 */
export interface Point {
  x: number;
  y: number;
}

/**
 * 路径（用于自由绘制）
 */
export interface Path {
  points: Point[];
  /** 压感（0-1，可选） */
  pressure?: number[];
}

// ============================================================
// 标注类型枚举
// ============================================================

/**
 * 标注类型
 */
export const AnnotationType = {
  // 文本标注
  HIGHLIGHT: 'highlight',           // 高亮
  UNDERLINE: 'underline',           // 下划线
  STRIKETHROUGH: 'strikethrough',   // 删除线
  SQUIGGLY: 'squiggly',            // 波浪线
  
  // 文字批注
  NOTE: 'note',                     // 便签（文字批注）
  TEXT: 'text',                     // 文本框
  
  // 图形标注
  SQUARE: 'square',                 // 矩形
  CIRCLE: 'circle',                 // 圆形
  POLYGON: 'polygon',               // 多边形
  LINE: 'line',                     // 直线
  ARROW: 'arrow',                   // 箭头
  
  // 自由绘制
  INK: 'ink',                       // 画笔
  
  // 图章和签名
  STAMP: 'stamp',                   // 图章
  SIGNATURE: 'signature',           // 签名
} as const;

export type AnnotationType = typeof AnnotationType[keyof typeof AnnotationType];

// ============================================================
// 样式定义
// ============================================================

/**
 * 标注样式基类
 */
export interface BaseAnnotationStyle {
  /** 标注类型 */
  type: AnnotationType;
  /** 颜色（HEX格式） */
  color: string;
  /** 透明度（0-1） */
  opacity: number;
}

/**
 * 文本标注样式
 */
export interface TextMarkupStyle extends BaseAnnotationStyle {
  type: 'highlight' | 'underline' | 'strikethrough' | 'squiggly';
}

/**
 * 图形标注样式
 */
export interface ShapeStyle extends BaseAnnotationStyle {
  type: 'square' | 'circle' | 'polygon' | 'line' | 'arrow';
  /** 边框宽度 */
  strokeWidth: number;
  /** 填充颜色（可选） */
  fillColor?: string;
  /** 填充透明度（可选） */
  fillOpacity?: number;
  /** 线条样式 */
  lineStyle?: 'solid' | 'dashed' | 'dotted';
  /** 箭头类型（仅箭头） */
  arrowType?: 'none' | 'open' | 'closed' | 'circle' | 'diamond';
}

/**
 * 画笔样式
 */
export interface InkStyle extends BaseAnnotationStyle {
  type: 'ink';
  /** 画笔宽度 */
  strokeWidth: number;
  /** 画笔类型 */
  brushType?: 'pen' | 'marker' | 'highlighter' | 'pencil';
  /** 是否平滑 */
  smoothing?: boolean;
}

/**
 * 文本框样式
 */
export interface TextBoxStyle extends BaseAnnotationStyle {
  type: 'text';
  /** 字体 */
  fontFamily: string;
  /** 字体大小 */
  fontSize: number;
  /** 字体粗细 */
  fontWeight: 'normal' | 'bold';
  /** 字体样式 */
  fontStyle: 'normal' | 'italic';
  /** 文本对齐 */
  textAlign: 'left' | 'center' | 'right';
  /** 背景颜色 */
  backgroundColor?: string;
  /** 边框颜色 */
  borderColor?: string;
  /** 边框宽度 */
  borderWidth?: number;
}

/**
 * 便签样式
 */
export interface NoteStyle extends BaseAnnotationStyle {
  type: 'note';
  /** 图标类型 */
  iconType: 'comment' | 'help' | 'note' | 'paragraph' | 'insert' | 'key';
}

/**
 * 图章样式
 */
export interface StampStyle extends BaseAnnotationStyle {
  type: 'stamp';
  /** 图章类型 */
  stampType: 'approved' | 'confidential' | 'draft' | 'final' | 'reviewed' | 'custom';
  /** 自定义图片URL（stampType为custom时使用） */
  imageUrl?: string;
}

/**
 * 签名样式
 */
export interface SignatureStyle extends BaseAnnotationStyle {
  type: 'signature';
  /** 签名图片URL */
  imageUrl: string;
}

/**
 * 所有样式类型联合
 */
export type AnnotationStyle = 
  | TextMarkupStyle 
  | ShapeStyle 
  | InkStyle 
  | TextBoxStyle 
  | NoteStyle 
  | StampStyle
  | SignatureStyle;

// ============================================================
// 标注数据结构
// ============================================================

/**
 * 标注批注内容
 */
export interface AnnotationComment {
  /** 批注文本 */
  text: string;
  /** 作者 */
  author: string;
  /** 作者ID */
  authorId: string;
  /** 创建时间 */
  createdAt: string;
  /** 更新时间 */
  updatedAt: string;
  /** 回复列表 */
  replies?: AnnotationComment[];
}

/**
 * 标注元数据
 */
export interface AnnotationMetadata {
  /** 创建时间 */
  createdAt: string;
  /** 更新时间 */
  updatedAt: string;
  /** 创建者ID */
  userId: string;
  /** 创建者名称 */
  userName: string;
  /** 是否锁定（不可编辑） */
  locked?: boolean;
  /** 标签 */
  tags?: string[];
}

/**
 * 文本标注数据
 */
export interface TextMarkupAnnotation {
  id: string;
  documentId: string;
  type: 'text-markup';
  /** 文本锚点 */
  textAnchor: TextAnchor;
  /** PDF坐标 */
  pdfCoordinates: PDFCoordinates;
  /** 样式 */
  style: TextMarkupStyle;
  /** 批注（可选） */
  comment?: AnnotationComment;
  /** 元数据 */
  metadata: AnnotationMetadata;
}

/**
 * 图形标注数据
 */
export interface ShapeAnnotation {
  id: string;
  documentId: string;
  type: 'shape';
  /** 页码 */
  pageNumber: number;
  /** 几何数据 */
  geometry: {
    /** 矩形/圆形 */
    rect?: Rectangle;
    /** 多边形/直线 */
    points?: Point[];
  };
  /** 样式 */
  style: ShapeStyle;
  /** 批注（可选） */
  comment?: AnnotationComment;
  /** 元数据 */
  metadata: AnnotationMetadata;
}

/**
 * 画笔标注数据
 */
export interface InkAnnotation {
  id: string;
  documentId: string;
  type: 'ink';
  /** 页码 */
  pageNumber: number;
  /** 路径数组 */
  paths: Path[];
  /** 样式 */
  style: InkStyle;
  /** 元数据 */
  metadata: AnnotationMetadata;
}

/**
 * 文本框标注数据
 */
export interface TextBoxAnnotation {
  id: string;
  documentId: string;
  type: 'textbox';
  /** 页码 */
  pageNumber: number;
  /** 位置 */
  rect: Rectangle;
  /** 文本内容 */
  text: string;
  /** 样式 */
  style: TextBoxStyle;
  /** 元数据 */
  metadata: AnnotationMetadata;
}

/**
 * 便签标注数据
 */
export interface NoteAnnotation {
  id: string;
  documentId: string;
  type: 'note';
  /** 页码 */
  pageNumber: number;
  /** 位置（锚点） */
  point: Point;
  /** 批注 */
  comment: AnnotationComment;
  /** 样式 */
  style: NoteStyle;
  /** 元数据 */
  metadata: AnnotationMetadata;
}

/**
 * 图章标注数据
 */
export interface StampAnnotation {
  id: string;
  documentId: string;
  type: 'stamp';
  /** 页码 */
  pageNumber: number;
  /** 位置 */
  rect: Rectangle;
  /** 样式 */
  style: StampStyle;
  /** 元数据 */
  metadata: AnnotationMetadata;
}

/**
 * 签名标注数据
 */
export interface SignatureAnnotation {
  id: string;
  documentId: string;
  type: 'signature';
  /** 页码 */
  pageNumber: number;
  /** 位置 */
  rect: Rectangle;
  /** 样式 */
  style: SignatureStyle;
  /** 元数据 */
  metadata: AnnotationMetadata;
}

/**
 * 所有标注类型联合
 */
export type Annotation = 
  | TextMarkupAnnotation 
  | ShapeAnnotation 
  | InkAnnotation 
  | TextBoxAnnotation 
  | NoteAnnotation
  | StampAnnotation
  | SignatureAnnotation;

// ============================================================
// 工具栏和编辑器状态
// ============================================================

/**
 * 工具类型
 */
export const ToolType = {
  SELECT: 'select',           // 选择工具
  HAND: 'hand',              // 手形工具（拖拽）
  
  // 文本标注工具
  HIGHLIGHT: 'highlight',
  UNDERLINE: 'underline',
  STRIKETHROUGH: 'strikethrough',
  SQUIGGLY: 'squiggly',
  
  // 批注工具
  NOTE: 'note',
  TEXT: 'text',
  
  // 图形工具
  SQUARE: 'square',
  CIRCLE: 'circle',
  POLYGON: 'polygon',
  LINE: 'line',
  ARROW: 'arrow',
  
  // 画笔工具
  INK: 'ink',
  ERASER: 'eraser',
  
  // 图章和签名
  STAMP: 'stamp',
  SIGNATURE: 'signature',
} as const;

export type ToolType = typeof ToolType[keyof typeof ToolType];

/**
 * 编辑器状态
 */
export interface EditorState {
  /** 当前工具 */
  currentTool: ToolType;
  /** 当前样式 */
  currentStyle: Partial<AnnotationStyle>;
  /** 选中的标注ID列表 */
  selectedAnnotations: string[];
  /** 是否正在绘制 */
  isDrawing: boolean;
  /** 是否正在拖拽 */
  isDragging: boolean;
  /** 剪贴板中的标注 */
  clipboard?: Annotation[];
}

// ============================================================
// 导出格式
// ============================================================

/**
 * XFDF 导出格式（XML Forms Data Format）
 */
export interface XFDFExport {
  version: string;
  annotations: Annotation[];
  document: {
    id: string;
    name: string;
    pageCount: number;
  };
}

/**
 * 标注过滤条件
 */
export interface AnnotationFilter {
  /** 标注类型 */
  types?: AnnotationType[];
  /** 作者 */
  authors?: string[];
  /** 页码范围 */
  pageRange?: { start: number; end: number };
  /** 日期范围 */
  dateRange?: { start: Date; end: Date };
  /** 标签 */
  tags?: string[];
  /** 搜索关键词 */
  searchText?: string;
}

/**
 * 标注排序方式
 */
export type AnnotationSortBy = 'createdAt' | 'updatedAt' | 'pageNumber' | 'author' | 'type';

/**
 * 排序顺序
 */
export type SortOrder = 'asc' | 'desc';
