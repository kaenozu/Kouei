import { useState, useEffect, useCallback } from 'react';

const API_BASE = 'http://localhost:8001';

export function usePushNotifications() {
  const [permission, setPermission] = useState('default');
  const [subscription, setSubscription] = useState(null);
  const [supported, setSupported] = useState(false);

  useEffect(() => {
    // Check if push notifications are supported
    const isSupported = 'Notification' in window && 
                        'serviceWorker' in navigator && 
                        'PushManager' in window;
    setSupported(isSupported);
    
    if (isSupported) {
      setPermission(Notification.permission);
    }
  }, []);

  const requestPermission = useCallback(async () => {
    if (!supported) return false;
    
    try {
      const result = await Notification.requestPermission();
      setPermission(result);
      return result === 'granted';
    } catch (error) {
      console.error('Permission request failed:', error);
      return false;
    }
  }, [supported]);

  const subscribe = useCallback(async () => {
    if (permission !== 'granted') {
      const granted = await requestPermission();
      if (!granted) return null;
    }

    try {
      const registration = await navigator.serviceWorker.ready;
      
      // In production, you'd use your VAPID public key
      const sub = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: null // Would need VAPID key for real push
      });
      
      setSubscription(sub);
      return sub;
    } catch (error) {
      console.error('Subscription failed:', error);
      return null;
    }
  }, [permission, requestPermission]);

  const showLocalNotification = useCallback(async (title, options = {}) => {
    if (permission !== 'granted') {
      const granted = await requestPermission();
      if (!granted) return false;
    }

    try {
      const registration = await navigator.serviceWorker.ready;
      await registration.showNotification(title, {
        icon: '/icon-192.svg',
        badge: '/badge-72.svg',
        vibrate: [200, 100, 200],
        ...options
      });
      return true;
    } catch (error) {
      console.error('Notification failed:', error);
      return false;
    }
  }, [permission, requestPermission]);

  return {
    supported,
    permission,
    subscription,
    requestPermission,
    subscribe,
    showLocalNotification
  };
}

export default usePushNotifications;
