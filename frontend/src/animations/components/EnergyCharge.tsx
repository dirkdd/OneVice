import React, { useState } from 'react';
import { motion, Variants } from 'framer-motion';
import { EnergyChargeProps } from '../types/animations';
import { performanceUtils } from '../utils/performanceUtils';
import { ANIMATION_DURATION, EASING, COLORS } from '../utils/animationConstants';
import { usePerformance } from '../performance';
import { cn } from '@/lib/utils';

export const EnergyCharge: React.FC<EnergyChargeProps> = ({
  children,
  className,
  chargeSpeed = 2,
  electricColor = COLORS.ELECTRIC_BLUE,
  particleCount = 6,
  magneticField = true,
  isActive = true,
  performanceMode: propPerformanceMode = 'balanced',
  ...props
}) => {
  const [isCharging, setIsCharging] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const [reducedMotion] = useState(performanceUtils.prefersReducedMotion());
  
  // Use performance context if available, fallback to prop
  const { performanceMode: contextPerformanceMode, isReducedMotion: contextReducedMotion } = usePerformance();
  const performanceMode = contextPerformanceMode || propPerformanceMode;
  const reducedMotionPreferred = contextReducedMotion || reducedMotion;
  
  // Simple pulse variants
  const pulseVariants: Variants = {
    idle: {
      boxShadow: `0px 0px 20px rgba(255,255,255,0.4)`,
    },
    pulse: {
      boxShadow: [
        `0px 0px 20px rgba(255,255,255,0.4)`,
        `0px 0px 40px rgba(255,255,255,0.7)`,
        `0px 0px 20px rgba(255,255,255,0.4)`,
      ],
      transition: {
        duration: 3,
        ease: EASING.EASE_IN_OUT,
        repeat: Infinity,
      },
    },
  };
  
  // Electric arc variants
  const arcVariants: Variants = {
    idle: {
      pathLength: 0,
      opacity: 0,
    },
    active: {
      pathLength: [0, 1, 0],
      opacity: [0, 1, 0],
      transition: {
        duration: ANIMATION_DURATION.SHORT,
        ease: EASING.EASE_IN_OUT,
        repeat: Infinity,
        repeatDelay: performanceUtils.randomInRange(0.1, 0.5),
      },
    },
  };
  
  // Particle variants
  const particleVariants: Variants = {
    idle: {
      scale: 0,
      opacity: 0,
    },
    active: (i: number) => ({
      scale: [0, 1.2, 0.8, 0],
      opacity: [0, 1, 0.8, 0],
      x: [
        0,
        performanceUtils.randomInRange(-30, 30),
        performanceUtils.randomInRange(-20, 20),
        0,
      ],
      y: [
        0,
        performanceUtils.randomInRange(-30, 30),
        performanceUtils.randomInRange(-20, 20),
        0,
      ],
      transition: {
        duration: ANIMATION_DURATION.LONG + i * 0.1,
        ease: EASING.EASE_OUT,
        repeat: Infinity,
        delay: i * 0.1,
      },
    }),
  };
  
  // Ripple effect variants
  const rippleVariants: Variants = {
    idle: {
      scale: 1,
      opacity: 0,
    },
    active: {
      scale: [1, 2, 3],
      opacity: [0.8, 0.4, 0],
      transition: {
        duration: ANIMATION_DURATION.MEDIUM,
        ease: EASING.EASE_OUT,
      },
    },
  };
  
  const handleClick = () => {
    setIsCharging(true);
    setTimeout(() => setIsCharging(false), ANIMATION_DURATION.MEDIUM * 1000);
  };
  
  if (reducedMotionPreferred) {
    return (
      <div className={cn('energy-charge', className)}>
        {children}
      </div>
    );
  }
  
  return (
    <motion.div
      className={cn('relative energy-charge', className)}
      variants={pulseVariants}
      initial="idle"
      animate={isActive ? 'pulse' : 'idle'}
      {...props}
    >
      {/* Main content */}
      {children}
    </motion.div>
  );
};