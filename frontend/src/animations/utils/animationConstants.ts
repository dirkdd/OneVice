// Animation timing constants
export const ANIMATION_DURATION = {
  MICRO: 0.15,      // Quick hover effects
  SHORT: 0.3,       // Button interactions
  MEDIUM: 0.6,      // Card transitions
  LONG: 0.8,        // Complex reveals
  AMBIENT: 3,       // Background flows
  IDLE: 5,          // Idle state animations
} as const;

// Easing functions
export const EASING = {
  EASE_OUT: [0.4, 0, 0.2, 1],
  EASE_IN: [0.4, 0, 1, 1],
  EASE_IN_OUT: [0.4, 0, 0.6, 1],
  SPRING: { type: 'spring', stiffness: 280, damping: 20, mass: 1 },
  GLITCH: [0.25, 0.46, 0.45, 0.94],
  LIQUID: [0.6, -0.05, 0.01, 0.99],
} as const;

// Color constants
export const COLORS = {
  GOLD_GRADIENT: ['#BC995C', '#DBC173'],
  ELECTRIC_BLUE: '#00ffff',
  NEON_PINK: '#ff00ff',
  WHITE: '#ffffff',
  GLITCH_COLORS: ['#ff0040', '#00ff80', '#8000ff'],
} as const;

// Performance thresholds
export const PERFORMANCE = {
  MIN_FPS: 30,
  TARGET_FPS: 60,
  HIGH_PERFORMANCE_THRESHOLD: 45,
  REDUCED_MOTION_FALLBACK: 0.5,
} as const;

// Animation intervals (in milliseconds)
export const INTERVALS = {
  GLITCH_MIN: 5000,
  GLITCH_MAX: 8000,
  PERFORMANCE_CHECK: 1000,
  THROTTLE: 16, // ~60fps
} as const;