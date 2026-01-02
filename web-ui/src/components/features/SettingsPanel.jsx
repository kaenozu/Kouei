import React, { useState } from 'react';
import { Settings, Bell, Database, Palette, Shield } from 'lucide-react';

export const SettingsPanel = () => {
  const [settings, setSettings] = useState({
    notifications: {
      highProbRaces: true,
      strategyAlerts: true,
      raceResults: false
    },
    model: {
      useOnnx: true,
      confidenceThreshold: 0.4
    },
    display: {
      darkMode: true,
      compactView: false
    }
  });

  const updateSetting = (category, key, value) => {
    setSettings(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [key]: value
      }
    }));
  };

  return (
    <div style={{ padding: '1rem', maxWidth: '800px', margin: '0 auto' }}>
      <h1 style={{ fontSize: '2.5rem', fontWeight: '900', marginBottom: '0.5rem' }}>
        <Settings style={{ display: 'inline', marginRight: '0.5rem' }} /> 設定
      </h1>
      <p style={{ color: 'var(--text-dim)', marginBottom: '2rem' }}>システム設定</p>

      <div className="card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
        <h3 style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Bell size={20} /> 通知設定
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '1rem', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={settings.notifications.highProbRaces}
              onChange={e => updateSetting('notifications', 'highProbRaces', e.target.checked)}
              style={{ width: '20px', height: '20px' }}
            />
            <span>高確率レース通知を受け取る</span>
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: '1rem', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={settings.notifications.strategyAlerts}
              onChange={e => updateSetting('notifications', 'strategyAlerts', e.target.checked)}
              style={{ width: '20px', height: '20px' }}
            />
            <span>戦略アラートを受け取る</span>
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: '1rem', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={settings.notifications.raceResults}
              onChange={e => updateSetting('notifications', 'raceResults', e.target.checked)}
              style={{ width: '20px', height: '20px' }}
            />
            <span>レース結果通知を受け取る</span>
          </label>
        </div>
      </div>

      <div className="card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
        <h3 style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Database size={20} /> モデル設定
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '1rem', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={settings.model.useOnnx}
              onChange={e => updateSetting('model', 'useOnnx', e.target.checked)}
              style={{ width: '20px', height: '20px' }}
            />
            <span>ONNX推論を使用（高速）</span>
          </label>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem' }}>
              信頼度閾値: {settings.model.confidenceThreshold}
            </label>
            <input
              type="range"
              min="0.1"
              max="0.9"
              step="0.1"
              value={settings.model.confidenceThreshold}
              onChange={e => updateSetting('model', 'confidenceThreshold', parseFloat(e.target.value))}
              style={{ width: '100%' }}
            />
          </div>
        </div>
      </div>

      <div className="card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
        <h3 style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Palette size={20} /> 表示設定
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '1rem', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={settings.display.darkMode}
              onChange={e => updateSetting('display', 'darkMode', e.target.checked)}
              style={{ width: '20px', height: '20px' }}
            />
            <span>ダークモード</span>
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: '1rem', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={settings.display.compactView}
              onChange={e => updateSetting('display', 'compactView', e.target.checked)}
              style={{ width: '20px', height: '20px' }}
            />
            <span>コンパクト表示</span>
          </label>
        </div>
      </div>

      <div className="card" style={{ padding: '1.5rem' }}>
        <h3 style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Shield size={20} /> システム情報
        </h3>
        <div style={{ color: 'var(--text-dim)', fontSize: '0.875rem' }}>
          <p>バージョン: v3.0.0</p>
          <p>モデル: LightGBM + XGBoost + CatBoost Ensemble</p>
          <p>API: FastAPI on port 8001</p>
        </div>
      </div>
    </div>
  );
};

export default SettingsPanel;
