import { useState, useEffect, useCallback } from 'react';

const useWebSocketNotification = (url) => {
  const [socket, setSocket] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const wsUrl = url || `ws://localhost:8001/ws/notifications`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setConnected(true);
      setSocket(ws);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'notification') {
          setNotifications(prev => [data, ...prev].slice(0, 100)); // 最新100件保持
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setConnected(false);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnected(false);
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [url]);

  const sendNotification = useCallback((data) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(data));
    } else {
      console.warn('WebSocket not connected');
    }
  }, [socket]);

  const clearNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  const markAsRead = useCallback((id) => {
    setNotifications(prev => 
      prev.map(n => n.id === id ? { ...n, read: true } : n)
    );
  }, []);

  return {
    notifications,
    connected,
    sendNotification,
    clearNotifications,
    markAsRead
  };
};

export default useWebSocketNotification;
