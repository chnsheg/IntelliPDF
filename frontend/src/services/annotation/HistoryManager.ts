/**
 * Command Pattern for Undo/Redo System
 * 
 * 实现命令模式，支持标注的撤销和重做操作
 */

import type { Annotation } from '../../types/annotation';

/**
 * 命令接口
 */
export interface Command {
    /** 命令唯一标识 */
    id: string;
    /** 命令类型 */
    type: 'create' | 'delete' | 'update' | 'move' | 'resize';
    /** 执行命令 */
    execute(): Promise<void>;
    /** 撤销命令 */
    undo(): Promise<void>;
    /** 命令描述（用于调试和UI显示） */
    getDescription(): string;
}

/**
 * 创建标注命令
 */
export class CreateAnnotationCommand implements Command {
    public readonly id: string;
    public readonly type = 'create' as const;
    private annotation: Annotation;
    private onCreate: (annotation: Annotation) => Promise<void>;
    private onDelete: (annotationId: string) => Promise<void>;

    constructor(
        annotation: Annotation,
        onCreate: (annotation: Annotation) => Promise<void>,
        onDelete: (annotationId: string) => Promise<void>
    ) {
        this.id = `create-${annotation.id}`;
        this.annotation = annotation;
        this.onCreate = onCreate;
        this.onDelete = onDelete;
    }

    async execute(): Promise<void> {
        await this.onCreate(this.annotation);
    }

    async undo(): Promise<void> {
        await this.onDelete(this.annotation.id);
    }

    getDescription(): string {
        return `创建${this.annotation.type}标注`;
    }
}

/**
 * 删除标注命令
 */
export class DeleteAnnotationCommand implements Command {
    public readonly id: string;
    public readonly type = 'delete' as const;
    private annotation: Annotation;
    private onDelete: (annotationId: string) => Promise<void>;
    private onCreate: (annotation: Annotation) => Promise<void>;

    constructor(
        annotation: Annotation,
        onDelete: (annotationId: string) => Promise<void>,
        onCreate: (annotation: Annotation) => Promise<void>
    ) {
        this.id = `delete-${annotation.id}`;
        this.annotation = annotation;
        this.onDelete = onDelete;
        this.onCreate = onCreate;
    }

    async execute(): Promise<void> {
        await this.onDelete(this.annotation.id);
    }

    async undo(): Promise<void> {
        await this.onCreate(this.annotation);
    }

    getDescription(): string {
        return `删除${this.annotation.type}标注`;
    }
}

/**
 * 更新标注命令
 */
export class UpdateAnnotationCommand implements Command {
    public readonly id: string;
    public readonly type = 'update' as const;
    private annotationId: string;
    private oldData: Partial<Annotation>;
    private newData: Partial<Annotation>;
    private onUpdate: (annotationId: string, data: Partial<Annotation>) => Promise<void>;

    constructor(
        annotationId: string,
        oldData: Partial<Annotation>,
        newData: Partial<Annotation>,
        onUpdate: (annotationId: string, data: Partial<Annotation>) => Promise<void>
    ) {
        this.id = `update-${annotationId}-${Date.now()}`;
        this.annotationId = annotationId;
        this.oldData = oldData;
        this.newData = newData;
        this.onUpdate = onUpdate;
    }

    async execute(): Promise<void> {
        await this.onUpdate(this.annotationId, this.newData);
    }

    async undo(): Promise<void> {
        await this.onUpdate(this.annotationId, this.oldData);
    }

    getDescription(): string {
        return `更新标注`;
    }
}

/**
 * 移动标注命令
 */
export class MoveAnnotationCommand implements Command {
    public readonly id: string;
    public readonly type = 'move' as const;
    private annotationId: string;
    private oldPosition: { x: number; y: number; width: number; height: number };
    private newPosition: { x: number; y: number; width: number; height: number };
    private onMove: (annotationId: string, geometry: any) => Promise<void>;

    constructor(
        annotationId: string,
        oldPosition: { x: number; y: number; width: number; height: number },
        newPosition: { x: number; y: number; width: number; height: number },
        onMove: (annotationId: string, geometry: any) => Promise<void>
    ) {
        this.id = `move-${annotationId}-${Date.now()}`;
        this.annotationId = annotationId;
        this.oldPosition = oldPosition;
        this.newPosition = newPosition;
        this.onMove = onMove;
    }

    async execute(): Promise<void> {
        await this.onMove(this.annotationId, this.newPosition);
    }

    async undo(): Promise<void> {
        await this.onMove(this.annotationId, this.oldPosition);
    }

    getDescription(): string {
        return `移动标注`;
    }
}

/**
 * 调整标注大小命令
 */
export class ResizeAnnotationCommand implements Command {
    public readonly id: string;
    public readonly type = 'resize' as const;
    private annotationId: string;
    private oldSize: { x: number; y: number; width: number; height: number };
    private newSize: { x: number; y: number; width: number; height: number };
    private onResize: (annotationId: string, geometry: any) => Promise<void>;

    constructor(
        annotationId: string,
        oldSize: { x: number; y: number; width: number; height: number },
        newSize: { x: number; y: number; width: number; height: number },
        onResize: (annotationId: string, geometry: any) => Promise<void>
    ) {
        this.id = `resize-${annotationId}-${Date.now()}`;
        this.annotationId = annotationId;
        this.oldSize = oldSize;
        this.newSize = newSize;
        this.onResize = onResize;
    }

    async execute(): Promise<void> {
        await this.onResize(this.annotationId, this.newSize);
    }

    async undo(): Promise<void> {
        await this.onResize(this.annotationId, this.oldSize);
    }

    getDescription(): string {
        return `调整标注大小`;
    }
}

/**
 * 历史管理器
 */
export class HistoryManager {
    private undoStack: Command[] = [];
    private redoStack: Command[] = [];
    private maxHistorySize: number = 50;
    private isExecuting: boolean = false;

    /**
     * 执行命令并添加到历史栈
     */
    async execute(command: Command): Promise<void> {
        if (this.isExecuting) {
            console.warn('Command is already executing');
            return;
        }

        this.isExecuting = true;

        try {
            await command.execute();

            // 添加到 undo 栈
            this.undoStack.push(command);

            // 清空 redo 栈（执行新命令后不能再 redo）
            this.redoStack = [];

            // 限制历史记录大小
            if (this.undoStack.length > this.maxHistorySize) {
                this.undoStack.shift();
            }

            console.log(`Executed: ${command.getDescription()}`);
        } catch (error) {
            console.error(`Failed to execute command: ${command.getDescription()}`, error);
            throw error;
        } finally {
            this.isExecuting = false;
        }
    }

    /**
     * 撤销上一个命令
     */
    async undo(): Promise<boolean> {
        if (!this.canUndo() || this.isExecuting) {
            return false;
        }

        this.isExecuting = true;

        try {
            const command = this.undoStack.pop()!;
            await command.undo();

            // 添加到 redo 栈
            this.redoStack.push(command);

            console.log(`Undone: ${command.getDescription()}`);
            return true;
        } catch (error) {
            console.error('Failed to undo command', error);
            return false;
        } finally {
            this.isExecuting = false;
        }
    }

    /**
     * 重做上一个撤销的命令
     */
    async redo(): Promise<boolean> {
        if (!this.canRedo() || this.isExecuting) {
            return false;
        }

        this.isExecuting = true;

        try {
            const command = this.redoStack.pop()!;
            await command.execute();

            // 添加回 undo 栈
            this.undoStack.push(command);

            console.log(`Redone: ${command.getDescription()}`);
            return true;
        } catch (error) {
            console.error('Failed to redo command', error);
            return false;
        } finally {
            this.isExecuting = false;
        }
    }

    /**
     * 检查是否可以撤销
     */
    canUndo(): boolean {
        return this.undoStack.length > 0;
    }

    /**
     * 检查是否可以重做
     */
    canRedo(): boolean {
        return this.redoStack.length > 0;
    }

    /**
     * 获取撤销栈大小
     */
    getUndoSize(): number {
        return this.undoStack.length;
    }

    /**
     * 获取重做栈大小
     */
    getRedoSize(): number {
        return this.redoStack.length;
    }

    /**
     * 清空历史记录
     */
    clear(): void {
        this.undoStack = [];
        this.redoStack = [];
        console.log('History cleared');
    }

    /**
     * 获取历史记录摘要（用于调试）
     */
    getHistorySummary(): { undo: string[]; redo: string[] } {
        return {
            undo: this.undoStack.map(cmd => cmd.getDescription()),
            redo: this.redoStack.map(cmd => cmd.getDescription()),
        };
    }
}

// 创建全局历史管理器实例
export const historyManager = new HistoryManager();
