/**
 * Shape Drawing Tool Component
 * 
 * Provides interactive shape drawing tools:
 * - Rectangle
 * - Circle/Ellipse
 * - Line
 * - Arrow
 * - Polygon
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import type { Point, Rectangle } from '../../types/annotation';

type ShapeType = 'rectangle' | 'circle' | 'polygon' | 'line' | 'arrow';

interface ShapeToolProps {
    pageNumber: number;
    pdfPage: any;  // PDFPageProxy
    scale: number;
    currentTool: ShapeType;
    onShapeComplete: (shape: {
        type: 'shape';
        pageNumber: number;
        geometry: { rect?: Rectangle; points?: Point[] };
    }) => void;
    onCancel: () => void;
}

export const ShapeTool: React.FC<ShapeToolProps> = ({
    pageNumber,
    pdfPage,
    scale,
    currentTool,
    onShapeComplete,
    onCancel,
}) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [isDrawing, setIsDrawing] = useState(false);
    const [startPoint, setStartPoint] = useState<Point | null>(null);
    const [currentPoint, setCurrentPoint] = useState<Point | null>(null);
    const [polygonPoints, setPolygonPoints] = useState<Point[]>([]);

    // Get viewport for coordinate conversion
    const viewport = pdfPage.getViewport({ scale });

    /**
     * Convert screen coordinates to PDF coordinates
     */
    const screenToPDF = useCallback((screenX: number, screenY: number): Point => {
        const [pdfX, pdfY] = viewport.convertToPdfPoint(screenX, screenY);
        return { x: pdfX, y: pdfY };
    }, [viewport]);

    /**
     * Convert PDF coordinates to screen coordinates
     */
    const pdfToScreen = useCallback((pdfX: number, pdfY: number): Point => {
        const [screenX, screenY] = viewport.convertToViewportPoint(pdfX, pdfY);
        return { x: screenX, y: screenY };
    }, [viewport]);

    /**
     * Handle mouse down - start drawing
     */
    const handleMouseDown = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const point = screenToPDF(x, y);

        if (currentTool === 'polygon') {
            // Polygon: accumulate points
            setPolygonPoints(prev => [...prev, point]);
        } else {
            // Other shapes: start drawing
            setStartPoint(point);
            setCurrentPoint(point);
            setIsDrawing(true);
        }
    }, [currentTool, screenToPDF]);

    /**
     * Handle mouse move - update current position
     */
    const handleMouseMove = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
        if (!isDrawing && currentTool !== 'polygon') return;

        const canvas = canvasRef.current;
        if (!canvas) return;

        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const point = screenToPDF(x, y);

        setCurrentPoint(point);
    }, [isDrawing, currentTool, screenToPDF]);

    /**
     * Handle mouse up - finish drawing
     */
    const handleMouseUp = useCallback(() => {
        if (!isDrawing || !startPoint || !currentPoint) return;

        // Calculate geometry based on shape type
        let geometry: { rect?: Rectangle; points?: Point[] } = {};

        if (currentTool === 'rectangle' || currentTool === 'circle') {
            geometry.rect = {
                x: Math.min(startPoint.x, currentPoint.x),
                y: Math.min(startPoint.y, currentPoint.y),
                width: Math.abs(currentPoint.x - startPoint.x),
                height: Math.abs(currentPoint.y - startPoint.y),
            };
        } else if (currentTool === 'line' || currentTool === 'arrow') {
            geometry.points = [startPoint, currentPoint];
        }

        onShapeComplete({
            type: 'shape',
            pageNumber,
            geometry,
        });

        // Reset state
        setIsDrawing(false);
        setStartPoint(null);
        setCurrentPoint(null);
    }, [isDrawing, startPoint, currentPoint, currentTool, pageNumber, onShapeComplete]);

    /**
     * Handle double-click for polygon - complete polygon
     */
    const handleDoubleClick = useCallback(() => {
        if (currentTool === 'polygon' && polygonPoints.length >= 3) {
            onShapeComplete({
                type: 'shape',
                pageNumber,
                geometry: {
                    points: polygonPoints,
                },
            });
            setPolygonPoints([]);
        }
    }, [currentTool, polygonPoints, pageNumber, onShapeComplete]);

    /**
     * Handle Escape key - cancel drawing
     */
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'Escape') {
                setIsDrawing(false);
                setStartPoint(null);
                setCurrentPoint(null);
                setPolygonPoints([]);
                onCancel();
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [onCancel]);

    /**
     * Render preview on canvas
     */
    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Set drawing style
        ctx.strokeStyle = '#2196F3';
        ctx.lineWidth = 2;
        ctx.setLineDash([5, 5]);

        // Draw preview
        if (isDrawing && startPoint && currentPoint) {
            const start = pdfToScreen(startPoint.x, startPoint.y);
            const current = pdfToScreen(currentPoint.x, currentPoint.y);

            ctx.beginPath();

            switch (currentTool) {
                case 'rectangle':
                    ctx.rect(
                        start.x,
                        start.y,
                        current.x - start.x,
                        current.y - start.y
                    );
                    break;

                case 'circle':
                    const radiusX = Math.abs(current.x - start.x) / 2;
                    const radiusY = Math.abs(current.y - start.y) / 2;
                    const centerX = (start.x + current.x) / 2;
                    const centerY = (start.y + current.y) / 2;
                    ctx.ellipse(centerX, centerY, radiusX, radiusY, 0, 0, 2 * Math.PI);
                    break;

                case 'line':
                case 'arrow':
                    ctx.moveTo(start.x, start.y);
                    ctx.lineTo(current.x, current.y);

                    // Draw arrow head for arrow tool
                    if (currentTool === 'arrow') {
                        const angle = Math.atan2(current.y - start.y, current.x - start.x);
                        const headLength = 15;
                        ctx.lineTo(
                            current.x - headLength * Math.cos(angle - Math.PI / 6),
                            current.y - headLength * Math.sin(angle - Math.PI / 6)
                        );
                        ctx.moveTo(current.x, current.y);
                        ctx.lineTo(
                            current.x - headLength * Math.cos(angle + Math.PI / 6),
                            current.y - headLength * Math.sin(angle + Math.PI / 6)
                        );
                    }
                    break;
            }

            ctx.stroke();
        }

        // Draw polygon preview
        if (currentTool === 'polygon' && polygonPoints.length > 0) {
            ctx.beginPath();
            polygonPoints.forEach((point, index) => {
                const screen = pdfToScreen(point.x, point.y);
                if (index === 0) {
                    ctx.moveTo(screen.x, screen.y);
                } else {
                    ctx.lineTo(screen.x, screen.y);
                }

                // Draw point markers
                ctx.fillStyle = '#2196F3';
                ctx.fillRect(screen.x - 3, screen.y - 3, 6, 6);
            });

            // Draw line to current cursor
            if (currentPoint) {
                const current = pdfToScreen(currentPoint.x, currentPoint.y);
                ctx.lineTo(current.x, current.y);
            }

            ctx.stroke();
        }
    }, [isDrawing, startPoint, currentPoint, polygonPoints, currentTool, pdfToScreen]);

    // Set canvas size to match page
    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        canvas.width = viewport.width;
        canvas.height = viewport.height;
    }, [viewport]);

    return (
        <canvas
            ref={canvasRef}
            className="absolute inset-0 cursor-crosshair"
            style={{ pointerEvents: 'auto', zIndex: 50 }}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onDoubleClick={handleDoubleClick}
        />
    );
};
