/**
 * AI Chat Panel Component
 */

import { useState, useRef, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { FiSend, FiX } from 'react-icons/fi';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import remarkGfm from 'remark-gfm';
import { apiService } from '../services/api';
import { useChatStore } from '../stores';
import type { ChatMessage } from '../types';

interface ChatPanelProps {
    documentId: string;
    onClose?: () => void;
}

export default function ChatPanel({ documentId, onClose }: ChatPanelProps) {
    const [inputValue, setInputValue] = useState('');
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const { messages, addMessage, setLoading, isLoading } = useChatStore();

    // Auto scroll to bottom
    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Chat mutation
    const chatMutation = useMutation({
        mutationFn: (question: string) =>
            apiService.chat(documentId, { question }),
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

    return (
        <div className="h-full flex flex-col">
            {/* Header */}
            <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-gray-900">AI 问答</h2>
                {onClose && (
                    <button
                        onClick={onClose}
                        className="btn-icon"
                        aria-label="关闭"
                    >
                        <FiX className="w-5 h-5" />
                    </button>
                )}
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin">
                {messages.length === 0 ? (
                    <div className="text-center text-gray-500 mt-8">
                        <p className="mb-2">👋 你好！我是 AI 助手</p>
                        <p className="text-sm">问我任何关于这个文档的问题</p>
                    </div>
                ) : (
                    messages.map((message, index) => (
                        <MessageBubble key={index} message={message} />
                    ))
                )}

                {isLoading && (
                    <div className="flex items-start gap-3">
                        <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center flex-shrink-0">
                            <span className="text-primary-600 text-sm font-medium">AI</span>
                        </div>
                        <div className="flex items-center gap-2 text-gray-500">
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100" />
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200" />
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <form
                onSubmit={handleSubmit}
                className="border-t border-gray-200 p-4 bg-white"
            >
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        placeholder="输入问题..."
                        className="input flex-1"
                        disabled={isLoading}
                    />
                    <button
                        type="submit"
                        disabled={!inputValue.trim() || isLoading}
                        className="btn btn-primary"
                        aria-label="发送"
                    >
                        <FiSend className="w-4 h-4" />
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
            className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'
                }`}
        >
            {/* Avatar */}
            <div
                className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${isUser
                    ? 'bg-primary-600 text-white'
                    : 'bg-primary-100 text-primary-600'
                    }`}
            >
                <span className="text-sm font-medium">{isUser ? '我' : 'AI'}</span>
            </div>

            {/* Message content */}
            <div
                className={`flex-1 ${isUser ? 'text-right' : 'text-left'} max-w-[80%]`}
            >
                <div
                    className={`inline-block rounded-lg px-4 py-2 ${isUser
                        ? 'bg-primary-600 text-white'
                        : 'bg-gray-100 text-gray-900'
                        }`}
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
                                            // @ts-ignore - SyntaxHighlighter type issue
                                            <SyntaxHighlighter
                                                style={vscDarkPlus as any}
                                                language={match[1]}
                                                PreTag="div"
                                            >
                                                {String(children).replace(/\n$/, '')}
                                            </SyntaxHighlighter>
                                        ) : (
                                            <code className={className} {...props}>
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

                {/* Sources */}
                {message.sources && message.sources.length > 0 && (
                    <div className="mt-2 text-xs text-gray-500">
                        <p className="mb-1">📚 参考来源：</p>
                        {message.sources.map((source, idx) => (
                            <div
                                key={idx}
                                className="bg-gray-50 rounded p-2 mb-1 text-left"
                            >
                                <p className="font-medium">
                                    第 {source.page_number} 页 (相似度:{' '}
                                    {(source.similarity_score * 100).toFixed(1)}%)
                                </p>
                                <p className="mt-1 text-gray-600 line-clamp-2">
                                    {source.content}
                                </p>
                            </div>
                        ))}
                    </div>
                )}

                {/* Timestamp */}
                {message.timestamp && (
                    <p className="text-xs text-gray-500 mt-1">
                        {new Date(message.timestamp).toLocaleTimeString('zh-CN')}
                    </p>
                )}
            </div>
        </div>
    );
}
