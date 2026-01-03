import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const SmartBettingDashboard = () => {
  const [bets, setBets] = useState([]);
  const [accuracyStats, setAccuracyStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);

  useEffect(() => {
    fetchSmartBets();
    fetchAccuracyStats();
    
    // データ更新間隔
    const interval = setInterval(() => {
      fetchSmartBets();
    }, 30000); // 30秒ごと
    
    return () => clearInterval(interval);
  }, [selectedDate]);

  const fetchSmartBets = async () => {
    try {
      const date = new Date().toISOString().slice(0, 10).replace(/-/g, '');
      const response = await fetch(`/api/smart-bets?date=${date}`);
      const data = await response.json();
      setBets(data.bets || []);
    } catch (error) {
      console.error('Failed to fetch smart bets:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAccuracyStats = async () => {
    try {
      const response = await fetch('/api/monitoring/accuracy-stats?days=30');
      const data = await response.json();
      setAccuracyStats(data);
    } catch (error) {
      console.error('Failed to fetch accuracy stats:', error);
    }
  };

  const getConfidenceColor = (confidence) => {
    const colors = {
      'S': '#ef4444',
      'A': '#f97316', 
      'B': '#eab308',
      'C': '#22c55e'
    };
    return colors[confidence] || '#6b7280';
  };

  const getStatusColor = (status) => {
    const colors = {
      'upcoming': '#3b82f6',
      'scheduled': '#6b7280',
      'live': '#f59e0b',
      'finished': '#9ca3af'
    };
    return colors[status] || '#6b7280';
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* ヘッダー */}
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">AIスマートベッティング</h1>
        <p className="text-gray-600">高確率レース予測と最適な買い目提案</p>
      </div>

      {/* 精度統計 */}
      {accuracyStats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-600 mb-1">的中率</div>
            <div className="text-2xl font-bold text-green-600">
              {accuracyStats.overall_hit_rate?.toFixed(1) || 0}%
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-600 mb-1">ROI</div>
            <div className="text-2xl font-bold text-blue-600">
              {accuracyStats.overall_roi?.toFixed(1) || 0}%
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-600 mb-1">本日の推奦</div>
            <div className="text-2xl font-bold text-purple-600">{bets.length}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-600 mb-1">平均確率</div>
            <div className="text-2xl font-bold text-red-600">
              {bets.length > 0 ? (bets.reduce((sum, bet) => sum + bet.probability, 0) / bets.length * 100).toFixed(1) : 0}%
            </div>
          </div>
        </div>
      )}

      {/* 推奨レース一覧 */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">推奨レース一覧</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  レース
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  艇番
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  選手名
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  確率
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  確信度
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  予想オッズ
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  EV
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  状態
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {bets.map((bet, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {bet.jyo_name} {bet.race_no}R
                    </div>
                    <div className="text-xs text-gray-500">
                      {bet.start_time}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-bold text-gray-900">{bet.boat_no}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{bet.racer_name}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-bold text-gray-900">
                      {(bet.probability * 100).toFixed(1)}%
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span 
                      className="px-2 py-1 text-xs font-semibold rounded-full text-white"
                      style={{ backgroundColor: getConfidenceColor(bet.confidence) }}
                    >
                      {bet.confidence}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {bet.expected_odds?.toFixed(1) || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-bold text-green-600">
                      {bet.ev?.toFixed(2) || '-'}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span 
                      className="px-2 py-1 text-xs font-semibold rounded-full text-white"
                      style={{ backgroundColor: getStatusColor(bet.status) }}
                    >
                      {bet.status === 'upcoming' ? '間際' : 
                       bet.status === 'live' ? 'レース中' : 
                       bet.status === 'scheduled' ? '予定' : '終了'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {bets.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              本日の推奨レースはありません
            </div>
          )}
        </div>
      </div>

      {/* 確信度別精度 */}
      {accuracyStats?.confidence_stats && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">確信度別精度</h2>
          </div>
          <div className="p-6">
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={accuracyStats.confidence_stats}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="confidence_level" />
                <YAxis />
                <Tooltip formatter={(value) => `${value}%`} />
                <Legend />
                <Bar dataKey="correct" fill="#3b82f6" name="的中数" />
                <Bar dataKey="total" fill="#e5e7eb" name="合計数" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
};

export default SmartBettingDashboard;
