import React from 'react';
import { LayoutDashboard, TrendingUp, BarChart3, Settings, Briefcase, Trophy, Zap, Clock } from 'lucide-react';

const menuItems = [
  { id: 'dashboard', icon: LayoutDashboard, label: 'ダッシュボード' },
  { id: 'race-select', icon: TrendingUp, label: 'レース選択' },
  { id: 'portfolio', icon: Briefcase, label: 'ポートフォリオ' },
  { id: 'today', icon: Clock, label: '本日のレース' },
  { id: 'backtest', icon: BarChart3, label: 'バックテスト・ラボ' },
  { id: 'analytics', icon: TrendingUp, label: '分析ダッシュボード' },
  { id: 'racer-tracker', icon: Trophy, label: '選手追跡' },
  { id: 'high-value', icon: Zap, label: '高確率レース', highlight: true },
  { id: 'tools', icon: Zap, label: 'AI Tools' },
  { id: 'settings', icon: Settings, label: '設定' },
];

export const Sidebar = ({ activeTab, setActiveTab }) => {
  return (
    <aside className="sidebar">
      <div className="logo">
        <h1 style={{ fontSize: '1.5rem', fontWeight: '900', background: 'linear-gradient(135deg, var(--primary), var(--success))', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          AI KYOTEI
        </h1>
      </div>
      <nav className="nav-menu">
        {menuItems.map(item => (
          <div
            key={item.id}
            className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
            onClick={() => setActiveTab(item.id)}
            style={item.highlight ? { background: 'linear-gradient(135deg, rgba(255,107,107,0.2), rgba(255,159,67,0.2))', border: '1px solid rgba(255,107,107,0.3)' } : {}}
          >
            <item.icon size={20} />
            <span>{item.label}</span>
          </div>
        ))}
      </nav>
    </aside>
  );
};

export default Sidebar;
