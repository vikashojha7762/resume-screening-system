import { useEffect } from 'react';
import { websocketService } from '../services/websocket';
import { useAppSelector } from '../store/hooks';

export const useWebSocket = (event: string, callback: (data: any) => void) => {
  const { token } = useAppSelector((state) => state.auth);

  useEffect(() => {
    if (token) {
      websocketService.connect(token);
      const unsubscribe = websocketService.on(event, callback);

      return () => {
        unsubscribe();
      };
    }
  }, [token, event, callback]);
};

export const useResumeProcessingUpdates = (callback: (data: any) => void) => {
  useWebSocket('resume_processed', callback);
};

export const useMatchUpdates = (callback: (data: any) => void) => {
  useWebSocket('match_completed', callback);
};

