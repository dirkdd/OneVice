import { useEffect, useRef, useCallback } from 'react';
import { usePerformance, PerformanceMode } from '../performance';

interface AnimationPerformanceConfig {
  particleCount?: number;
  animationDuration?: number;
  enableAdvancedEffects?: boolean;
  enableParticles?: boolean;
  enableBlur?: boolean;
  enableShadows?: boolean;
}

interface OptimizedAnimationConfig extends AnimationPerformanceConfig {
  shouldAnimate: boolean;
  optimizedParticleCount: number;
  optimizedDuration: number;
  gpuAcceleration: boolean;
}

export const useAnimationPerformance = (
  baseConfig: AnimationPerformanceConfig = {}
): OptimizedAnimationConfig => {
  const { 
    performanceMode, 
    isReducedMotion, 
    deviceCapabilities 
  } = usePerformance();
  
  const frameTimeRef = useRef<number[]>([]);
  const lastFrameTime = useRef<number>(performance.now());

  // Track animation performance
  const trackFrame = useCallback(() => {
    const now = performance.now();
    const frameTime = now - lastFrameTime.current;
    
    frameTimeRef.current.push(frameTime);
    if (frameTimeRef.current.length > 60) {
      frameTimeRef.current.shift();
    }
    
    lastFrameTime.current = now;
  }, []);

  // Auto-adjust based on performance mode and device capabilities
  const getOptimizedConfig = useCallback((): OptimizedAnimationConfig => {
    // Don't animate if reduced motion is preferred
    if (isReducedMotion) {
      return {
        ...baseConfig,
        shouldAnimate: false,
        optimizedParticleCount: 0,
        optimizedDuration: 0,
        gpuAcceleration: false,
        enableAdvancedEffects: false,
        enableParticles: false,
        enableBlur: false,
        enableShadows: false,
      };
    }

    const baseParticleCount = baseConfig.particleCount || 6;
    const baseDuration = baseConfig.animationDuration || 2;

    let optimizedConfig: OptimizedAnimationConfig = {
      ...baseConfig,
      shouldAnimate: true,
      optimizedParticleCount: baseParticleCount,
      optimizedDuration: baseDuration,
      gpuAcceleration: true,
      enableAdvancedEffects: true,
      enableParticles: true,
      enableBlur: true,
      enableShadows: true,
    };

    // Optimize based on performance mode
    switch (performanceMode) {
      case 'low':
        optimizedConfig = {
          ...optimizedConfig,
          optimizedParticleCount: Math.max(1, Math.floor(baseParticleCount * 0.3)),
          optimizedDuration: baseDuration * 1.5, // Slower animations
          enableAdvancedEffects: false,
          enableParticles: false,
          enableBlur: false,
          enableShadows: false,
        };
        break;
        
      case 'balanced':
        optimizedConfig = {
          ...optimizedConfig,
          optimizedParticleCount: Math.floor(baseParticleCount * 0.7),
          optimizedDuration: baseDuration * 1.2,
          enableAdvancedEffects: deviceCapabilities.supportsAdvancedEffects,
          enableBlur: deviceCapabilities.supportsAdvancedEffects,
        };
        break;
        
      case 'high':
        // Keep base config for high performance
        break;
    }

    // Further optimize for mobile devices
    if (deviceCapabilities.isMobile) {
      optimizedConfig.optimizedParticleCount = Math.floor(optimizedConfig.optimizedParticleCount * 0.8);
      optimizedConfig.enableBlur = optimizedConfig.enableBlur && !deviceCapabilities.isLowEndDevice;
    }

    // Disable heavy effects on low-end devices
    if (deviceCapabilities.isLowEndDevice) {
      optimizedConfig.enableAdvancedEffects = false;
      optimizedConfig.enableParticles = false;
      optimizedConfig.enableBlur = false;
      optimizedConfig.optimizedParticleCount = Math.min(optimizedConfig.optimizedParticleCount, 2);
    }

    return optimizedConfig;
  }, [
    performanceMode, 
    isReducedMotion, 
    deviceCapabilities, 
    baseConfig
  ]);

  // Performance monitoring
  useEffect(() => {
    let rafId: number;
    
    const monitor = () => {
      trackFrame();
      rafId = requestAnimationFrame(monitor);
    };
    
    rafId = requestAnimationFrame(monitor);
    
    return () => {
      if (rafId) cancelAnimationFrame(rafId);
    };
  }, [trackFrame]);

  return getOptimizedConfig();
};

// Utility hook for GPU acceleration classes
export const useGPUAcceleration = (enabled: boolean = true): string => {
  return enabled ? 'gpu-accelerated transform-gpu' : '';
};

// Utility hook for animation-safe transforms
export const useAnimationSafeTransform = () => {
  return useCallback((transform: string) => {
    // Ensure transforms use translate3d for hardware acceleration
    if (transform.includes('translate') && !transform.includes('translate3d')) {
      return transform.replace(/translate\(([^)]+)\)/, 'translate3d($1, 0)');
    }
    return transform;
  }, []);
};