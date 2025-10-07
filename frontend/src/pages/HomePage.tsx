/**
 * HomePage - Modern Dashboard with statistics and recent documents
 */

import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  FiUpload, FiFile, FiClock, FiCheckCircle, FiTrendingUp,
  FiFileText, FiZap, FiArrowRight, FiActivity
} from 'react-icons/fi';
import { apiService } from '../services/api';
import { Spinner, CardSkeleton } from '../components/Loading';

export default function HomePage() {
  const navigate = useNavigate();

  // Fetch documents
  const { data: documents, isLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: () => apiService.getDocuments(),
  });

  const stats = documents ? [
    {
      icon: FiFileText,
      label: '总文档数',
      value: documents.items.length,
      trend: '+12%',
      color: 'from-blue-500 to-cyan-500',
      bgColor: 'bg-blue-50',
      iconColor: 'text-blue-600',
    },
    {
      icon: FiCheckCircle,
      label: '已处理',
      value: documents.items.filter((d: any) => d.status === 'completed').length,
      trend: '+8%',
      color: 'from-green-500 to-emerald-500',
      bgColor: 'bg-green-50',
      iconColor: 'text-green-600',
    },
    {
      icon: FiClock,
      label: '处理中',
      value: documents.items.filter((d: any) => d.status === 'processing').length,
      trend: '-3%',
      color: 'from-orange-500 to-yellow-500',
      bgColor: 'bg-orange-50',
      iconColor: 'text-orange-600',
    },
    {
      icon: FiActivity,
      label: '今日活跃',
      value: documents.items.filter((d: any) => {
        const today = new Date().toDateString();
        return new Date(d.created_at).toDateString() === today;
      }).length,
      trend: '+24%',
      color: 'from-purple-500 to-pink-500',
      bgColor: 'bg-purple-50',
      iconColor: 'text-purple-600',
    },
  ] : [];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-purple-50/30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">

        {/* Hero Section */}
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-primary-600 via-primary-700 to-accent-600 p-8 md:p-12 text-white animate-fade-in">
          <div className="absolute inset-0 bg-grid-white/10 [mask-image:linear-gradient(0deg,white,rgba(255,255,255,0.5))]" />
          <div className="relative z-10 max-w-3xl">
            <h1 className="text-4xl md:text-5xl font-bold mb-4 animate-fade-in-up">
              欢迎来到 IntelliPDF
            </h1>
            <p className="text-lg md:text-xl text-blue-100 mb-8 animate-fade-in-up" style={{ animationDelay: '100ms' }}>
              智能 PDF 知识管理平台，让文档阅读更智能，知识获取更高效
            </p>
            <div className="flex flex-wrap gap-4 animate-fade-in-up" style={{ animationDelay: '200ms' }}>
              <button
                onClick={() => navigate('/upload')}
                className="group flex items-center gap-2 bg-white text-primary-600 px-6 py-3 rounded-xl font-semibold hover:scale-105 hover:shadow-xl transition-all duration-300"
              >
                <FiUpload className="w-5 h-5 group-hover:animate-bounce-soft" />
                上传文档
                <FiArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </button>
              <button
                className="flex items-center gap-2 bg-white/10 backdrop-blur-sm text-white px-6 py-3 rounded-xl font-semibold border border-white/20 hover:bg-white/20 transition-all duration-300"
              >
                <FiZap className="w-5 h-5" />
                快速开始
              </button>
            </div>
          </div>

          {/* Decorative elements */}
          <div className="absolute top-10 right-10 w-32 h-32 bg-white/5 rounded-full blur-3xl animate-pulse-soft" />
          <div className="absolute bottom-10 right-20 w-40 h-40 bg-accent-400/20 rounded-full blur-3xl animate-pulse-soft" style={{ animationDelay: '1s' }} />
        </div>

        {/* Statistics Cards */}
        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <CardSkeleton count={4} />
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {stats.map((stat, index) => (
              <div
                key={index}
                className="group relative overflow-hidden bg-white rounded-2xl shadow-soft hover:shadow-soft-lg transition-all duration-300 hover:-translate-y-1 animate-fade-in-up"
                style={{ animationDelay: `${index * 100}ms` }}
              >
                <div className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className={`p-3 rounded-xl ${stat.bgColor}`}>
                      <stat.icon className={`w-6 h-6 ${stat.iconColor}`} />
                    </div>
                    <span className="flex items-center gap-1 text-sm font-semibold text-green-600">
                      <FiTrendingUp className="w-4 h-4" />
                      {stat.trend}
                    </span>
                  </div>
                  <div className="space-y-1">
                    <p className="text-3xl font-bold text-gray-900">{stat.value}</p>
                    <p className="text-sm text-gray-600">{stat.label}</p>
                  </div>
                </div>
                {/* Gradient overlay on hover */}
                <div className={`absolute inset-0 bg-gradient-to-br ${stat.color} opacity-0 group-hover:opacity-5 transition-opacity duration-300`} />
              </div>
            ))}
          </div>
        )}

        {/* Recent Documents */}
        <div className="space-y-6 animate-fade-in-up" style={{ animationDelay: '400ms' }}>
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-900">最近文档</h2>
            <button className="text-sm font-medium text-primary-600 hover:text-primary-700 transition-colors">
              查看全部
            </button>
          </div>

          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <CardSkeleton count={3} />
            </div>
          ) : documents?.items.length === 0 ? (
            <div className="card-glass text-center py-16">
              <div className="w-20 h-20 mx-auto mb-6 bg-gradient-to-br from-primary-100 to-accent-100 rounded-full flex items-center justify-center">
                <FiFile className="w-10 h-10 text-primary-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">暂无文档</h3>
              <p className="text-gray-600 mb-6">开始上传您的第一个 PDF 文档</p>
              <button
                onClick={() => navigate('/upload')}
                className="inline-flex items-center gap-2 bg-primary-600 text-white px-6 py-3 rounded-xl font-semibold hover:bg-primary-700 transition-colors"
              >
                <FiUpload className="w-5 h-5" />
                立即上传
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {documents?.items.slice(0, 6).map((doc: any, index: number) => (
                <div
                  key={doc.id}
                  className="group card-hover cursor-pointer animate-fade-in-up"
                  style={{ animationDelay: `${index * 50}ms` }}
                  onClick={() => navigate(`/document/${doc.id}`)}
                >
                  <div className="flex items-start gap-4 mb-4">
                    <div className="flex-shrink-0 w-12 h-12 bg-gradient-to-br from-primary-500 to-accent-500 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                      <FiFile className="w-6 h-6 text-white" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-gray-900 truncate mb-1 group-hover:text-primary-600 transition-colors">
                        {doc.filename}
                      </h3>
                      <p className="text-sm text-gray-500">
                        {new Date(doc.created_at).toLocaleDateString('zh-CN')}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-sm">
                    <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium ${doc.status === 'completed'
                        ? 'bg-green-100 text-green-700'
                        : doc.status === 'processing'
                          ? 'bg-yellow-100 text-yellow-700'
                          : 'bg-gray-100 text-gray-700'
                      }`}>
                      {doc.status === 'completed' && <FiCheckCircle className="w-3 h-3" />}
                      {doc.status === 'processing' && <Spinner size="sm" />}
                      {doc.status === 'completed' ? '已完成' :
                        doc.status === 'processing' ? '处理中' : '等待中'}
                    </span>
                    <span className="text-gray-500">
                      {(doc.file_size / 1024 / 1024).toFixed(2)} MB
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
