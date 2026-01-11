import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import * as SecureStore from 'expo-secure-store';

const APPLIED_COUNT_KEY = 'applied_count';

interface AppliedContextType {
  appliedCount: number;
  incrementApplied: () => void;
  resetApplied: () => void;
}

const AppliedContext = createContext<AppliedContextType | undefined>(undefined);

export const AppliedProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [appliedCount, setAppliedCount] = useState(0);

  // Load count from storage on mount
  useEffect(() => {
    loadAppliedCount();
  }, []);

  const loadAppliedCount = async () => {
    try {
      const stored = await SecureStore.getItemAsync(APPLIED_COUNT_KEY);
      if (stored) {
        setAppliedCount(parseInt(stored, 10));
      } else {
        setAppliedCount(0);
      }
    } catch (error) {
      console.error('Error loading applied count:', error);
      setAppliedCount(0);
    }
  };

  const incrementApplied = async () => {
    const newCount = appliedCount + 1;
    setAppliedCount(newCount);
    try {
      await SecureStore.setItemAsync(APPLIED_COUNT_KEY, newCount.toString());
    } catch (error) {
      console.error('Error saving applied count:', error);
    }
  };

  const resetApplied = async () => {
    setAppliedCount(0);
    try {
      await SecureStore.setItemAsync(APPLIED_COUNT_KEY, '0');
    } catch (error) {
      console.error('Error resetting applied count:', error);
    }
  };

  return (
    <AppliedContext.Provider value={{ appliedCount, incrementApplied, resetApplied }}>
      {children}
    </AppliedContext.Provider>
  );
};

export const useApplied = () => {
  const context = useContext(AppliedContext);
  if (context === undefined) {
    throw new Error('useApplied must be used within an AppliedProvider');
  }
  return context;
};
