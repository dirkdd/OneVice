import { MotionProps } from 'framer-motion';
import { ReactNode } from 'react';

export interface BaseAnimationProps extends MotionProps {
  children?: ReactNode;
  isActive?: boolean;
  delay?: number;
  duration?: number;
  intensity?: number;
  onAnimationComplete?: () => void;
  performanceMode?: 'high' | 'balanced' | 'low';
  className?: string;
}

export interface GlitchEffectProps extends BaseAnimationProps {
  glitchIntensity?: number;
  colorShift?: boolean;
  scanLines?: boolean;
  distortionAmount?: number;
}

export interface LiquidMetalProps extends BaseAnimationProps {
  viscosity?: number;
  reflectivity?: number;
  flowDirection?: 'horizontal' | 'vertical' | 'radial';
  gradientColors?: string[];
}

export interface InkRevealProps extends BaseAnimationProps {
  revealDirection?: 'left' | 'right' | 'top' | 'bottom' | 'center';
  inkColor?: string;
  splatterEffect?: boolean;
  bleedAmount?: number;
}

export interface HolographicStaggerProps extends BaseAnimationProps {
  staggerDelay?: number;
  hologramColor?: string;
  scanlineSpeed?: number;
  glowIntensity?: number;
}

export interface GlassMorphismPulseProps extends BaseAnimationProps {
  pulseFrequency?: number;
  blurAmount?: number;
  glassOpacity?: number;
  refractionIndex?: number;
}

export interface EnergyChargeProps extends BaseAnimationProps {
  chargeSpeed?: number;
  electricColor?: string;
  particleCount?: number;
  magneticField?: boolean;
}

export interface AnimationState {
  globalPlayState: 'playing' | 'paused' | 'stopped';
  activeAnimations: Set<string>;
  performanceMode: 'high' | 'balanced' | 'low';
  reducedMotion: boolean;
  fps: number;
}

export interface AnimationStore extends AnimationState {
  setGlobalPlayState: (state: 'playing' | 'paused' | 'stopped') => void;
  registerAnimation: (id: string) => void;
  unregisterAnimation: (id: string) => void;
  setPerformanceMode: (mode: 'high' | 'balanced' | 'low') => void;
  setReducedMotion: (reduced: boolean) => void;
  setFps: (fps: number) => void;
  shouldPlayAnimations: () => boolean;
  getAnimationMultiplier: () => number;
}