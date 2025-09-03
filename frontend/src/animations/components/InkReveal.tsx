import React, { useState, useEffect } from 'react';
import { motion, Variants } from 'framer-motion';
import { InkRevealProps } from '../types/animations';
import { performanceUtils } from '../utils/performanceUtils';
import { ANIMATION_DURATION, EASING } from '../utils/animationConstants';
import { cn } from '@/lib/utils';

export const InkReveal: React.FC<InkRevealProps> = ({
  children,
  className,
  revealDirection = 'center',
  inkColor = '#ffffff',
  splatterEffect = true,
  bleedAmount = 2,
  isActive = true,
  performanceMode = 'balanced',
  ...props
}) => {
  const [isRevealing, setIsRevealing] = useState(false);
  const [reducedMotion] = useState(performanceUtils.prefersReducedMotion());

  // Trigger reveal animation on mount
  useEffect(() => {
    if (isActive && !reducedMotion) {
      const timer = setTimeout(() => setIsRevealing(true), 500);
      return () => clearTimeout(timer);
    }
  }, [isActive, reducedMotion]);

  // Clip path variants for different reveal directions
  const getClipPath = (direction: string, progress: number) => {
    switch (direction) {
      case 'left':
        return `inset(0 ${100 - progress}% 0 0)`;
      case 'right':
        return `inset(0 0 0 ${100 - progress}%)`;
      case 'top':
        return `inset(0 0 ${100 - progress}% 0)`;
      case 'bottom':
        return `inset(${100 - progress}% 0 0 0)`;
      case 'center':
      default:
        const centerProgress = progress / 2;
        return `inset(${50 - centerProgress}% ${50 - centerProgress}% ${50 - centerProgress}% ${50 - centerProgress}%)`;
    }
  };

  const revealVariants: Variants = {
    hidden: {
      opacity: 0,
      scale: 0.8,
      filter: 'blur(10px)',
    },
    visible: {
      opacity: 1,
      scale: 1,
      filter: 'blur(0px)',
      transition: {
        duration: ANIMATION_DURATION.LONG,
        ease: EASING.EASE_OUT,
      },
    },
  };

  // Ink splatter effect
  const splatterVariants: Variants = {
    hidden: { scale: 0, opacity: 0 },
    visible: (i: number) => ({
      scale: [0, 1.2, 0.8],
      opacity: [0, 0.6, 0],
      transition: {
        duration: ANIMATION_DURATION.MEDIUM,
        delay: i * 0.1,
        ease: EASING.EASE_OUT,
      },
    }),
  };

  if (reducedMotion) {
    return (
      <div className={cn('ink-reveal', className)}>
        {children}
      </div>
    );
  }

  return (
    <div className={cn('relative ink-reveal', className)}>
      {/* Main content with reveal animation */}
      <motion.div
        variants={revealVariants}
        initial="hidden"
        animate={isRevealing ? 'visible' : 'hidden'}
        className="relative"
      >
        {children}
      </motion.div>

      {/* Ink splatter effects */}
      {splatterEffect && performanceMode !== 'low' && (
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          {[...Array(6)].map((_, i) => (
            <motion.div
              key={i}
              className="absolute rounded-full"
              style={{
                backgroundColor: inkColor,
                width: `${performanceUtils.randomInRange(2, 8)}px`,
                height: `${performanceUtils.randomInRange(2, 8)}px`,
                left: `${performanceUtils.randomInRange(10, 90)}%`,
                top: `${performanceUtils.randomInRange(10, 90)}%`,
                filter: `blur(${bleedAmount}px)`,
              }}
              variants={splatterVariants}
              initial="hidden"
              animate={isRevealing ? 'visible' : 'hidden'}
              custom={i}
            />
          ))}
        </div>
      )}

      {/* Brush stroke overlay */}
      {performanceMode === 'high' && (
        <motion.div
          className="absolute inset-0 pointer-events-none"
          style={{
            background: `linear-gradient(45deg, transparent 48%, ${inkColor}20 49%, ${inkColor}40 50%, ${inkColor}20 51%, transparent 52%)`,
            backgroundSize: '20px 20px',
          }}
          initial={{ opacity: 0 }}
          animate={{ opacity: isRevealing ? [0.3, 0] : 0 }}
          transition={{
            duration: ANIMATION_DURATION.MEDIUM,
            ease: EASING.EASE_OUT,
          }}
        />
      )}
    </div>
  );
};