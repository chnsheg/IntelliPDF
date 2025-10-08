/**
 * 文本锚点服务
 * 用于创建和重新定位基于文本的标注
 */

import type { PDFPageProxy } from 'pdfjs-dist';
import type { TextAnchor } from '../../types/annotation';
import { sha256, escapeRegex, diceCoefficient } from '../../utils/annotation';

export class TextAnchorService {
    /**
     * 创建文本锚点
     */
    async createTextAnchor(
        selection: Selection,
        pageNumber: number,
        pdfPage: PDFPageProxy
    ): Promise<TextAnchor> {
        // 1. 获取页面完整文本
        const pageText = await this.getPageText(pdfPage);

        // 2. 获取选中文本
        const selectedText = selection.toString().trim();
        if (!selectedText) {
            throw new Error('No text selected');
        }

        // 3. 计算选中文本在页面中的位置
        const startOffset = pageText.indexOf(selectedText);
        if (startOffset === -1) {
            throw new Error('Selected text not found in page');
        }
        const endOffset = startOffset + selectedText.length;

        // 4. 提取前后文
        const prefixStart = Math.max(0, startOffset - 50);
        const prefix = pageText.substring(prefixStart, startOffset);

        const suffixEnd = Math.min(pageText.length, endOffset + 50);
        const suffix = pageText.substring(endOffset, suffixEnd);

        // 5. 计算文本指纹
        const textHash = await sha256(pageText);

        return {
            selectedText,
            prefix,
            suffix,
            pageNumber,
            startOffset,
            endOffset,
            textHash
        };
    }

    /**
     * 获取页面文本内容
     */
    private async getPageText(pdfPage: PDFPageProxy): Promise<string> {
        const textContent = await pdfPage.getTextContent();
        return textContent.items
            .map((item: any) => item.str)
            .join('');
    }

    /**
     * 重新定位标注（三种策略）
     */
    async relocateAnnotation(
        anchor: TextAnchor,
        pdfPage: PDFPageProxy
    ): Promise<{ startOffset: number; endOffset: number } | null> {
        // 获取当前页面文本
        const pageText = await this.getPageText(pdfPage);

        // 策略1：精确匹配（最快）
        const exactMatch = this.exactMatch(pageText, anchor);
        if (exactMatch) return exactMatch;

        // 策略2：前后文匹配（中等）
        const contextMatch = this.contextMatch(pageText, anchor);
        if (contextMatch) return contextMatch;

        // 策略3：模糊匹配（最慢，最宽容）
        const fuzzyMatch = this.fuzzyMatch(pageText, anchor, 0.85);
        if (fuzzyMatch) return fuzzyMatch;

        // 失败
        console.warn('Failed to relocate annotation:', {
            text: anchor.selectedText.substring(0, 20) + '...',
            pageNumber: anchor.pageNumber
        });
        return null;
    }

    /**
     * 策略1：精确匹配
     */
    private exactMatch(
        pageText: string,
        anchor: TextAnchor
    ): { startOffset: number; endOffset: number } | null {
        const startOffset = pageText.indexOf(anchor.selectedText);
        if (startOffset !== -1) {
            return {
                startOffset,
                endOffset: startOffset + anchor.selectedText.length
            };
        }
        return null;
    }

    /**
     * 策略2：前后文匹配
     */
    private contextMatch(
        pageText: string,
        anchor: TextAnchor
    ): { startOffset: number; endOffset: number } | null {
        // 构建正则表达式：prefix + (任意文本) + suffix
        const pattern = escapeRegex(anchor.prefix) +
            '(.+?)' +
            escapeRegex(anchor.suffix);

        const regex = new RegExp(pattern, 's');
        const match = pageText.match(regex);

        if (match && match.index !== undefined) {
            const startOffset = match.index + anchor.prefix.length;
            return {
                startOffset,
                endOffset: startOffset + match[1].length
            };
        }

        return null;
    }

    /**
     * 策略3：模糊匹配
     */
    private fuzzyMatch(
        pageText: string,
        anchor: TextAnchor,
        threshold: number
    ): { startOffset: number; endOffset: number } | null {
        const needleLen = anchor.selectedText.length;
        const windowSize = Math.floor(needleLen * 1.5);  // 允许 50% 长度差异

        let bestMatch = { score: 0, start: -1, end: -1 };

        // 滑动窗口搜索
        for (let i = 0; i <= pageText.length - needleLen; i += 5) {  // 步长5，提高性能
            const window = pageText.substring(i, Math.min(i + windowSize, pageText.length));

            // 使用 Dice 系数计算相似度
            const similarity = diceCoefficient(window, anchor.selectedText);

            if (similarity > bestMatch.score) {
                bestMatch = {
                    score: similarity,
                    start: i,
                    end: i + needleLen
                };
            }

            // 如果找到非常高的匹配度，提前退出
            if (similarity > 0.95) break;
        }

        if (bestMatch.score >= threshold) {
            return {
                startOffset: bestMatch.start,
                endOffset: bestMatch.end
            };
        }

        return null;
    }

    /**
     * 验证文本锚点是否仍然有效
     */
    async validate(
        anchor: TextAnchor,
        pdfPage: PDFPageProxy
    ): Promise<boolean> {
        const pageText = await this.getPageText(pdfPage);

        // 检查文本指纹
        const currentHash = await sha256(pageText);
        if (currentHash !== anchor.textHash) {
            console.warn('Page text has changed:', {
                pageNumber: anchor.pageNumber,
                expected: anchor.textHash.substring(0, 8),
                actual: currentHash.substring(0, 8)
            });
            return false;
        }

        // 检查精确位置
        const textAtPosition = pageText.substring(
            anchor.startOffset,
            anchor.endOffset
        );

        if (textAtPosition !== anchor.selectedText) {
            console.warn('Text at position has changed:', {
                pageNumber: anchor.pageNumber,
                expected: anchor.selectedText.substring(0, 20),
                actual: textAtPosition.substring(0, 20)
            });
            return false;
        }

        return true;
    }
}

// 单例导出
export const textAnchorService = new TextAnchorService();
