import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';

export type PerformanceMode = 'high' | 'balanced' | 'low';

interface PerformanceContextValue {
  performanceMode: PerformanceMode;
  setPerformanceMode: (mode: PerformanceMode) => void;
  isReducedMotion: boolean;
  deviceCapabilities: {
    isMobile: boolean;
    isLowEndDevice: boolean;
    supportsAdvancedEffects: boolean;
  };
}

const PerformanceContext = createContext<PerformanceContextValue | undefined>(undefined);

interface PerformanceProviderProps {
  children: React.ReactNode;
  initialMode?: PerformanceMode;
}

export const PerformanceProvider: React.FC<PerformanceProviderProps> = ({
  children,
  initialMode = 'balanced',
}) => {
  const [performanceMode, setPerformanceMode] = useState<PerformanceMode>(initialMode);
  const [isReducedMotion, setIsReducedMotion] = useState(false);
  const [deviceCapabilities, setDeviceCapabilities] = useState({
    isMobile: false,
    isLowEndDevice: false,
    supportsAdvancedEffects: true,
  });

  // Detect device capabilities and preferences
  useEffect(() => {
    // Check for reduced motion preference
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setIsReducedMotion(mediaQuery.matches);
    
    const handleChange = (e: MediaQueryListEvent) => {
      setIsReducedMotion(e.matches);
    };
    
    mediaQuery.addEventListener('change', handleChange);

    // Detect device capabilities
    const userAgent = navigator.userAgent.toLowerCase();
    const isMobile = /mobile|android|ios|iphone|ipad/.test(userAgent);
    
    // Rough heuristics for low-end devices
    const isLowEndDevice = 
      navigator.hardwareConcurrency <= 2 ||
      (performance as any).memory?.usedJSHeapSize > 50 * 1024 * 1024 ||
      /android.*version\/[1-4]\./.test(userAgent);
    
    // Check for advanced effect support
    const supportsAdvancedEffects = 
      'CSS' in window &&
      'supports' in CSS &&
      CSS.supports('backdrop-filter', 'blur(10px)') &&
      CSS.supports('filter', 'blur(10px)');

    setDeviceCapabilities({
      isMobile,
      isLowEndDevice,
      supportsAdvancedEffects,
    });

    // Auto-adjust performance mode based on device
    if (isLowEndDevice && initialMode === 'high') {
      setPerformanceMode('balanced');
    } else if (isMobile && initialMode === 'high') {
      setPerformanceMode('balanced');
    }

    return () => {
      mediaQuery.removeEventListener('change', handleChange);
    };
  }, [initialMode]);

  // Smart performance mode adjustment
  const setPerformanceModeWithFallback = useCallback((mode: PerformanceMode) => {
    // Don't allow high performance on low-end devices
    if (mode === 'high' && deviceCapabilities.isLowEndDevice) {
      setPerformanceMode('balanced');
      return;
    }

    // Don't allow advanced effects if not supported
    if (mode === 'high' && !deviceCapabilities.supportsAdvancedEffects) {
      setPerformanceMode('balanced');
      return;
    }

    setPerformanceMode(mode);
  }, [deviceCapabilities]);

  const value: PerformanceContextValue = {
    performanceMode,
    setPerformanceMode: setPerformanceModeWithFallback,
    isReducedMotion,
    deviceCapabilities,
  };

  return (
    <PerformanceContext.Provider value={value}>
      {children}
    </PerformanceContext.Provider>
  );
};

export const usePerformance = (): PerformanceContextValue => {
  const context = useContext(PerformanceContext);
  if (!context) {
    throw new Error('usePerformance must be used within a PerformanceProvider');
  }
  return context;
};