import React, { useState, useEffect } from 'react';
import { Bell, X, Check, AlertTriangle, Zap, Clock } from 'lucide-react';

export const NotificationCenter = () => {
  const [notifications, setNotifications] = useState([]);
  const [showPanel, setShowPanel] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    // WebSocketで通知を受信
    const ws = new WebSocket('wss://tree-router.exe.xyz:8000/api/ws');
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'notification') {
          addNotification(data.payload);
        } else if (data.type === 'high_prob_race') {
          addNotification({
            id: Date.now(),
            type: 'high_prob',
            title: '🚨 高確率レース検出',
            message: `${data.payload.venue} ${data.payload.race}R - 予測確率 ${(data.payload.probability * 100).toFixed(1)}%`,
            timestamp: new Date().toISOString(),
            read: false,
            data: data.payload
          });
        } else if (data.type === 'race_result') {
          addNotification({
            id: Date.now(),
            type: 'result',
            title: '🏁 レース結果',
            message: `${data.payload.venue} ${data.payload.race}R - ${data.payload.result}`,
            timestamp: new Date().toISOString(),
            read: false,
            data: data.payload
          });
        }
      } catch (e) {
        console.error('Failed to parse notification', e);
      }
    };

    ws.onerror = () => console.log('WebSocket error');
    ws.onclose = () => console.log('WebSocket closed');

    return () => ws.close();
  }, []);

  useEffect(() => {
    setUnreadCount(notifications.filter(n => !n.read).length);
  }, [notifications]);

  const addNotification = (notification) => {
    setNotifications(prev => [notification, ...prev].slice(0, 50));
    
    // ブラウザ通知を表示
    if (Notification.permission === 'granted') {
      new Notification(notification.title, {
        body: notification.message,
        icon: '/icon-192.png'
      });
    }
  };

  const markAsRead = (id) => {
    setNotifications(prev => prev.map(n => 
      n.id === id ? { ...n, read: true } : n
    ));
  };

  const markAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
  };

  const clearAll = () => {
    setNotifications([]);
  };

  const requestPermission = () => {
    if ('Notification' in window) {
      Notification.requestPermission();
    }
  };

  const getIcon = (type) => {
    switch (type) {
      case 'high_prob': return <Zap size={16} color="var(--warning)" />;
      case 'result': return <Check size={16} color="var(--success)" />;
      case 'alert': return <AlertTriangle size={16} color="var(--danger)" />;
      default: return <Bell size={16} />;
    }
  };

  return (
    <>
      {/* 通知ボタン */}
      <button
        onClick={() => setShowPanel(!showPanel)}
        style={{
          position: 'relative',
          padding: '0.5rem',
          background: 'rgba(255,255,255,0.05)',
          border: 'none',
          borderRadius: '8px',
          cursor: 'pointer'
        }}
      >
        <Bell size={20} />
        {unreadCount > 0 && (
          <span style={{
            position: 'absolute', top: '-4px', right: '-4px',
            width: '18px', height: '18px', borderRadius: '50%',
            background: 'var(--danger)',
            color: '#fff', fontSize: '0.7rem',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontWeight: '700'
          }}>
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {/* 通知パネル */}
      {showPanel && (
        <div style={{
          position: 'absolute', top: '100%', right: 0, marginTop: '0.5rem',
          width: '360px', maxHeight: '500px',
          background: 'var(--card-bg)', borderRadius: '12px',
          border: '1px solid var(--glass-border)',
          boxShadow: '0 10px 40px rgba(0,0,0,0.5)',
          overflow: 'hidden', zIndex: 1000
        }}>
          <div style={{
            padding: '1rem', borderBottom: '1px solid var(--glass-border)',
            display: 'flex', justifyContent: 'space-between', alignItems: 'center'
          }}>
            <span style={{ fontWeight: '700' }}>通知</span>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button onClick={markAllAsRead} style={{ background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', fontSize: '0.75rem' }}>
                全て既読
              </button>
              <button onClick={clearAll} style={{ background: 'none', border: 'none', color: 'var(--text-dim)', cursor: 'pointer', fontSize: '0.75rem' }}>
                クリア
              </button>
              <button onClick={() => setShowPanel(false)} style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
                <X size={18} />
              </button>
            </div>
          </div>

          <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
            {notifications.length === 0 ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-dim)' }}>
                <Bell size={32} style={{ opacity: 0.3, marginBottom: '0.5rem' }} />
                <p>通知はありません</p>
              </div>
            ) : (
              notifications.map(n => (
                <div
                  key={n.id}
                  onClick={() => markAsRead(n.id)}
                  style={{
                    padding: '1rem',
                    borderBottom: '1px solid var(--glass-border)',
                    background: n.read ? 'transparent' : 'rgba(0,242,255,0.05)',
                    cursor: 'pointer',
                    transition: 'background 0.2s'
                  }}
                >
                  <div style={{ display: 'flex', gap: '0.75rem' }}>
                    <div style={{ flexShrink: 0, marginTop: '0.25rem' }}>
                      {getIcon(n.type)}
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: '600', marginBottom: '0.25rem' }}>{n.title}</div>
                      <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>{n.message}</div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', marginTop: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                        <Clock size={12} />
                        {new Date(n.timestamp).toLocaleTimeString('ja-JP')}
                      </div>
                    </div>
                    {!n.read && (
                      <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--primary)', flexShrink: 0 }} />
                    )}
                  </div>
                </div>
              ))
            )}
          </div>

          {'Notification' in window && Notification.permission !== 'granted' && (
            <div style={{ padding: '1rem', borderTop: '1px solid var(--glass-border)' }}>
              <button
                onClick={requestPermission}
                className="btn-primary"
                style={{ width: '100%', fontSize: '0.875rem' }}
              >
                ブラウザ通知を有効にする
              </button>
            </div>
          )}
        </div>
      )}
    </>
  );
};

export default NotificationCenter;
