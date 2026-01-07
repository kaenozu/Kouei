import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  Activity, 
  TrendingUp, 
  AlertCircle, 
  CheckCircle, 
  Cpu, 
  HardDrive, 
  Brain,
  Timer,
  Zap,
  Users
} from 'lucide-react';

const RealtimeDashboard = () => {
  const [systemStatus, setSystemStatus] = useState({});
  const [predictionMetrics, setPredictionMetrics] = useState({});
  const [modelHealth, setModelHealth] = useState({});
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  useEffect(() => {
    const interval = setInterval(() => {
      fetchSystemStatus();
      fetchPredictionMetrics();
      fetchModelHealth();
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const fetchSystemStatus = async () => {
    try {
      const response = await fetch('/api/v1/monitoring/system-status');
      const data = await response.json();
      setSystemStatus(data);
    } catch (error) {
      console.error('Error fetching system status:', error);
    }
  };

  const fetchPredictionMetrics = async () => {
    try {
      const response = await fetch('/api/v1/monitoring/prediction-metrics');
      const data = await response.json();
      setPredictionMetrics(data);
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Error fetching prediction metrics:', error);
    }
  };

  const fetchModelHealth = async () => {
    try {
      const response = await fetch('/api/v1/monitoring/model-health');
      const data = await response.json();
      setModelHealth(data);
    } catch (error) {
      console.error('Error fetching model health:', error);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return 'text-green-500';
      case 'warning': return 'text-yellow-500';
      case 'critical': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy': return <CheckCircle className="w-4 h-4" />;
      case 'warning': return <AlertCircle className="w-4 h-4" />;
      case 'critical': return <AlertCircle className="w-4 h-4" />;
      default: return <Activity className="w-4 h-4" />;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">リアルタイム監視ダッシュボード</h2>
        <div className="flex items-center gap-2">
          <Badge className={isConnected ? 'bg-green-500' : 'bg-gray-500'}>
            {isConnected ? '接続中' : '未接続'}
          </Badge>
          <span className="text-sm text-gray-500">
            最終更新: {lastUpdate.toLocaleTimeString()}
          </span>
        </div>
      </div>

      {/* System Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">CPU使用率</p>
                <p className="text-2xl font-bold">{systemStatus.cpu_usage?.toFixed(1)}%</p>
              </div>
              <Cpu className="w-8 h-8 text-blue-500" />
            </div>
            <Progress 
              value={systemStatus.cpu_usage} 
              className="mt-2"
            />
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">メモリ使用率</p>
                <p className="text-2xl font-bold">{systemStatus.memory_usage?.toFixed(1)}%</p>
              </div>
              <Brain className="w-8 h-8 text-purple-500" />
            </div>
            <Progress 
              value={systemStatus.memory_usage} 
              className="mt-2"
            />
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">本日の予測数</p>
                <p className="text-2xl font-bold">{predictionMetrics.total_predictions || 0}</p>
              </div>
              <Activity className="w-8 h-8 text-green-500" />
            </div>
            <div className="flex items-center gap-2 mt-2">
              <Timer className="w-4 h-4 text-gray-400" />
              <span className="text-xs text-gray-500">
                平均処理時間: {predictionMetrics.avg_processing_time_ms?.toFixed(0)}ms
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">モデル精度</p>
                <p className="text-2xl font-bold">
                  {((predictionMetrics.model_accuracy || 0) * 100).toFixed(1)}%
                </p>
              </div>
              <TrendingUp className="w-8 h-8 text-orange-500" />
            </div>
            <div className="flex items-center gap-2 mt-2">
              <Zap className="w-4 h-4 text-gray-400" />
              <span className="text-xs text-gray-500">
                高信頼度: {predictionMetrics.high_confidence_count || 0}
              </span>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Model Health */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="w-5 h-5" />
              モ健全性チェック
            </CardTitle>
            <CardDescription>
              各モデルのステータスと性能
            </CardDescription>
          </CardHeader>
          <CardContent>
            {modelHealth.models ? (
              <div className="space-y-3">
                {Object.entries(modelHealth.models).map(([model_name, data]) => (
                  <div key={model_name} className="flex items-center justify-between p-3 border rounded">
                    <div className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${
                        data.status === 'healthy' ? 'bg-green-500' : 
                        data.status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
                      }`} />
                      <span className="font-medium capitalize">{model_name}</span>
                      {data.status && (
                        <Badge variant={data.status === 'healthy' ? 'default' : 'destructive'}>
                          {data.status === 'healthy' ? '正常' : '警告'}
                        </Badge>
                      )}
                    </div>
                    {data.auc_score && (
                      <div className="text-sm text-gray-600">
                        AUC: {data.auc_score.toFixed(3)}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center text-gray-500 py-8">
                <HardDrive className="w-8 h-8 mx-auto mb-2" />
                <p>読み込み中...</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Activity */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="w-5 h-5" />
              最新アクティビティ
            </CardTitle>
            <CardDescription>
              システムの最近のアクティビティログ
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-sm">
              <div className="flex items-center gap-2 text-gray-600">
                <CheckCircle className="w-4 h-4 text-green-500" />
                <span>モデル予測完了 - {new Date().toLocaleTimeString()}</span>
              </div>
              <div className="flex items-center gap-2 text-gray-600">
                <Activity className="w-4 h-4 text-blue-500" />
                <span>データ同期中 - {new Date(Date.now() - 60000).toLocaleTimeString()}</span>
              </div>
              <div className="flex items-center gap-2 text-gray-600">
                <Brain className="w-4 h-4 text-purple-500" />
                <span>モデル精度チェック - {new Date(Date.now() - 180000).toLocaleTimeString()}</span>
              </div>
              <div className="flex items-center gap-2 text-gray-600">
                <Users className="w-4 h-4 text-orange-500" />
                <span>ユーザーアクセス - {new Date(Date.now() - 300000).toLocaleTimeString()}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* System Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="w-5 h-5" />
            システム概要
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-500">
                {systemStatus.active_models || 5}
              </div>
              <div className="text-sm text-gray-600">アクティブモデル</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-500">
                {predictionMetrics.total_predictions || 0}
              </div>
              <div className="text-sm text-gray-600">本日予測数</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-500">
                {predictionMetrics.avg_predicted_prob?.toFixed(3) || '0.000'}
              </div>
              <div className="text-sm text-gray-600">平均確率</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-500">
                {systemStatus.disk_usage?.toFixed(1) || '0.0'}%
              </div>
              <div className="text-sm text-gray-600">ディスク使用率</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default RealtimeDashboard;