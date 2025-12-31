import React, { useState, useEffect } from 'react';
import { Card, Select, Button, Switch, Space } from 'antd';

const DashboardCustomizer = ({ onLayoutChange, savedLayouts = [] }) => {
  const [layout, setLayout] = useState(savedLayouts[0] || 'default');
  const [widgets, setWidgets] = useState({
    races: true,
    predictions: true,
    analytics: true,
    portfolio: true,
    notifications: true,
    weather: false
  });

  const layoutOptions = [
    { value: 'default', label: '標準' },
    { value: 'compact', label: 'コンパクト' },
    { value: 'detailed', label: '詳細' },
    { value: 'mobile', label: 'モバイル用' },
    { value: 'analytics', label: '分析重視' }
  ];

  const widgetCategories = [
    { key: 'races', label: '本日レース', icon: '🏁' },
    { key: 'predictions', label: 'AI予測', icon: '🤖' },
    { key: 'analytics', label: '分析チャート', icon: '📊' },
    { key: 'portfolio', label: 'ポートフォリオ', icon: '💼' },
    { key: 'notifications', label: '通知', icon: '🔔' },
    { key: 'weather', label: '天候情報', icon: '🌤️' }
  ];

  const handleLayoutChange = (newLayout) => {
    setLayout(newLayout);
    onLayoutChange({ layout: newLayout, widgets });
  };

  const handleWidgetToggle = (widgetKey) => {
    const newWidgets = { ...widgets, [widgetKey]: !widgets[widgetKey] };
    setWidgets(newWidgets);
    onLayoutChange({ layout, widgets: newWidgets });
  };

  const saveLayout = () => {
    localStorage.setItem('dashboardLayout', JSON.stringify({ layout, widgets }));
    // APIに保存する処理も追加可能
  };

  useEffect(() => {
    const saved = localStorage.getItem('dashboardLayout');
    if (saved) {
      const { layout: savedLayout, widgets: savedWidgets } = JSON.parse(saved);
      setLayout(savedLayout);
      setWidgets(savedWidgets);
    }
  }, []);

  return (
    <Card title="ダッシュボードカスタマイズ" size="small">
      <Space direction="vertical" style={{ width: '100%' }}>
        <div>
          <label>レイアウト:</label>
          <Select
            value={layout}
            onChange={handleLayoutChange}
            style={{ width: '100%', marginTop: 8 }}
            options={layoutOptions}
          />
        </div>
        
        <div>
          <label>表示ウィジェット:</label>
          <div style={{ marginTop: 8 }}>
            {widgetCategories.map(({ key, label, icon }) => (
              <div key={key} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                <span>{icon} {label}</span>
                <Switch
                  checked={widgets[key]}
                  onChange={() => handleWidgetToggle(key)}
                />
              </div>
            ))}
          </div>
        </div>
        
        <Button type="primary" onClick={saveLayout} style={{ width: '100%' }}>
          設定を保存
        </Button>
      </Space>
    </Card>
  );
};

export default DashboardCustomizer;
