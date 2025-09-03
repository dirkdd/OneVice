import React, { useEffect, useState, useRef } from 'react';

interface PerformanceMetrics {
  fps: number;
  frameTime: number;
  memoryUsage: number;
  animationCount: number;
  isOptimal: boolean;
}

interface AnimationMonitorProps {
  children: React.ReactNode;
  enableMonitoring?: boolean;
  performanceTarget?: 'high' | 'balanced' | 'low';
  onPerformanceChange?: (mode: 'high' | 'balanced' | 'low') => void;
}

export const AnimationMonitor: React.FC<AnimationMonitorProps> = ({
  children,
  enableMonitoring = process.env.NODE_ENV === 'development',
  performanceTarget = 'balanced',
  onPerformanceChange,
}) => {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    fps: 60,
    frameTime: 16.67,
    memoryUsage: 0,
    animationCount: 0,
    isOptimal: true,
  });

  const frameCountRef = useRef(0);
  const lastTimeRef = useRef(performance.now());
  const rafIdRef = useRef<number>();
  const metricsHistory = useRef<number[]>([]);

  useEffect(() => {
    if (!enableMonitoring) return;

    const measurePerformance = () => {
      const now = performance.now();
      const deltaTime = now - lastTimeRef.current;
      
      frameCountRef.current++;
      
      if (deltaTime >= 1000) {
        const currentFps = (frameCountRef.current * 1000) / deltaTime;
        const frameTime = 1000 / currentFps;
        
        // Track FPS history for trend analysis
        metricsHistory.current.push(currentFps);
        if (metricsHistory.current.length > 10) {
          metricsHistory.current.shift();
        }
        
        // Calculate average FPS over last 10 frames
        const avgFps = metricsHistory.current.reduce((a, b) => a + b, 0) / metricsHistory.current.length;
        
        // Get memory usage if available
        const memoryUsage = (performance as any).memory?.usedJSHeapSize || 0;
        
        // Count active animations (estimate based on RAF calls)
        const animationCount = Math.floor(currentFps / 60 * 10); // Rough estimate
        
        const newMetrics: PerformanceMetrics = {
          fps: Math.round(avgFps),
          frameTime: Math.round(frameTime * 100) / 100,
          memoryUsage: Math.round(memoryUsage / 1024 / 1024),
          animationCount,
          isOptimal: avgFps >= 55, // Consider >55fps as optimal
        };
        
        setMetrics(newMetrics);
        
        // Auto-adjust performance mode based on FPS
        if (onPerformanceChange) {
          if (avgFps < 30 && performanceTarget !== 'low') {
            onPerformanceChange('low');
          } else if (avgFps < 45 && performanceTarget === 'high') {
            onPerformanceChange('balanced');
          } else if (avgFps >= 55 && performanceTarget === 'low') {
            onPerformanceChange('balanced');
          }
        }
        
        frameCountRef.current = 0;
        lastTimeRef.current = now;
      }
      
      rafIdRef.current = requestAnimationFrame(measurePerformance);
    };

    rafIdRef.current = requestAnimationFrame(measurePerformance);

    return () => {
      if (rafIdRef.current) {
        cancelAnimationFrame(rafIdRef.current);
      }
    };
  }, [enableMonitoring, performanceTarget, onPerformanceChange]);

  // Performance warning overlay (development only)
  const showWarning = enableMonitoring && !metrics.isOptimal;

  return (
    <>
      {children}
      {showWarning && (
        <div className="fixed top-4 right-4 z-50 bg-yellow-500/90 text-black px-3 py-2 rounded-lg text-sm font-mono">
          <div>FPS: {metrics.fps}</div>
          <div>Frame: {metrics.frameTime}ms</div>
          {metrics.memoryUsage > 0 && <div>RAM: {metrics.memoryUsage}MB</div>}
          <div className="text-xs mt-1">
            {metrics.fps < 30 ? '🔴 Poor' : metrics.fps < 45 ? '🟡 Fair' : '🟢 Good'}
          </div>
        </div>
      )}
    </>
  );
};