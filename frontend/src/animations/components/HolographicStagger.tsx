import React, { useState } from 'react';
import { motion, Variants } from 'framer-motion';
import { HolographicStaggerProps } from '../types/animations';
import { performanceUtils } from '../utils/performanceUtils';
import { ANIMATION_DURATION, EASING, COLORS } from '../utils/animationConstants';
import { cn } from '@/lib/utils';

export const HolographicStagger: React.FC<HolographicStaggerProps> = ({
  children,
  className,
  staggerDelay = 0.1,
  hologramColor = COLORS.ELECTRIC_BLUE,
  glowIntensity = 0.6,
  isActive = true,
  performanceMode = 'balanced',
  ...props
}) => {
  const [isHovered, setIsHovered] = useState(false);
  const [reducedMotion] = useState(performanceUtils.prefersReducedMotion());

  // Container variants for stagger effect
  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        delayChildren: 0.2,
        staggerChildren: staggerDelay,
      },
    },
    hover: {
      transition: {
        staggerChildren: staggerDelay * 0.5,
      },
    },
  };

  // Individual item variants
  const itemVariants: Variants = {
    hidden: {
      opacity: 0,
      y: 20,
      rotateX: -15,
      scale: 0.9,
      filter: 'drop-shadow(0 0 0px transparent)',
    },
    visible: {
      opacity: 1,
      y: 0,
      rotateX: 0,
      scale: 1,
      filter: `drop-shadow(0 0 4px ${hologramColor}90) drop-shadow(0 0 2px ${hologramColor}FF)`,
      transition: {
        duration: ANIMATION_DURATION.MEDIUM,
        ease: EASING.EASE_OUT,
      },
    },
    hover: {
      y: -5,
      rotateX: 5,
      scale: 1.05,
      filter: `drop-shadow(0 0 20px ${hologramColor}FF) drop-shadow(0 0 6px ${hologramColor}FF) drop-shadow(0 0 2px ${hologramColor}FF)`,
      transition: {
        duration: ANIMATION_DURATION.SHORT,
        ease: EASING.EASE_OUT,
      },
    },
    float: {
      y: [-2, 2, -2],
      rotateY: [-1, 1, -1],
      filter: [
        `drop-shadow(0 0 3px ${hologramColor}90) drop-shadow(0 0 1px ${hologramColor}FF)`,
        `drop-shadow(0 0 16px ${hologramColor}FF) drop-shadow(0 0 6px ${hologramColor}FF) drop-shadow(0 0 2px ${hologramColor}FF)`,
        `drop-shadow(0 0 3px ${hologramColor}90) drop-shadow(0 0 1px ${hologramColor}FF)`,
      ],
      transition: {
        duration: ANIMATION_DURATION.AMBIENT,
        ease: EASING.EASE_IN_OUT,
        repeat: Infinity,
      },
    },
  };


  if (reducedMotion) {
    return (
      <div className={cn('holographic-stagger', className)}>
        {children}
      </div>
    );
  }

  return (
    <motion.div
      className={cn('relative holographic-stagger gpu-accelerated', className)}
      variants={containerVariants}
      initial="hidden"
      animate={isActive ? 'visible' : 'hidden'}
      style={{ perspective: '1000px' }}
      {...props}
    >

      {/* Content wrapper with stagger animation */}
      <motion.div
        className="relative"
        variants={{}}
        animate={[
          isActive ? 'visible' : 'hidden',
          performanceMode !== 'low' ? 'float' : 'visible'
        ]}
      >
        {React.Children.map(children, (child, index) => (
          <motion.div
            key={index}
            variants={itemVariants}
            className="relative"
            whileHover="hover"
          >
            {child}
          </motion.div>
        ))}
      </motion.div>

    </motion.div>
  );
};