/**
 * Modern AI Chat Panel Component with gradients and animations
 */

import { useState, useRef, useEffect } from 'react';
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
                                className={clsx(
                                    'bg-white rounded-xl p-3 border border-gray-200',
                                    'transition-all duration-300 hover:shadow-md hover:border-primary-300',
                                    'cursor-pointer group'
                                )}
                            >
                                <div className="flex items-center justify-between mb-2">
                                    <span className="text-xs font-medium text-primary-600 flex items-center gap-1">
                                        📄 第 {source.page_number} 页
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
