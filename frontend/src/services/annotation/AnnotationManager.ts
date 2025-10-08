/**
 * 标注管理器
 * 统一管理所有标注的创建、编辑、删除
 */

import type { PDFPageProxy } from 'pdfjs-dist';
import type { 
  Annotation, 
  TextMarkupAnnotation,
  AnnotationStyle,
  EditorState,
  ToolType
} from '../../types/annotation';
import { textAnchorService } from './textAnchor';
import { pdfCoordinateService } from './pdfCoordinates';
import { generateUUID } from '../../utils/annotation';

export class AnnotationManager {
  private annotations: Annotation[] = [];
  private editorState: EditorState = {
    currentTool: 'select' as ToolType,
    currentStyle: {
      type: 'highlight',
      color: '#FAEB96',
      opacity: 0.45
    },
    selectedAnnotations: [],
    isDrawing: false,
    isDragging: false
  };
  
  private listeners: Map<string, Set<Function>> = new Map();
  
  constructor() {
    this.initializeDefaultStyles();
  }
  
  /**
   * 初始化默认样式
   */
  private initializeDefaultStyles() {
    // 可以从localStorage加载用户偏好设置
  }
  
  /**
   * 创建文本标注（高亮、下划线等）
   */
  async createTextMarkupAnnotation(
    selection: Selection,
    pageNumber: number,
    pdfPage: PDFPageProxy,
    documentId: string,
    userId: string,
    userName: string
  ): Promise<TextMarkupAnnotation> {
    // 1. 创建文本锚点
    const textAnchor = await textAnchorService.createTextAnchor(
      selection,
      pageNumber,
      pdfPage
    );
    
    // 2. 创建 PDF 坐标
    const pdfCoordinates = await pdfCoordinateService.createPDFCoordinates(
      selection,
      pageNumber,
      pdfPage
    );
    
    // 3. 构建标注数据
    const annotation: TextMarkupAnnotation = {
      id: generateUUID(),
      documentId,
      type: 'text-markup',
      textAnchor,
      pdfCoordinates,
      style: {
        type: this.editorState.currentStyle.type as 'highlight' | 'underline' | 'strikethrough' | 'squiggly',
        color: this.editorState.currentStyle.color || '#FAEB96',
        opacity: this.editorState.currentStyle.opacity || 0.45
      },
      metadata: {
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        userId,
        userName
      }
    };
    
    // 4. 添加到列表
    this.annotations.push(annotation);
    
    // 5. 触发事件
    this.emit('annotationCreated', annotation);
    this.emit('annotationsChanged', this.annotations);
    
    return annotation;
  }
  
  /**
   * 删除标注
   */
  deleteAnnotation(annotationId: string): boolean {
    const index = this.annotations.findIndex(a => a.id === annotationId);
    if (index === -1) return false;
    
    const deleted = this.annotations.splice(index, 1)[0];
    
    this.emit('annotationDeleted', deleted);
    this.emit('annotationsChanged', this.annotations);
    
    return true;
  }
  
  /**
   * 更新标注
   */
  updateAnnotation(annotationId: string, updates: Partial<Annotation>): boolean {
    const annotation = this.annotations.find(a => a.id === annotationId);
    if (!annotation) return false;
    
    Object.assign(annotation, updates);
    annotation.metadata.updatedAt = new Date().toISOString();
    
    this.emit('annotationUpdated', annotation);
    this.emit('annotationsChanged', this.annotations);
    
    return true;
  }
  
  /**
   * 获取所有标注
   */
  getAnnotations(): Annotation[] {
    return [...this.annotations];
  }
  
  /**
   * 获取指定页面的标注
   */
  getAnnotationsByPage(pageNumber: number): Annotation[] {
    return this.annotations.filter(a => {
      if (a.type === 'text-markup') {
        return a.pdfCoordinates.pageNumber === pageNumber;
      }
      return a.pageNumber === pageNumber;
    });
  }
  
  /**
   * 设置标注列表（从后端加载）
   */
  setAnnotations(annotations: Annotation[]) {
    this.annotations = annotations;
    this.emit('annotationsChanged', this.annotations);
  }
  
  /**
   * 选中标注
   */
  selectAnnotation(annotationId: string, append: boolean = false) {
    if (append) {
      if (!this.editorState.selectedAnnotations.includes(annotationId)) {
        this.editorState.selectedAnnotations.push(annotationId);
      }
    } else {
      this.editorState.selectedAnnotations = [annotationId];
    }
    
    this.emit('selectionChanged', this.editorState.selectedAnnotations);
  }
  
  /**
   * 取消选中
   */
  deselectAnnotation(annotationId?: string) {
    if (annotationId) {
      this.editorState.selectedAnnotations = this.editorState.selectedAnnotations.filter(
        id => id !== annotationId
      );
    } else {
      this.editorState.selectedAnnotations = [];
    }
    
    this.emit('selectionChanged', this.editorState.selectedAnnotations);
  }
  
  /**
   * 获取选中的标注
   */
  getSelectedAnnotations(): Annotation[] {
    return this.annotations.filter(a => 
      this.editorState.selectedAnnotations.includes(a.id)
    );
  }
  
  /**
   * 设置当前工具
   */
  setCurrentTool(tool: ToolType) {
    this.editorState.currentTool = tool;
    this.emit('toolChanged', tool);
  }
  
  /**
   * 获取当前工具
   */
  getCurrentTool(): ToolType {
    return this.editorState.currentTool;
  }
  
  /**
   * 设置当前样式
   */
  setCurrentStyle(style: Partial<AnnotationStyle>) {
    this.editorState.currentStyle = {
      ...this.editorState.currentStyle,
      ...style
    };
    this.emit('styleChanged', this.editorState.currentStyle);
  }
  
  /**
   * 获取当前样式
   */
  getCurrentStyle(): Partial<AnnotationStyle> {
    return { ...this.editorState.currentStyle };
  }
  
  /**
   * 获取编辑器状态
   */
  getEditorState(): EditorState {
    return { ...this.editorState };
  }
  
  /**
   * 删除选中的标注
   */
  deleteSelectedAnnotations() {
    const ids = [...this.editorState.selectedAnnotations];
    ids.forEach(id => this.deleteAnnotation(id));
    this.editorState.selectedAnnotations = [];
  }
  
  /**
   * 复制选中的标注
   */
  copySelectedAnnotations() {
    const selected = this.getSelectedAnnotations();
    this.editorState.clipboard = selected.map(a => ({ ...a }));
    this.emit('annotationsCopied', this.editorState.clipboard);
  }
  
  /**
   * 粘贴标注
   */
  pasteAnnotations(pageNumber: number) {
    if (!this.editorState.clipboard || this.editorState.clipboard.length === 0) {
      return;
    }
    
    const pasted: Annotation[] = [];
    
    this.editorState.clipboard.forEach(annotation => {
      const newAnnotation = {
        ...annotation,
        id: generateUUID(),
        metadata: {
          ...annotation.metadata,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString()
        }
      };
      
      // 更新页码
      if (newAnnotation.type === 'text-markup') {
        newAnnotation.pdfCoordinates.pageNumber = pageNumber;
        newAnnotation.textAnchor.pageNumber = pageNumber;
      } else {
        newAnnotation.pageNumber = pageNumber;
      }
      
      this.annotations.push(newAnnotation);
      pasted.push(newAnnotation);
    });
    
    this.emit('annotationsPasted', pasted);
    this.emit('annotationsChanged', this.annotations);
  }
  
  /**
   * 清空所有标注
   */
  clearAnnotations() {
    this.annotations = [];
    this.editorState.selectedAnnotations = [];
    this.emit('annotationsChanged', this.annotations);
  }
  
  /**
   * 事件监听
   */
  on(event: string, callback: Function) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);
  }
  
  /**
   * 取消事件监听
   */
  off(event: string, callback: Function) {
    if (this.listeners.has(event)) {
      this.listeners.get(event)!.delete(callback);
    }
  }
  
  /**
   * 触发事件
   */
  private emit(event: string, data?: any) {
    if (this.listeners.has(event)) {
      this.listeners.get(event)!.forEach(callback => callback(data));
    }
  }
  
  /**
   * 销毁管理器
   */
  destroy() {
    this.annotations = [];
    this.listeners.clear();
  }
}

// 导出单例
export const annotationManager = new AnnotationManager();
