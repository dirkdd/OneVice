import React, { useState } from 'react';
import { motion, Variants } from 'framer-motion';
import { GlassMorphismPulseProps } from '../types/animations';
import { performanceUtils } from '../utils/performanceUtils';
import { ANIMATION_DURATION, EASING } from '../utils/animationConstants';
import { cn } from '@/lib/utils';

export const GlassMorphismPulse: React.FC<GlassMorphismPulseProps> = ({
  children,
  className,
  pulseFrequency = 2,
  blurAmount = 10,
  glassOpacity = 0.1,
  isActive = true,
  performanceMode = 'balanced',
  ...props
}) => {
  const [isHovered, setIsHovered] = useState(false);
  const [reducedMotion] = useState(performanceUtils.prefersReducedMotion());

  // Glass morphism pulse variants
  const glassVariants: Variants = {
    idle: {
      backdropFilter: `blur(${blurAmount}px)`,
      backgroundColor: `rgba(255, 255, 255, ${glassOpacity})`,
      borderColor: `rgba(255, 255, 255, ${glassOpacity * 2})`,
      scale: 1,
    },
    pulse: {
      backdropFilter: [
        `blur(${blurAmount}px)`,
        `blur(${blurAmount + 2}px)`,
        `blur(${blurAmount}px)`,
      ],
      backgroundColor: [
        `rgba(255, 255, 255, ${glassOpacity})`,
        `rgba(255, 255, 255, ${glassOpacity * 1.5})`,
        `rgba(255, 255, 255, ${glassOpacity})`,
      ],
      borderColor: [
        `rgba(255, 255, 255, ${glassOpacity * 2})`,
        `rgba(255, 255, 255, ${glassOpacity * 3})`,
        `rgba(255, 255, 255, ${glassOpacity * 2})`,
      ],
      scale: [1, 1.02, 1],
      transition: {
        duration: pulseFrequency,
        ease: EASING.EASE_IN_OUT,
        repeat: Infinity,
      },
    },
    hover: {
      backdropFilter: `blur(${blurAmount + 5}px)`,
      backgroundColor: `rgba(255, 255, 255, ${glassOpacity * 2})`,
      borderColor: `rgba(255, 255, 255, ${glassOpacity * 4})`,
      scale: 1.05,
      transition: {
        duration: ANIMATION_DURATION.SHORT,
        ease: EASING.EASE_OUT,
      },
    },
  };

  // Floating particles for enhanced effect
  const particleVariants: Variants = {
    idle: { opacity: 0, scale: 0 },
    active: (i: number) => ({
      opacity: [0, 0.6, 0],
      scale: [0, 1, 0],
      x: [
        0,
        performanceUtils.randomInRange(-20, 20),
        performanceUtils.randomInRange(-10, 10),
      ],
      y: [
        0,
        performanceUtils.randomInRange(-20, 20),
        performanceUtils.randomInRange(-10, 10),
      ],
      transition: {
        duration: ANIMATION_DURATION.LONG + i * 0.2,
        ease: EASING.EASE_OUT,
        repeat: Infinity,
        delay: i * 0.3,
      },
    }),
  };

  // Shimmer effect variants
  const shimmerVariants: Variants = {
    idle: {
      backgroundPosition: '-100% 0',
    },
    active: {
      backgroundPosition: '200% 0',
      transition: {
        duration: ANIMATION_DURATION.LONG,
        ease: 'linear',
        repeat: Infinity,
      },
    },
  };

  if (reducedMotion) {
    return (
      <div
        className={cn('glass-morphism', className)}
        style={{
          backdropFilter: `blur(${blurAmount}px)`,
          backgroundColor: `rgba(255, 255, 255, ${glassOpacity})`,
          border: `1px solid rgba(255, 255, 255, ${glassOpacity * 2})`,
        }}
      >
        {children}
      </div>
    );
  }

  return (
    <motion.div
      className={cn('relative glass-morphism gpu-accelerated', className)}
      variants={glassVariants}
      initial="idle"
      animate={isActive && !isHovered ? 'pulse' : 'idle'}
      whileHover="hover"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={{
        border: '1px solid transparent',
      }}
      {...props}
    >
      {/* Shimmer overlay */}
      {performanceMode !== 'low' && (
        <motion.div
          className="absolute inset-0 rounded-inherit pointer-events-none overflow-hidden"
          style={{
            background: `linear-gradient(
              90deg,
              transparent 0%,
              rgba(255, 255, 255, 0.4) 50%,
              transparent 100%
            )`,
            backgroundSize: '200% 100%',
          }}
          variants={shimmerVariants}
          initial="idle"
          animate={isHovered ? 'active' : 'idle'}
        />
      )}

      {/* Content */}
      <div className="relative z-10">
        {children}
      </div>

      {/* Floating particles */}
      {performanceMode === 'high' && (
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          {[...Array(4)].map((_, i) => (
            <motion.div
              key={i}
              className="absolute w-1 h-1 rounded-full bg-white/30"
              style={{
                left: `${20 + i * 20}%`,
                top: `${30 + i * 15}%`,
              }}
              variants={particleVariants}
              initial="idle"
              animate={isActive ? 'active' : 'idle'}
              custom={i}
            />
          ))}
        </div>
      )}

      {/* Edge glow effect */}
      {performanceMode !== 'low' && isHovered && (
        <motion.div
          className="absolute inset-0 rounded-inherit pointer-events-none"
          style={{
            boxShadow: `inset 0 0 20px rgba(255, 255, 255, ${glassOpacity * 3})`,
          }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{
            duration: ANIMATION_DURATION.SHORT,
            ease: EASING.EASE_OUT,
          }}
        />
      )}
    </motion.div>
  );
};