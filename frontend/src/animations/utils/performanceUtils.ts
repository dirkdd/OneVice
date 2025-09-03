import { PERFORMANCE, INTERVALS } from './animationConstants';

export const performanceUtils = {
  // Debounce animation updates
  debounceAnimation: (fn: Function, delay: number = INTERVALS.THROTTLE) => {
    let timeoutId: NodeJS.Timeout;
    return (...args: any[]) => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => fn(...args), delay);
    };
  },
  
  // Throttle high-frequency animations
  throttleAnimation: (fn: Function, limit: number = INTERVALS.THROTTLE) => {
    let inThrottle: boolean;
    return (...args: any[]) => {
      if (!inThrottle) {
        fn(...args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  },
  
  // Use CSS transforms for GPU acceleration
  getGPUAcceleratedTransform: (x: number, y: number, z = 0) => {
    return `translate3d(${x}px, ${y}px, ${z}px)`;
  },
  
  // Detect device capabilities
  getPerformanceMode: (): 'high' | 'balanced' | 'low' => {
    // Check device memory
    const memory = (navigator as any).deviceMemory;
    const cores = navigator.hardwareConcurrency;
    
    // Check if we're on mobile
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
      navigator.userAgent
    );
    
    if (isMobile) return 'balanced';
    if (memory >= 8 && cores >= 4) return 'high';
    if (memory >= 4 && cores >= 2) return 'balanced';
    return 'low';
  },
  
  // Check for reduced motion preference
  prefersReducedMotion: (): boolean => {
    if (typeof window === 'undefined') return false;
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  },
  
  // Intersection Observer for lazy animation init
  createAnimationObserver: (
    callback: IntersectionObserverCallback,
    options?: IntersectionObserverInit
  ) => {
    return new IntersectionObserver(callback, {
      threshold: 0.1,
      rootMargin: '50px',
      ...options,
    });
  },
  
  // Generate random value within range
  randomInRange: (min: number, max: number): number => {
    return Math.random() * (max - min) + min;
  },
  
  // Generate random glitch interval
  randomGlitchInterval: (): number => {
    return performanceUtils.randomInRange(INTERVALS.GLITCH_MIN, INTERVALS.GLITCH_MAX);
  },
  
  // Check if animation should be reduced based on performance
  shouldReduceAnimation: (fps: number): boolean => {
    return fps < PERFORMANCE.MIN_FPS;
  },
  
  // Get animation multiplier based on performance
  getAnimationMultiplier: (fps: number, performanceMode: 'high' | 'balanced' | 'low'): number => {
    if (performanceMode === 'low' || fps < PERFORMANCE.MIN_FPS) return 0.5;
    if (performanceMode === 'balanced' || fps < PERFORMANCE.HIGH_PERFORMANCE_THRESHOLD) return 0.75;
    return 1;
  },
};