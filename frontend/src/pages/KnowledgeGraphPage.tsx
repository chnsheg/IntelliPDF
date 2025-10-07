/**
 * Knowledge Graph Visualization Page
 * Using React Flow for interactive graph visualization
 */

import { useState, useCallback, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import ReactFlow, {
    Controls,
    Background,
    useNodesState,
    useEdgesState,
    addEdge,
    BackgroundVariant,
    MiniMap,
    type Node,
    type Edge,
    type Connection,
} from 'reactflow';
import 'reactflow/dist/style.css';
import {
    FiRefreshCw,
    FiMaximize,
    FiDownload,
} from 'react-icons/fi';
import clsx from 'clsx';
import { apiService } from '../services/api';
import { Spinner } from '../components/Loading';

// Custom node types
const nodeTypes = {
    document: DocumentNode,
    entity: EntityNode,
};

function DocumentNode({ data }: { data: any }) {
    return (
        <div className="px-4 py-3 bg-gradient-to-br from-primary-500 to-accent-500 text-white rounded-xl shadow-lg border-2 border-white/20 min-w-[150px]">
            <div className="flex items-center gap-2 mb-1">
                <span className="text-lg">📄</span>
                <div className="font-semibold text-sm truncate">{data.label}</div>
            </div>
            {data.pages && (
                <div className="text-xs opacity-80">{data.pages} 页</div>
            )}
        </div>
    );
}

function EntityNode({ data }: { data: any }) {
    return (
        <div className="px-3 py-2 bg-white rounded-lg shadow-md border-2 border-primary-200 min-w-[100px]">
            <div className="flex items-center gap-2">
                <span>{data.icon || '🔗'}</span>
                <div className="font-medium text-sm text-gray-800 truncate">{data.label}</div>
            </div>
            {data.type && (
                <div className="text-xs text-gray-500 mt-1">{data.type}</div>
            )}
        </div>
    );
}

export default function KnowledgeGraphPage() {
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const [selectedLayout, setSelectedLayout] = useState<'horizontal' | 'vertical' | 'circular'>('horizontal');
    const [showMiniMap, setShowMiniMap] = useState(true);

    // Fetch graph data from API
    const { data: graphData, isLoading, refetch } = useQuery({
        queryKey: ['knowledge-graph-data'],
        queryFn: async () => {
            return await apiService.getGraphData(50);
        },
    });

    // Generate graph from API data
    useEffect(() => {
        if (!graphData || !graphData.nodes || graphData.nodes.length === 0) return;

        const newNodes: Node[] = [];
        const newEdges: Edge[] = [];

        // Create document nodes
        graphData.nodes.forEach((node: any, index: number) => {
            const position = calculateNodePosition(index, graphData.nodes.length, selectedLayout);

            newNodes.push({
                id: node.id,
                type: 'document',
                position,
                data: {
                    label: node.label,
                    pages: node.pages,
                },
            });
        });

        // Create edges from API data
        if (graphData.edges) {
            graphData.edges.forEach((edge: any) => {
                newEdges.push({
                    id: edge.id,
                    source: edge.source,
                    target: edge.target,
                    animated: true,
                    style: { stroke: '#6366f1' },
                    label: edge.type || '相关',
                });
            });
        }

        setNodes(newNodes);
        setEdges(newEdges);
    }, [graphData, selectedLayout, setNodes, setEdges]);

    const onConnect = useCallback(
        (params: Connection) => setEdges((eds: Edge[]) => addEdge(params, eds)),
        [setEdges]
    );

    const handleLayoutChange = (layout: 'horizontal' | 'vertical' | 'circular') => {
        setSelectedLayout(layout);
    };

    const handleExport = () => {
        // TODO: Implement export functionality
        alert('导出功能开发中...');
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-screen bg-gradient-to-b from-gray-50 to-white">
                <div className="text-center">
                    <Spinner size="lg" />
                    <p className="mt-4 text-gray-600">加载知识图谱中...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="h-screen flex flex-col bg-gradient-to-b from-gray-50 to-white">
            {/* Header */}
            <div className="bg-white border-b border-gray-200 px-6 py-4 shadow-sm">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl font-bold bg-gradient-to-r from-primary-600 to-accent-600 bg-clip-text text-transparent">
                            知识图谱
                        </h1>
                        <p className="text-sm text-gray-600 mt-1">
                            可视化文档关系和实体连接
                        </p>
                    </div>

                    <div className="flex items-center gap-3">
                        {/* Layout Selection */}
                        <div className="flex gap-2 bg-gray-100 rounded-lg p-1">
                            <button
                                onClick={() => handleLayoutChange('horizontal')}
                                className={clsx(
                                    'px-3 py-1.5 rounded text-sm font-medium transition-all duration-300',
                                    selectedLayout === 'horizontal'
                                        ? 'bg-white text-primary-600 shadow'
                                        : 'text-gray-600 hover:text-gray-900'
                                )}
                            >
                                横向
                            </button>
                            <button
                                onClick={() => handleLayoutChange('vertical')}
                                className={clsx(
                                    'px-3 py-1.5 rounded text-sm font-medium transition-all duration-300',
                                    selectedLayout === 'vertical'
                                        ? 'bg-white text-primary-600 shadow'
                                        : 'text-gray-600 hover:text-gray-900'
                                )}
                            >
                                纵向
                            </button>
                            <button
                                onClick={() => handleLayoutChange('circular')}
                                className={clsx(
                                    'px-3 py-1.5 rounded text-sm font-medium transition-all duration-300',
                                    selectedLayout === 'circular'
                                        ? 'bg-white text-primary-600 shadow'
                                        : 'text-gray-600 hover:text-gray-900'
                                )}
                            >
                                环形
                            </button>
                        </div>

                        {/* Mini Map Toggle */}
                        <button
                            onClick={() => setShowMiniMap(!showMiniMap)}
                            className={clsx(
                                'p-2 rounded-lg transition-all duration-300',
                                showMiniMap
                                    ? 'bg-primary-100 text-primary-600'
                                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                            )}
                            title="切换小地图"
                        >
                            <FiMaximize className="w-5 h-5" />
                        </button>

                        {/* Refresh */}
                        <button
                            onClick={() => refetch()}
                            className="p-2 rounded-lg bg-gray-100 text-gray-600 hover:bg-gray-200 transition-all duration-300"
                            title="刷新图谱"
                        >
                            <FiRefreshCw className="w-5 h-5" />
                        </button>

                        {/* Export */}
                        <button
                            onClick={handleExport}
                            className="px-4 py-2 bg-gradient-to-r from-primary-600 to-accent-600 text-white rounded-lg hover:shadow-lg transition-all duration-300 flex items-center gap-2"
                        >
                            <FiDownload className="w-4 h-4" />
                            导出
                        </button>
                    </div>
                </div>
            </div>

            {/* Graph Canvas */}
            <div className="flex-1 relative">
                {graphData && graphData.nodes && graphData.nodes.length > 0 ? (
                    <ReactFlow
                        nodes={nodes}
                        edges={edges}
                        onNodesChange={onNodesChange}
                        onEdgesChange={onEdgesChange}
                        onConnect={onConnect}
                        nodeTypes={nodeTypes}
                        fitView
                        attributionPosition="bottom-left"
                    >
                        <Background
                            variant={BackgroundVariant.Dots}
                            gap={20}
                            size={1}
                            color="#e5e7eb"
                        />
                        <Controls />
                        {showMiniMap && (
                            <MiniMap
                                nodeColor={(node: Node) => {
                                    if (node.type === 'document') return '#6366f1';
                                    return '#e5e7eb';
                                }}
                                maskColor="rgba(0, 0, 0, 0.1)"
                            />
                        )}
                    </ReactFlow>
                ) : (
                    <div className="flex items-center justify-center h-full">
                        <div className="text-center">
                            <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-gray-100 flex items-center justify-center">
                                <span className="text-4xl">🕸️</span>
                            </div>
                            <h3 className="text-xl font-semibold text-gray-900 mb-2">
                                暂无知识图谱数据
                            </h3>
                            <p className="text-gray-600 mb-4">
                                上传文档后将自动生成知识图谱
                            </p>
                            <button
                                onClick={() => window.location.href = '/upload'}
                                className="px-6 py-3 bg-gradient-to-r from-primary-600 to-accent-600 text-white rounded-xl hover:shadow-lg transition-all duration-300"
                            >
                                上传文档
                            </button>
                        </div>
                    </div>
                )}
            </div>

            {/* Stats Footer */}
            {graphData && graphData.nodes && graphData.nodes.length > 0 && (
                <div className="bg-white border-t border-gray-200 px-6 py-3">
                    <div className="flex items-center justify-between text-sm text-gray-600">
                        <div className="flex items-center gap-6">
                            <span>📄 {nodes.length} 个节点</span>
                            <span>🔗 {edges.length} 条连接</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="w-3 h-3 rounded-full bg-primary-500"></span>
                            <span>文档节点</span>
                            <span className="w-3 h-3 rounded-full bg-white border-2 border-primary-200 ml-4"></span>
                            <span>实体节点</span>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

// Helper function to calculate node positions based on layout
function calculateNodePosition(index: number, total: number, layout: 'horizontal' | 'vertical' | 'circular') {
    const spacing = 250;
    const centerX = 400;
    const centerY = 300;

    switch (layout) {
        case 'horizontal':
            return {
                x: (index % 5) * spacing,
                y: Math.floor(index / 5) * spacing,
            };
        case 'vertical':
            return {
                x: Math.floor(index / 5) * spacing,
                y: (index % 5) * spacing,
            };
        case 'circular':
            const angle = (index / total) * 2 * Math.PI;
            const radius = 300;
            return {
                x: centerX + radius * Math.cos(angle),
                y: centerY + radius * Math.sin(angle),
            };
        default:
            return { x: 0, y: 0 };
    }
}
