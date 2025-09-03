import React, { useState, useRef } from 'react';
import { motion, useMotionValue, useTransform, MotionValue } from 'framer-motion';
import { LiquidMetalProps } from '../types/animations';
import { performanceUtils } from '../utils/performanceUtils';
import { ANIMATION_DURATION, EASING, COLORS } from '../utils/animationConstants';
import { cn } from '@/lib/utils';

export const LiquidMetalFlow: React.FC<LiquidMetalProps> = ({
  children,
  className,
  viscosity = 0.8,
  reflectivity = 0.9,
  flowDirection = 'horizontal',
  gradientColors = COLORS.GOLD_GRADIENT,
  isActive = true,
  performanceMode = 'balanced',
  ...props
}) => {
  const [isHovered, setIsHovered] = useState(false);
  const [reducedMotion] = useState(performanceUtils.prefersReducedMotion());
  const containerRef = useRef<HTMLDivElement>(null);
  
  // Motion values for mouse interaction
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);
  
  // Background position for flowing effect
  const backgroundPosition = useMotionValue('0% 50%');
  
  // Transform mouse position to gradient angle
  const gradientAngle = useTransform(
    [mouseX, mouseY],
    ([x, y]) => {
      if (flowDirection === 'horizontal') return 90;
      if (flowDirection === 'vertical') return 0;
      // Radial flow - calculate angle based on mouse position
      return Math.atan2(y as number, x as number) * 180 / Math.PI;
    }
  );
  
  // Create dynamic gradient based on mouse position and flow direction
  const dynamicGradient = useTransform(
    [mouseX, mouseY, gradientAngle],
    ([x, y, angle]) => {
      const colors = gradientColors.join(', ');
      
      if (flowDirection === 'radial') {
        const centerX = (x as number) * 100;
        const centerY = (y as number) * 100;
        return `radial-gradient(circle at ${centerX}% ${centerY}%, ${colors})`;
      }
      
      return `linear-gradient(${angle}deg, ${colors})`;
    }
  );
  
  // Shimmer intensity based on hover state
  const shimmerIntensity = useTransform(
    mouseX,
    [0, 1],
    [`0 0 20px rgba(${gradientColors[1]}, 0.5)`, `0 0 40px rgba(${gradientColors[1]}, 0.8)`]
  );
  
  // Handle mouse movement
  const handleMouseMove = (e: React.MouseEvent) => {
    if (!containerRef.current || reducedMotion) return;
    
    const rect = containerRef.current.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width;
    const y = (e.clientY - rect.top) / rect.height;
    
    mouseX.set(x);
    mouseY.set(y);
  };
  
  // Flow animation variants
  const flowVariants = {
    idle: {
      backgroundPosition: ['0% 50%', '100% 50%', '0% 50%'],
      transition: {
        duration: ANIMATION_DURATION.AMBIENT / viscosity,
        ease: 'linear',
        repeat: Infinity,
      },
    },
    hover: {
      backgroundPosition: ['0% 50%', '200% 50%', '0% 50%'],
      transition: {
        duration: (ANIMATION_DURATION.AMBIENT / viscosity) * 0.7,
        ease: 'linear',
        repeat: Infinity,
      },
    },
  };
  
  // Shimmer variants
  const shimmerVariants = {
    idle: {
      textShadow: `0 0 20px rgba(219,193,115,${0.3 * reflectivity})`,
    },
    hover: {
      textShadow: [
        `0 0 20px rgba(219,193,115,${0.5 * reflectivity})`,
        `0 0 40px rgba(219,193,115,${0.8 * reflectivity})`,
        `0 0 60px rgba(219,193,115,${0.6 * reflectivity})`,
        `0 0 20px rgba(219,193,115,${0.5 * reflectivity})`,
      ],
      transition: {
        duration: ANIMATION_DURATION.MEDIUM,
        ease: EASING.EASE_IN_OUT,
        repeat: Infinity,
      },
    },
  };
  
  if (reducedMotion) {
    return (
      <div
        className={cn('liquid-metal', className)}
        style={{
          color: '#DBC173',
          textShadow: '0 0 10px rgba(219, 193, 115, 0.5)',
        }}
      >
        {children}
      </div>
    );
  }
  
  return (
    <motion.div
      ref={containerRef}
      className={cn('relative liquid-metal gpu-accelerated', className)}
      style={{
        color: '#DBC173',
        textShadow: `0 0 20px rgba(219, 193, 115, 0.6), 0 0 40px rgba(188, 153, 92, 0.3)`,
      }}
      variants={flowVariants}
      initial="idle"
      animate={isHovered ? 'hover' : 'idle'}
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => {
        setIsHovered(false);
        mouseX.set(0.5);
        mouseY.set(0.5);
      }}
      {...props}
    >
      {/* Main liquid metal text */}
      <motion.div
        className="relative z-10"
        variants={shimmerVariants}
        initial="idle"
        animate={isHovered ? 'hover' : 'idle'}
      >
        {children}
      </motion.div>
      
      {/* Reflection layer for enhanced metallic effect */}
      {performanceMode !== 'low' && (
        <motion.div
          className="absolute inset-0 opacity-30 mix-blend-overlay pointer-events-none"
          style={{
            background: `linear-gradient(45deg, transparent 30%, rgba(255,255,255,${reflectivity * 0.3}) 50%, transparent 70%)`,
            backgroundSize: '200% 200%',
          }}
          animate={{
            backgroundPosition: isHovered 
              ? ['0% 0%', '100% 100%', '0% 0%'] 
              : ['0% 0%', '50% 50%', '0% 0%'],
          }}
          transition={{
            duration: ANIMATION_DURATION.AMBIENT * (isHovered ? 0.8 : 1.2),
            ease: 'linear',
            repeat: Infinity,
          }}
        />
      )}
      
      {/* Particle effects for high performance mode */}
      {performanceMode === 'high' && isHovered && (
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          {[...Array(6)].map((_, i) => (
            <motion.div
              key={i}
              className="absolute w-1 h-1 bg-yellow-300 rounded-full opacity-60"
              initial={{
                x: Math.random() * 100,
                y: Math.random() * 100,
                opacity: 0,
              }}
              animate={{
                x: Math.random() * 100,
                y: Math.random() * 100,
                opacity: [0, 1, 0],
              }}
              transition={{
                duration: ANIMATION_DURATION.LONG + Math.random(),
                delay: i * 0.1,
                repeat: Infinity,
                ease: 'easeInOut',
              }}
            />
          ))}
        </div>
      )}
    </motion.div>
  );
};