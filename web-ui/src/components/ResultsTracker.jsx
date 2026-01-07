import React, { useState, useEffect } from 'react';

const API_BASE = '';

export default function ResultsTracker() {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState(null);
  const [dateRange, setDateRange] = useState('today');

  useEffect(() => {
    fetchResults();
  }, [dateRange]);

  const fetchResults = async () => {
    setLoading(true);
    try {
      // Fetch accuracy data
      const res = await fetch(`${API_BASE}/api/accuracy/detailed`);
      if (res.ok) {
        const data = await res.json();
        setResults(data.recent_predictions || []);
        setSummary(data.summary || null);
      }
    } catch (err) {
      console.error('Error fetching results:', err);
    }
    setLoading(false);
  };

  const getResultBadge = (predicted, actual) => {
    if (predicted === actual) {
      return <span className="px-2 py-1 bg-green-500 text-white text-xs rounded">的中</span>;
    }
    return <span className="px-2 py-1 bg-red-500 text-white text-xs rounded">外れ</span>;
  };

  return (
    <div className="bg-gray-900 rounded-xl p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-bold text-white">📋 予測結果追跡</h2>
        <div className="flex gap-2">
          {['today', 'week', 'month'].map(range => (
            <button
              key={range}
              onClick={() => setDateRange(range)}
              className={`px-3 py-1 rounded text-sm ${
                dateRange === range 
                  ? 'bg-cyan-600 text-white' 
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              {range === 'today' ? '今日' : range === 'week' ? '1週間' : '1ヶ月'}
            </button>
          ))}
        </div>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-gray-800 rounded-lg p-4 text-center">
            <div className="text-gray-400 text-sm">総予測数</div>
            <div className="text-2xl font-bold text-white">{summary.total_predictions || 0}</div>
          </div>
          <div className="bg-gray-800 rounded-lg p-4 text-center">
            <div className="text-gray-400 text-sm">的中数</div>
            <div className="text-2xl font-bold text-green-400">{summary.correct_predictions || 0}</div>
          </div>
          <div className="bg-gray-800 rounded-lg p-4 text-center">
            <div className="text-gray-400 text-sm">的中率</div>
            <div className="text-2xl font-bold text-cyan-400">{summary.accuracy?.toFixed(1) || 0}%</div>
          </div>
          <div className="bg-gray-800 rounded-lg p-4 text-center">
            <div className="text-gray-400 text-sm">推定ROI</div>
            <div className={`text-2xl font-bold ${(summary.roi || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {summary.roi?.toFixed(1) || 0}%
            </div>
          </div>
        </div>
      )}

      {/* Results Table */}
      <div className="bg-gray-800 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-700">
            <tr>
              <th className="px-4 py-3 text-left text-gray-300 text-sm">日時</th>
              <th className="px-4 py-3 text-left text-gray-300 text-sm">会場</th>
              <th className="px-4 py-3 text-left text-gray-300 text-sm">R</th>
              <th className="px-4 py-3 text-left text-gray-300 text-sm">予測</th>
              <th className="px-4 py-3 text-left text-gray-300 text-sm">結果</th>
              <th className="px-4 py-3 text-left text-gray-300 text-sm">判定</th>
              <th className="px-4 py-3 text-left text-gray-300 text-sm">信頼度</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-gray-400">
                  読み込み中...
                </td>
              </tr>
            ) : results.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-gray-400">
                  データがありません
                </td>
              </tr>
            ) : (
              results.map((r, idx) => (
                <tr key={idx} className="border-t border-gray-700 hover:bg-gray-750">
                  <td className="px-4 py-3 text-gray-300 text-sm">{r.date}</td>
                  <td className="px-4 py-3 text-white">{r.venue_name}</td>
                  <td className="px-4 py-3 text-white font-bold">{r.race_no}R</td>
                  <td className="px-4 py-3">
                    <span className="text-cyan-400 font-bold">{r.predicted_boat}号艇</span>
                    <span className="text-gray-500 text-sm ml-1">({(r.probability * 100).toFixed(0)}%)</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-yellow-400 font-bold">{r.actual_winner}号艇</span>
                  </td>
                  <td className="px-4 py-3">
                    {getResultBadge(r.predicted_boat, r.actual_winner)}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded text-xs font-bold ${
                      r.confidence === 'S' ? 'bg-yellow-500 text-black' :
                      r.confidence === 'A' ? 'bg-purple-500 text-white' :
                      r.confidence === 'B' ? 'bg-blue-500 text-white' : 'bg-gray-600 text-white'
                    }`}>
                      {r.confidence}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Refresh Button */}
      <div className="mt-4 text-center">
        <button
          onClick={fetchResults}
          disabled={loading}
          className="px-4 py-2 bg-gray-700 text-white rounded hover:bg-gray-600 disabled:opacity-50"
        >
          🔄 更新
        </button>
      </div>
    </div>
  );
}
