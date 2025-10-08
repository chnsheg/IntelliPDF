/**
 * 工具函数库
 */

// ============================================================
// 颜色转换
// ============================================================

/**
 * HEX 转 RGBA
 */
export function hexToRgba(hex: string, opacity: number): string {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${opacity})`;
}

/**
 * RGB 转 HEX
 */
export function rgbToHex(r: number, g: number, b: number): string {
    return '#' + [r, g, b].map(x => {
        const hex = x.toString(16);
        return hex.length === 1 ? '0' + hex : hex;
    }).join('');
}

// ============================================================
// 加密和哈希
// ============================================================

/**
 * 计算 SHA-256 哈希
 */
export async function sha256(text: string): Promise<string> {
    const encoder = new TextEncoder();
    const data = encoder.encode(text);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    return hashHex;
}

// ============================================================
// UUID 生成
// ============================================================

/**
 * 生成 UUID v4
 */
export function generateUUID(): string {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// ============================================================
// 几何计算
// ============================================================

/**
 * 计算两点之间的距离
 */
export function distance(x1: number, y1: number, x2: number, y2: number): number {
    return Math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2);
}

/**
 * 判断点是否在矩形内
 */
export function isPointInRect(
    px: number,
    py: number,
    rx: number,
    ry: number,
    rw: number,
    rh: number
): boolean {
    return px >= rx && px <= rx + rw && py >= ry && py <= ry + rh;
}

/**
 * 判断点是否在圆内
 */
export function isPointInCircle(
    px: number,
    py: number,
    cx: number,
    cy: number,
    radius: number
): boolean {
    return distance(px, py, cx, cy) <= radius;
}

/**
 * 计算矩形的边界框
 */
export function getBoundingBox(points: { x: number; y: number }[]): {
    x: number;
    y: number;
    width: number;
    height: number;
} {
    if (points.length === 0) {
        return { x: 0, y: 0, width: 0, height: 0 };
    }

    const xs = points.map(p => p.x);
    const ys = points.map(p => p.y);

    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    const minY = Math.min(...ys);
    const maxY = Math.max(...ys);

    return {
        x: minX,
        y: minY,
        width: maxX - minX,
        height: maxY - minY
    };
}

// ============================================================
// 路径平滑（Catmull-Rom Spline）
// ============================================================

/**
 * Catmull-Rom 样条曲线平滑
 */
export function smoothPath(
    points: { x: number; y: number }[],
    tension: number = 0.5
): { x: number; y: number }[] {
    if (points.length < 3) return points;

    const smoothed: { x: number; y: number }[] = [points[0]];

    for (let i = 0; i < points.length - 1; i++) {
        const p0 = points[Math.max(0, i - 1)];
        const p1 = points[i];
        const p2 = points[i + 1];
        const p3 = points[Math.min(points.length - 1, i + 2)];

        const segments = 10; // 每段插值点数
        for (let t = 0; t < segments; t++) {
            const tNorm = t / segments;
            const point = catmullRomInterpolate(p0, p1, p2, p3, tNorm, tension);
            smoothed.push(point);
        }
    }

    smoothed.push(points[points.length - 1]);
    return smoothed;
}

/**
 * Catmull-Rom 插值
 */
function catmullRomInterpolate(
    p0: { x: number; y: number },
    p1: { x: number; y: number },
    p2: { x: number; y: number },
    p3: { x: number; y: number },
    t: number,
    tension: number
): { x: number; y: number } {
    const t2 = t * t;
    const t3 = t2 * t;

    const v0 = (p2.x - p0.x) * tension;
    const v1 = (p3.x - p1.x) * tension;
    const w0 = (p2.y - p0.y) * tension;
    const w1 = (p3.y - p1.y) * tension;

    const x = (2 * p1.x - 2 * p2.x + v0 + v1) * t3 +
        (-3 * p1.x + 3 * p2.x - 2 * v0 - v1) * t2 +
        v0 * t + p1.x;

    const y = (2 * p1.y - 2 * p2.y + w0 + w1) * t3 +
        (-3 * p1.y + 3 * p2.y - 2 * w0 - w1) * t2 +
        w0 * t + p1.y;

    return { x, y };
}

// ============================================================
// 字符串相似度计算
// ============================================================

/**
 * 计算 Levenshtein 距离
 */
export function levenshteinDistance(str1: string, str2: string): number {
    const m = str1.length;
    const n = str2.length;
    const dp: number[][] = Array(m + 1).fill(null).map(() => Array(n + 1).fill(0));

    for (let i = 0; i <= m; i++) dp[i][0] = i;
    for (let j = 0; j <= n; j++) dp[0][j] = j;

    for (let i = 1; i <= m; i++) {
        for (let j = 1; j <= n; j++) {
            if (str1[i - 1] === str2[j - 1]) {
                dp[i][j] = dp[i - 1][j - 1];
            } else {
                dp[i][j] = Math.min(
                    dp[i - 1][j] + 1,      // 删除
                    dp[i][j - 1] + 1,      // 插入
                    dp[i - 1][j - 1] + 1   // 替换
                );
            }
        }
    }

    return dp[m][n];
}

/**
 * 计算字符串相似度（0-1）
 */
export function stringSimilarity(str1: string, str2: string): number {
    const maxLen = Math.max(str1.length, str2.length);
    if (maxLen === 0) return 1.0;

    const dist = levenshteinDistance(str1, str2);
    return 1.0 - dist / maxLen;
}

/**
 * Dice 系数（Bigram 相似度）
 */
export function diceCoefficient(str1: string, str2: string): number {
    const bigrams1 = getBigrams(str1);
    const bigrams2 = getBigrams(str2);

    if (bigrams1.length === 0 && bigrams2.length === 0) return 1.0;
    if (bigrams1.length === 0 || bigrams2.length === 0) return 0.0;

    const intersection = bigrams1.filter(b => bigrams2.includes(b)).length;
    return (2 * intersection) / (bigrams1.length + bigrams2.length);
}

/**
 * 获取字符串的 Bigrams
 */
function getBigrams(str: string): string[] {
    const bigrams: string[] = [];
    for (let i = 0; i < str.length - 1; i++) {
        bigrams.push(str.substring(i, i + 2));
    }
    return bigrams;
}

// ============================================================
// 正则表达式转义
// ============================================================

/**
 * 转义正则表达式特殊字符
 */
export function escapeRegex(str: string): string {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// ============================================================
// 日期格式化
// ============================================================

/**
 * 格式化日期为 ISO 字符串
 */
export function formatDate(date: Date): string {
    return date.toISOString();
}

/**
 * 解析日期字符串
 */
export function parseDate(dateStr: string): Date {
    return new Date(dateStr);
}

/**
 * 获取相对时间描述
 */
export function getRelativeTime(date: Date): string {
    const now = new Date();
    const diff = now.getTime() - date.getTime();

    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (seconds < 60) return '刚刚';
    if (minutes < 60) return `${minutes}分钟前`;
    if (hours < 24) return `${hours}小时前`;
    if (days < 7) return `${days}天前`;
    if (days < 30) return `${Math.floor(days / 7)}周前`;
    if (days < 365) return `${Math.floor(days / 30)}个月前`;
    return `${Math.floor(days / 365)}年前`;
}

// ============================================================
// 防抖和节流
// ============================================================

/**
 * 防抖函数
 */
export function debounce<T extends (...args: any[]) => any>(
    func: T,
    wait: number
): (...args: Parameters<T>) => void {
    let timeout: ReturnType<typeof setTimeout> | null = null;

    return (...args: Parameters<T>) => {
        if (timeout) clearTimeout(timeout);
        timeout = setTimeout(() => func(...args), wait);
    };
}

/**
 * 节流函数
 */
export function throttle<T extends (...args: any[]) => any>(
    func: T,
    limit: number
): (...args: Parameters<T>) => void {
    let inThrottle = false;

    return (...args: Parameters<T>) => {
        if (!inThrottle) {
            func(...args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// ============================================================
// 深拷贝
// ============================================================

/**
 * 深拷贝对象
 */
export function deepClone<T>(obj: T): T {
    return JSON.parse(JSON.stringify(obj));
}

// ============================================================
// 文件操作
// ============================================================

/**
 * 将 Data URL 转换为 Blob
 */
export function dataURLToBlob(dataURL: string): Blob {
    const parts = dataURL.split(',');
    const mime = parts[0].match(/:(.*?);/)?.[1] || '';
    const bstr = atob(parts[1]);
    let n = bstr.length;
    const u8arr = new Uint8Array(n);

    while (n--) {
        u8arr[n] = bstr.charCodeAt(n);
    }

    return new Blob([u8arr], { type: mime });
}

/**
 * 将 Blob 转换为 Data URL
 */
export function blobToDataURL(blob: Blob): Promise<string> {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result as string);
        reader.onerror = reject;
        reader.readAsDataURL(blob);
    });
}

// ============================================================
// 后端数据转换
// ============================================================

/**
 * 将后端标注数据转换为前端 Annotation 格式
 */
export function transformBackendAnnotation(backendAnnotation: any): any {
    const { annotation_type, data, page_number, user_id, user_name, created_at, id } = backendAnnotation;

    // 解析 data 字段（可能是字符串或对象）
    const parsedData = typeof data === 'string' ? JSON.parse(data) : data;

    if (annotation_type === 'shape') {
        // 图形标注
        return {
            id: parsedData.id || id,
            type: 'shape',
            pageNumber: page_number,
            geometry: parsedData.geometry,
            style: {
                type: parsedData.shapeType,
                color: parsedData.style?.color || '#2196F3',
                opacity: parsedData.style?.opacity || 0.8,
                strokeWidth: parsedData.style?.strokeWidth || 2,
                fillColor: parsedData.style?.fillColor,
                fillOpacity: parsedData.style?.fillOpacity || 0.2,
                lineStyle: parsedData.style?.lineStyle || 'solid',
            },
            metadata: {
                createdAt: created_at,
                updatedAt: backendAnnotation.updated_at,
                userId: user_id,
                userName: user_name || 'Anonymous',
            },
        };
    } else if (annotation_type === 'text-markup') {
        // 文本标注（高亮、下划线等）
        return {
            id: parsedData.id || id,
            type: 'text-markup',
            subtype: parsedData.subtype,
            textAnchor: parsedData.textAnchor,
            pdfCoordinates: parsedData.pdfCoordinates,
            style: parsedData.style,
            metadata: {
                createdAt: created_at,
                updatedAt: backendAnnotation.updated_at,
                userId: user_id,
                userName: user_name || 'Anonymous',
            },
        };
    }

    // 其他类型标注
    return {
        ...parsedData,
        id: parsedData.id || id,
        pageNumber: page_number,
        metadata: {
            createdAt: created_at,
            updatedAt: backendAnnotation.updated_at,
            userId: user_id,
            userName: user_name || 'Anonymous',
        },
    };
}
