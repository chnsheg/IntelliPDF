/**
 * Modern AI Chat Panel Component with gradients and animations
 */

import { useState, useRef, useEffect, useCallback } from 'react';
import { useMutation } from '@tanstack/react-query';
import { FiSend, FiX, FiCopy, FiCheck, FiExternalLink } from 'react-icons/fi';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import remarkGfm from 'remark-gfm';
import clsx from 'clsx';
import { apiService } from '../services/api';
import { useChatStore } from '../stores';
import type { ChatMessage } from '../types';
import { DotsLoader } from './Loading';

interface ChatPanelProps {
    documentId: string;
    currentPage?: number;
    selectedText?: string;
    selectedTextPosition?: { x: number; y: number; width: number; height: number };
    onClose?: () => void;
    onBookmarkCreated?: () => void;
}

export default function ChatPanel({
    documentId,
    currentPage = 1,
    selectedText,
    selectedTextPosition,
    onClose,
    onBookmarkCreated
}: ChatPanelProps) {
    const [inputValue, setInputValue] = useState('');
    const [contextChunks, setContextChunks] = useState<string[]>([]);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const { messages, addMessage, setLoading, isLoading } = useChatStore();

    // 话题上下文管理
    // topicContext: 当前话题的上下文（选中的文本）
    // topicStartIndex: 当前话题开始的消息索引
    const [topicContext, setTopicContext] = useState<{
        text: string;
        pageNumber: number;
        position: { x: number; y: number; width: number; height: number };
        chunkContext?: string[];
    } | null>(null);
    const [topicStartIndex, setTopicStartIndex] = useState<number>(0);

    // Auto scroll to bottom
    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Fetch context when page changes
    useEffect(() => {
        const fetchContext = async () => {
            try {
                const contextData = await apiService.getCurrentContext(
                    documentId,
                    currentPage
                );
                const chunkContents = contextData.relevant_chunks.map(
                    (chunk) => chunk.content
                );
                setContextChunks(chunkContents);
            } catch (error) {
                console.error('Failed to fetch context:', error);
                setContextChunks([]);
            }
        };

        if (currentPage) {
            fetchContext();
        }
    }, [documentId, currentPage]);

    // Chat mutation
    const chatMutation = useMutation({
        mutationFn: async (question: string) => {
            // Prepare question with context if available
            let enhancedQuestion = question;
            if (contextChunks.length > 0) {
                const contextText = contextChunks.slice(0, 2).join('\n\n');
                enhancedQuestion = `基于以下上下文回答问题:\n\n上下文:\n${contextText}\n\n问题: ${question}`;
            }
            return apiService.chat(documentId, { question: enhancedQuestion });
        },
        onMutate: (question) => {
            // Add user message
            addMessage({
                role: 'user',
                content: question,
                timestamp: new Date().toISOString(),
            });
            setLoading(true);
        },
        onSuccess: (response) => {
            if (response) {
                // Add assistant message
                addMessage({
                    role: 'assistant',
                    content: response.answer,
                    timestamp: new Date().toISOString(),
                    sources: response.sources,
                });
            }
            setLoading(false);
        },
        onError: (error) => {
            addMessage({
                role: 'assistant',
                content: `抱歉，出现错误：${(error as Error).message}`,
                timestamp: new Date().toISOString(),
            });
            setLoading(false);
        },
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        const question = inputValue.trim();
        if (!question || isLoading) return;

        chatMutation.mutate(question);
        setInputValue('');
    };

    // 设置话题上下文（仅在点击AI提问按钮时调用）
    const setTopicFromSelection = useCallback((text: string, page: number, position: any, context?: string[]) => {
        // 如果选中的文本发生变化，则设置新话题
        if (!topicContext || topicContext.text !== text) {
            setTopicContext({
                text,
                pageNumber: page,
                position,
                chunkContext: context || contextChunks,
            });
            setTopicStartIndex(messages.length);
        }
    }, [topicContext, contextChunks, messages.length]);

    // 清除话题上下文
    const clearTopicContext = useCallback(() => {
        setTopicContext(null);
        setTopicStartIndex(messages.length);
    }, [messages.length]);

    // Listen for setTopicContext events from PDFViewerEnhanced
    useEffect(() => {
        const handleSetTopicContext = (e: Event) => {
            const ce = e as CustomEvent;
            const detail = ce.detail || {};
            const text = detail.selected_text || '';
            const page = Number(detail.page_number) || currentPage;
            const position = detail.position;
            const context = detail.chunk_context;

            if (text && page) {
                setTopicFromSelection(text, page, position, context);
            }
        };

        window.addEventListener('setTopicContext', handleSetTopicContext);
        return () => window.removeEventListener('setTopicContext', handleSetTopicContext);
    }, [setTopicFromSelection, currentPage]);

    // Handle bookmark generation - 基于当前话题的对话历史
    useEffect(() => {
        const handleGenerateBookmark = async (e: Event) => {
            try {
                const ce = e as CustomEvent;
                const detail = ce.detail || {};

                if (detail.documentId !== documentId) return;

                // 只使用当前话题的对话历史（从topicStartIndex开始）
                const topicMessages = messages.slice(topicStartIndex);

                if (topicMessages.length === 0) {
                    console.warn('No conversation in current topic');
                    return;
                }

                // 准备对话历史
                const conversationHistory = topicMessages.map(msg => ({
                    role: msg.role,
                    content: msg.content
                }));

                // 调用API生成书签
                const response = await apiService.generateBookmark({
                    document_id: documentId,
                    conversation_history: conversationHistory,
                    context_text: topicContext?.text,
                    page_number: topicContext?.pageNumber || currentPage
                });

                // 生成书签后，可以选择清除当前话题或保持
                // clearTopicContext(); // 可选：生成后开始新话题

                if (onBookmarkCreated) {
                    onBookmarkCreated();
                }

                console.log('Bookmark generated:', response);
            } catch (error) {
                console.error('Failed to generate bookmark:', error);
            }
        };

        window.addEventListener('generateBookmark', handleGenerateBookmark);
        return () => window.removeEventListener('generateBookmark', handleGenerateBookmark);
    }, [documentId, messages, topicStartIndex, topicContext, currentPage, onBookmarkCreated]);

    return (
        <div className="h-full flex flex-col">
            {/* Modern Header with Glass Effect */}
            <div className="glass backdrop-blur-xl bg-white/80 border-b border-gray-200 px-4 py-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
                        <span className="text-xl">🤖</span>
                    </div>
                    <div>
                        <h2 className="text-lg font-semibold bg-gradient-to-r from-primary-600 to-accent-600 bg-clip-text text-transparent">
                            AI 智能问答
                        </h2>
                        <p className="text-xs text-gray-500">基于文档内容的智能回答</p>
                    </div>
                </div>
                {onClose && (
                    <button
                        onClick={onClose}
                        className="p-2 rounded-lg hover:bg-gray-100 transition-all duration-300 hover:scale-110 active:scale-95"
                        aria-label="关闭"
                    >
                        <FiX className="w-5 h-5 text-gray-600" />
                    </button>
                )}
            </div>

            {/* Messages with animations */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin bg-gradient-to-b from-gray-50 to-white">
                {messages.length === 0 ? (
                    <div className="text-center mt-12 animate-fadeInUp">
                        <div className="w-20 h-20 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center animate-bounceSoft">
                            <span className="text-4xl">👋</span>
                        </div>
                        <h3 className="text-xl font-semibold text-gray-900 mb-2">
                            你好！我是 AI 助手
                        </h3>
                        <p className="text-sm text-gray-600 mb-6">
                            问我任何关于这个文档的问题
                        </p>
                        <div className="max-w-md mx-auto space-y-2">
                            <button
                                onClick={() => setInputValue('这个文档的主要内容是什么？')}
                                className="w-full px-4 py-3 text-left bg-white rounded-xl border border-gray-200 hover:border-primary-300 hover:shadow-md transition-all duration-300 text-sm text-gray-700"
                            >
                                💡 这个文档的主要内容是什么？
                            </button>
                            <button
                                onClick={() => setInputValue('总结一下关键要点')}
                                className="w-full px-4 py-3 text-left bg-white rounded-xl border border-gray-200 hover:border-primary-300 hover:shadow-md transition-all duration-300 text-sm text-gray-700"
                            >
                                📝 总结一下关键要点
                            </button>
                            <button
                                onClick={() => setInputValue('有哪些重要的数据或结论？')}
                                className="w-full px-4 py-3 text-left bg-white rounded-xl border border-gray-200 hover:border-primary-300 hover:shadow-md transition-all duration-300 text-sm text-gray-700"
                            >
                                📊 有哪些重要的数据或结论？
                            </button>
                        </div>
                    </div>
                ) : (
                    messages.map((message, index) => (
                        <div
                            key={index}
                            className="animate-fadeInUp"
                            style={{ animationDelay: `${index * 50}ms` }}
                        >
                            <MessageBubble message={message} />
                        </div>
                    ))
                )}

                {isLoading && (
                    <div className="flex items-start gap-3 animate-fadeIn">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-100 to-accent-100 flex items-center justify-center flex-shrink-0">
                            <span className="text-primary-600 text-sm font-medium">AI</span>
                        </div>
                        <div className="flex items-center gap-2 bg-white px-4 py-3 rounded-xl border border-gray-200 shadow-sm">
                            <DotsLoader />
                            <span className="text-sm text-gray-600 ml-2">正在思考中...</span>
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Modern Input with Glass Effect */}
            <form
                onSubmit={handleSubmit}
                className="glass backdrop-blur-xl bg-white/80 border-t border-gray-200 p-4"
            >
                {/* 话题上下文显示区域 */}
                {topicContext && (
                    <div className="mb-3 p-3 bg-gradient-to-r from-blue-50 to-purple-50 border-2 border-blue-300 rounded-xl relative">
                        {/* 关闭按钮 */}
                        <button
                            type="button"
                            onClick={clearTopicContext}
                            className="absolute top-2 right-2 w-5 h-5 flex items-center justify-center text-gray-500 hover:text-gray-700 hover:bg-white/50 rounded transition-colors"
                            title="关闭话题上下文，代表对整个文章提问"
                        >
                            ✕
                        </button>

                        <div className="flex items-center justify-between mb-1 pr-6">
                            <div className="flex items-center gap-2">
                                <span className="text-xs font-semibold text-blue-700">📌 当前话题</span>
                                <span className="text-xs bg-blue-200 text-blue-800 px-2 py-0.5 rounded-full">
                                    {messages.length - topicStartIndex} 条对话
                                </span>
                            </div>
                            <span className="text-xs text-blue-600">第 {topicContext.pageNumber} 页</span>
                        </div>
                        <p className="text-sm text-gray-700 line-clamp-2 mb-1">{topicContext.text}</p>
                        <div className="flex items-center justify-between">
                            <p className="text-xs text-gray-500">💡 当前对话都围绕这段文本展开</p>
                        </div>
                    </div>
                )}

                {/* 生成书签按钮 */}
                {messages.length > topicStartIndex && (
                    <div className="mb-3 flex justify-end">
                        <button
                            type="button"
                            onClick={() => {
                                window.dispatchEvent(new CustomEvent('generateBookmark', {
                                    detail: { documentId }
                                }));
                            }}
                            className="px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:from-purple-600 hover:to-pink-600 transition-all duration-300 flex items-center gap-2 text-sm font-medium shadow-md hover:shadow-lg"
                            title={`根据当前话题的 ${messages.length - topicStartIndex} 条对话生成AI书签`}
                        >
                            <span>📑</span>
                            <span>生成AI书签</span>
                            <span className="text-xs opacity-80">({messages.length - topicStartIndex}条对话)</span>
                        </button>
                    </div>
                )}

                <div className="flex gap-3">
                    <input
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        placeholder="输入您的问题..."
                        className="flex-1 px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-primary-500 focus:ring-4 focus:ring-primary-500/10 transition-all duration-300 outline-none"
                        disabled={isLoading}
                    />
                    <button
                        type="submit"
                        disabled={!inputValue.trim() || isLoading}
                        className={clsx(
                            'px-6 py-3 rounded-xl font-medium transition-all duration-300',
                            'flex items-center gap-2',
                            'hover:scale-105 active:scale-95',
                            'shadow-lg',
                            inputValue.trim() && !isLoading
                                ? 'bg-gradient-to-r from-primary-600 to-accent-600 text-white hover:shadow-xl'
                                : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                        )}
                        aria-label="发送"
                    >
                        <FiSend className="w-4 h-4" />
                        <span className="hidden sm:inline">发送</span>
                    </button>
                </div>
            </form>
        </div>
    );
}

function MessageBubble({ message }: { message: ChatMessage }) {
    const isUser = message.role === 'user';

    return (
        <div
            className={clsx(
                'flex items-start gap-3',
                isUser ? 'flex-row-reverse' : 'flex-row'
            )}
        >
            {/* Avatar with gradient */}
            <div
                className={clsx(
                    'w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg',
                    'transition-all duration-300 hover:scale-110',
                    isUser
                        ? 'bg-gradient-to-br from-primary-600 to-accent-600 text-white'
                        : 'bg-gradient-to-br from-primary-100 to-accent-100 text-primary-600'
                )}
            >
                <span className="text-sm font-medium">{isUser ? '我' : 'AI'}</span>
            </div>

            {/* Message content */}
            <div
                className={clsx(
                    'flex-1 max-w-[80%]',
                    isUser ? 'text-right' : 'text-left'
                )}
            >
                <div
                    className={clsx(
                        'inline-block rounded-2xl px-4 py-3 shadow-lg',
                        'transition-all duration-300 hover:shadow-xl',
                        isUser
                            ? 'bg-gradient-to-br from-primary-600 to-accent-600 text-white'
                            : 'bg-white text-gray-900 border border-gray-200'
                    )}
                >
                    {isUser ? (
                        <p className="whitespace-pre-wrap break-words">{message.content}</p>
                    ) : (
                        <div className="prose prose-sm max-w-none">
                            <ReactMarkdown
                                remarkPlugins={[remarkGfm]}
                                components={{
                                    code({ className, children, ...props }) {
                                        const match = /language-(\w+)/.exec(className || '');
                                        const isInline = !match;

                                        return !isInline ? (
                                            <CodeBlock
                                                language={match[1]}
                                                code={String(children).replace(/\n$/, '')}
                                            />
                                        ) : (
                                            <code
                                                className="px-1.5 py-0.5 rounded bg-gray-100 text-primary-600 font-mono text-sm"
                                                {...props}
                                            >
                                                {children}
                                            </code>
                                        );
                                    },
                                }}
                            >
                                {message.content}
                            </ReactMarkdown>
                        </div>
                    )}
                </div>

                {/* Enhanced Sources */}
                {message.sources && message.sources.length > 0 && (
                    <div className="mt-3 space-y-2">
                        <p className="text-xs font-medium text-gray-500 flex items-center gap-1">
                            📚 参考来源 ({message.sources.length})
                        </p>
                        {message.sources.map((source, idx) => (
                            <div
                                key={idx}
                                onClick={() => {
                                    // 触发页面跳转事件
                                    const pageNum = source.page_number || (source as any).page;
                                    if (pageNum) {
                                        window.dispatchEvent(new CustomEvent('jumpToPage', {
                                            detail: { page_number: pageNum }
                                        }));
                                    }
                                }}
                                className={clsx(
                                    'bg-white rounded-xl p-3 border border-gray-200',
                                    'transition-all duration-300 hover:shadow-md hover:border-primary-300',
                                    'cursor-pointer group'
                                )}
                            >
                                <div className="flex items-center justify-between mb-2">
                                    <span className="text-xs font-medium text-primary-600 flex items-center gap-1">
                                        📄 第 {source.page_number || (source as any).page} 页
                                    </span>
                                    <div className="flex items-center gap-2">
                                        <div className={clsx(
                                            'px-2 py-0.5 rounded-full text-xs font-medium',
                                            source.similarity_score > 0.8
                                                ? 'bg-green-100 text-green-700'
                                                : source.similarity_score > 0.6
                                                    ? 'bg-blue-100 text-blue-700'
                                                    : 'bg-gray-100 text-gray-700'
                                        )}>
                                            {(source.similarity_score * 100).toFixed(0)}%
                                        </div>
                                        <FiExternalLink className="w-3 h-3 text-gray-400 group-hover:text-primary-500 transition-colors duration-300" />
                                    </div>
                                </div>
                                <p className="text-xs text-gray-600 line-clamp-2">
                                    {source.content}
                                </p>
                            </div>
                        ))}
                    </div>
                )}

                {/* Timestamp */}
                {message.timestamp && (
                    <p className="text-xs text-gray-400 mt-2">
                        {new Date(message.timestamp).toLocaleTimeString('zh-CN')}
                    </p>
                )}
            </div>
        </div>
    );
}

function CodeBlock({ language, code }: { language: string; code: string }) {
    const [copied, setCopied] = useState(false);

    const handleCopy = () => {
        navigator.clipboard.writeText(code);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="relative group my-4">
            <button
                onClick={handleCopy}
                className={clsx(
                    'absolute top-2 right-2 p-2 rounded-lg',
                    'transition-all duration-300',
                    'opacity-0 group-hover:opacity-100',
                    copied
                        ? 'bg-green-500 text-white'
                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                )}
                aria-label="复制代码"
            >
                {copied ? (
                    <FiCheck className="w-4 h-4" />
                ) : (
                    <FiCopy className="w-4 h-4" />
                )}
            </button>
            {/* @ts-ignore - SyntaxHighlighter type issue */}
            <SyntaxHighlighter
                style={vscDarkPlus as any}
                language={language}
                PreTag="div"
                className="rounded-xl !mt-0 !mb-0"
            >
                {code}
            </SyntaxHighlighter>
        </div>
    );
}
