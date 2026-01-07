/**
 * Custom hooks for API calls
 */
import { useState, useEffect, useCallback } from 'react';
import api from '../utils/api';

/**
 * Generic fetch hook with loading and error states
 */
export function useFetch(fetchFn, deps = []) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchFn();
      setData(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, deps);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { data, loading, error, refetch };
}

/**
 * Status hook
 */
export function useStatus() {
  return useFetch(() => api.getStatus(), []);
}

/**
 * Stadiums hook
 */
export function useStadiums() {
  return useFetch(() => api.getStadiums(), []);
}

/**
 * Today's races hook with auto-refresh
 */
export function useTodayRaces(refreshInterval = 120000) {
  const { data, loading, error, refetch } = useFetch(() => api.getTodayRaces(), []);

  useEffect(() => {
    const interval = setInterval(refetch, refreshInterval);
    return () => clearInterval(interval);
  }, [refetch, refreshInterval]);

  return { races: data?.races || [], meta: data?.meta, loading, error, refetch };
}

/**
 * Prediction hook
 */
export function usePrediction(date, jyo, race) {
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchPrediction = useCallback(async () => {
    if (!date || !jyo || !race) return;
    
    setLoading(true);
    setError(null);
    try {
      const result = await api.getPrediction(date, jyo, race);
      setPrediction(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [date, jyo, race]);

  useEffect(() => {
    fetchPrediction();
  }, [fetchPrediction]);

  return { prediction, loading, error, refetch: fetchPrediction };
}

/**
 * Portfolio hook
 */
export function usePortfolio() {
  return useFetch(() => api.getPortfolio(), []);
}

/**
 * Strategies hook
 */
export function useStrategies() {
  return useFetch(() => api.getStrategies(), []);
}

/**
 * Simulation hook
 */
export function useSimulation(threshold = 0.4) {
  return useFetch(() => api.getSimulation(threshold), [threshold]);
}

/**
 * Racer stats hook
 */
export function useRacerStats(racerId, nRaces = 10) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetch = useCallback(async () => {
    if (!racerId) return;
    
    setLoading(true);
    setError(null);
    try {
      const result = await api.getRacerStats(racerId, nRaces);
      setStats(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [racerId, nRaces]);

  return { stats, loading, error, fetch };
}

/**
 * WebSocket hook for real-time updates
 */
export function useWebSocket(onMessage) {
  const [connected, setConnected] = useState(false);
  const [ws, setWs] = useState(null);

  useEffect(() => {
    const wsUrl = `ws://${window.location.hostname}:8000/ws`;
    const socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      setConnected(true);
      console.log('WebSocket connected');
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage?.(data);
      } catch (err) {
        console.error('WebSocket message error:', err);
      }
    };

    socket.onclose = () => {
      setConnected(false);
      console.log('WebSocket disconnected');
    };

    socket.onerror = (err) => {
      console.error('WebSocket error:', err);
    };

    setWs(socket);

    return () => {
      socket.close();
    };
  }, [onMessage]);

  return { connected, ws };
}

export default {
  useFetch,
  useStatus,
  useStadiums,
  useTodayRaces,
  usePrediction,
  usePortfolio,
  useStrategies,
  useSimulation,
  useRacerStats,
  useWebSocket,
};
