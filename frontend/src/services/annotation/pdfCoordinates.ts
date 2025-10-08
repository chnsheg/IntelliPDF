/**
 * PDF 坐标服务
 * 处理 PDF 原生坐标系统和屏幕坐标的转换
 */

import type { PDFPageProxy, PageViewport } from 'pdfjs-dist';
import type { QuadPoint, PDFCoordinates, Rectangle, Point } from '../../types/annotation';

export class PDFCoordinateService {
  /**
   * 从用户选择创建 QuadPoints
   * 支持跨行选择，返回多个四边形
   */
  async getQuadPointsFromSelection(
    selection: Selection,
    pageNumber: number,
    pdfPage: PDFPageProxy
  ): Promise<QuadPoint[]> {
    const range = selection.getRangeAt(0);
    const clientRects = Array.from(range.getClientRects());
    
    if (clientRects.length === 0) {
      throw new Error('No client rects found for selection');
    }
    
    // 获取页面元素
    const pageElement = document.querySelector(
      `[data-page-number="${pageNumber}"]`
    );
    if (!pageElement) {
      throw new Error(`Page element not found: ${pageNumber}`);
    }
    
    const pageRect = pageElement.getBoundingClientRect();
    
    // 获取 PDF 视口（使用 scale=1.0 获取原始坐标）
    const viewport = pdfPage.getViewport({ scale: 1.0 });
    
    // 转换每个 ClientRect 到 QuadPoint
    const quadPoints: QuadPoint[] = [];
    
    for (const rect of clientRects) {
      const quad = this.clientRectToQuadPoint(rect, pageRect, viewport);
      quadPoints.push(quad);
    }
    
    return quadPoints;
  }
  
  /**
   * 将 ClientRect 转换为 QuadPoint（PDF坐标）
   */
  private clientRectToQuadPoint(
    rect: DOMRect,
    pageRect: DOMRect,
    viewport: PageViewport
  ): QuadPoint {
    // 计算相对于页面的坐标
    const relX1 = rect.left - pageRect.left;
    const relY1 = rect.top - pageRect.top;
    const relX2 = rect.right - pageRect.left;
    const relY2 = rect.bottom - pageRect.top;
    
    // 转换为 PDF 坐标（原点在左下角）
    const [pdfX1, pdfY1] = viewport.convertToPdfPoint(relX1, relY1);
    const [pdfX2, pdfY2] = viewport.convertToPdfPoint(relX2, relY2);
    const [pdfX3, pdfY3] = viewport.convertToPdfPoint(relX1, relY2);
    const [pdfX4, pdfY4] = viewport.convertToPdfPoint(relX2, relY1);
    
    return {
      x1: pdfX1, y1: pdfY1,  // 左下
      x2: pdfX2, y2: pdfY2,  // 右下
      x3: pdfX3, y3: pdfY3,  // 左上
      x4: pdfX4, y4: pdfY4   // 右上
    };
  }
  
  /**
   * 创建完整的 PDF 坐标数据
   */
  async createPDFCoordinates(
    selection: Selection,
    pageNumber: number,
    pdfPage: PDFPageProxy
  ): Promise<PDFCoordinates> {
    const quadPoints = await this.getQuadPointsFromSelection(
      selection,
      pageNumber,
      pdfPage
    );
    
    const viewport = pdfPage.getViewport({ scale: 1.0 });
    
    return {
      pageNumber,
      quadPoints,
      rotation: pdfPage.rotate || 0,
      pageWidth: viewport.width,
      pageHeight: viewport.height
    };
  }
  
  /**
   * 将 QuadPoint 转换为屏幕坐标
   */
  quadPointToScreen(
    quad: QuadPoint,
    viewport: PageViewport
  ): {
    x: number;
    y: number;
    width: number;
    height: number;
    points: [number, number][];
  } {
    // 转换四个顶点
    const [x1, y1] = viewport.convertToViewportPoint(quad.x1, quad.y1);
    const [x2, y2] = viewport.convertToViewportPoint(quad.x2, quad.y2);
    const [x3, y3] = viewport.convertToViewportPoint(quad.x3, quad.y3);
    const [x4, y4] = viewport.convertToViewportPoint(quad.x4, quad.y4);
    
    // 计算边界框
    const minX = Math.min(x1, x2, x3, x4);
    const maxX = Math.max(x1, x2, x3, x4);
    const minY = Math.min(y1, y2, y3, y4);
    const maxY = Math.max(y1, y2, y3, y4);
    
    return {
      x: minX,
      y: minY,
      width: maxX - minX,
      height: maxY - minY,
      points: [[x1, y1], [x2, y2], [x4, y4], [x3, y3]]  // 绘制顺序
    };
  }
  
  /**
   * 将矩形转换为 PDF 坐标
   */
  rectangleToPDF(
    rect: Rectangle,
    pageElement: HTMLElement,
    viewport: PageViewport
  ): Rectangle {
    const pageRect = pageElement.getBoundingClientRect();
    
    // 相对坐标
    const relX = rect.x - pageRect.left;
    const relY = rect.y - pageRect.top;
    
    // 转换为 PDF 坐标
    const [pdfX, pdfY] = viewport.convertToPdfPoint(relX, relY);
    const [pdfX2, pdfY2] = viewport.convertToPdfPoint(
      relX + rect.width,
      relY + rect.height
    );
    
    return {
      x: Math.min(pdfX, pdfX2),
      y: Math.min(pdfY, pdfY2),
      width: Math.abs(pdfX2 - pdfX),
      height: Math.abs(pdfY2 - pdfY)
    };
  }
  
  /**
   * 将 PDF 矩形转换为屏幕坐标
   */
  rectangleToScreen(
    rect: Rectangle,
    viewport: PageViewport
  ): Rectangle {
    const [x1, y1] = viewport.convertToViewportPoint(rect.x, rect.y);
    const [x2, y2] = viewport.convertToViewportPoint(
      rect.x + rect.width,
      rect.y + rect.height
    );
    
    return {
      x: Math.min(x1, x2),
      y: Math.min(y1, y2),
      width: Math.abs(x2 - x1),
      height: Math.abs(y2 - y1)
    };
  }
  
  /**
   * 将点转换为 PDF 坐标
   */
  pointToPDF(
    point: Point,
    pageElement: HTMLElement,
    viewport: PageViewport
  ): Point {
    const pageRect = pageElement.getBoundingClientRect();
    
    const relX = point.x - pageRect.left;
    const relY = point.y - pageRect.top;
    
    const [pdfX, pdfY] = viewport.convertToPdfPoint(relX, relY);
    
    return { x: pdfX, y: pdfY };
  }
  
  /**
   * 将 PDF 点转换为屏幕坐标
   */
  pointToScreen(
    point: Point,
    viewport: PageViewport
  ): Point {
    const [x, y] = viewport.convertToViewportPoint(point.x, point.y);
    return { x, y };
  }
  
  /**
   * 将路径转换为 PDF 坐标
   */
  pathToPDF(
    points: Point[],
    pageElement: HTMLElement,
    viewport: PageViewport
  ): Point[] {
    return points.map(point => this.pointToPDF(point, pageElement, viewport));
  }
  
  /**
   * 将 PDF 路径转换为屏幕坐标
   */
  pathToScreen(
    points: Point[],
    viewport: PageViewport
  ): Point[] {
    return points.map(point => this.pointToScreen(point, viewport));
  }
  
  /**
   * 获取页面元素
   */
  getPageElement(pageNumber: number): HTMLElement | null {
    return document.querySelector(`[data-page-number="${pageNumber}"]`);
  }
  
  /**
   * 判断点是否在 QuadPoint 内
   */
  isPointInQuadPoint(
    point: Point,
    quad: QuadPoint,
    viewport: PageViewport
  ): boolean {
    const screenCoords = this.quadPointToScreen(quad, viewport);
    
    // 简化：使用边界框判断
    return (
      point.x >= screenCoords.x &&
      point.x <= screenCoords.x + screenCoords.width &&
      point.y >= screenCoords.y &&
      point.y <= screenCoords.y + screenCoords.height
    );
  }
  
  /**
   * 获取 QuadPoints 的边界框
   */
  getQuadPointsBoundingBox(
    quadPoints: QuadPoint[],
    viewport: PageViewport
  ): Rectangle {
    if (quadPoints.length === 0) {
      return { x: 0, y: 0, width: 0, height: 0 };
    }
    
    const screenRects = quadPoints.map(quad => 
      this.quadPointToScreen(quad, viewport)
    );
    
    const minX = Math.min(...screenRects.map(r => r.x));
    const minY = Math.min(...screenRects.map(r => r.y));
    const maxX = Math.max(...screenRects.map(r => r.x + r.width));
    const maxY = Math.max(...screenRects.map(r => r.y + r.height));
    
    return {
      x: minX,
      y: minY,
      width: maxX - minX,
      height: maxY - minY
    };
  }
}

// 单例导出
export const pdfCoordinateService = new PDFCoordinateService();
