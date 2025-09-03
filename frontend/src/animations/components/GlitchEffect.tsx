import React, { useEffect, useState, useCallback, useRef } from 'react';
import { motion, useMotionValue, useTransform } from 'framer-motion';
import { GlitchEffectProps } from '../types/animations';
import { performanceUtils } from '../utils/performanceUtils';
import { ANIMATION_DURATION, EASING, COLORS } from '../utils/animationConstants';
import { cn } from '@/lib/utils';

export const GlitchEffect: React.FC<GlitchEffectProps> = ({
  children,
  className,
  glitchIntensity = 1,
  colorShift = true,
  scanLines = true,
  distortionAmount = 2,
  isActive = true,
  performanceMode = 'balanced',
  ...props
}) => {
  const [isGlitching, setIsGlitching] = useState(false);
  const [reducedMotion] = useState(performanceUtils.prefersReducedMotion());
  const [mouseDistance, setMouseDistance] = useState(1);
  const componentRef = useRef<HTMLDivElement>(null);
  
  // Motion values for transform properties
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const skewX = useMotionValue(0);
  const skewY = useMotionValue(0);
  const scale = useMotionValue(1);
  
  // Transform RGB separation offsets
  const redOffset = useTransform(x, (value) => value * -1.5 * glitchIntensity);
  const greenOffset = useTransform(x, (value) => value * 1.5 * glitchIntensity);
  
  // Glitch animation function
  const triggerGlitch = useCallback(() => {
    if (!isActive || reducedMotion) return;
    
    setIsGlitching(true);
    
    // Random distortion values
    const intensity = glitchIntensity * distortionAmount;
    const randomX = performanceUtils.randomInRange(-intensity, intensity);
    const randomY = performanceUtils.randomInRange(-intensity * 0.5, intensity * 0.5);
    const randomSkewX = performanceUtils.randomInRange(-intensity * 0.5, intensity * 0.5);
    const randomSkewY = performanceUtils.randomInRange(-intensity * 0.3, intensity * 0.3);
    const randomScale = performanceUtils.randomInRange(0.98, 1.02);
    
    // Apply distortion
    x.set(randomX);
    y.set(randomY);
    skewX.set(randomSkewX);
    skewY.set(randomSkewY);
    scale.set(randomScale);
    
    // Reset after brief duration
    setTimeout(() => {
      x.set(0);
      y.set(0);
      skewX.set(0);
      skewY.set(0);
      scale.set(1);
      setIsGlitching(false);
    }, ANIMATION_DURATION.SHORT * 1000);
  }, [isActive, reducedMotion, glitchIntensity, distortionAmount, x, y, skewX, skewY, scale]);
  
  // Random glitch intervals
  useEffect(() => {
    if (!isActive || reducedMotion) return;
    
    const scheduleNextGlitch = () => {
      const interval = performanceUtils.randomGlitchInterval();
      return setTimeout(triggerGlitch, interval);
    };
    
    let timeoutId = scheduleNextGlitch();
    
    return () => {
      clearTimeout(timeoutId);
    };
  }, [isActive, reducedMotion, triggerGlitch]);

  // Global mouse tracking effect
  useEffect(() => {
    if (!isActive || reducedMotion) return;

    const handleGlobalMouseMove = (e: MouseEvent) => {
      if (!componentRef.current) return;

      const rect = componentRef.current.getBoundingClientRect();
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;
      
      const deltaX = e.clientX - centerX;
      const deltaY = e.clientY - centerY;
      const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
      const maxDistance = Math.sqrt(window.innerWidth * window.innerWidth + window.innerHeight * window.innerHeight);
      
      // Normalized distance (0 = at center, 1 = at edge of screen)
      const normalizedDistance = Math.min(distance / maxDistance, 1);
      setMouseDistance(normalizedDistance);
      
      // Apply subtle movement based on mouse position
      const intensity = glitchIntensity * (1 - normalizedDistance) * 2;
      x.set(deltaX * intensity * 0.01);
      y.set(deltaY * intensity * 0.01);
      skewX.set(deltaX * intensity * 0.005);
      skewY.set(deltaY * intensity * 0.005);
    };

    document.addEventListener('mousemove', handleGlobalMouseMove);
    
    return () => {
      document.removeEventListener('mousemove', handleGlobalMouseMove);
    };
  }, [isActive, reducedMotion, glitchIntensity, x, y, skewX, skewY]);
  
  // Glitch variants for different intensities
  const glitchVariants = {
    idle: {
      filter: 'hue-rotate(0deg) contrast(1) brightness(1)',
      transition: { duration: ANIMATION_DURATION.SHORT, ease: EASING.EASE_OUT },
    },
    glitching: {
      filter: [
        'hue-rotate(0deg) contrast(1) brightness(1)',
        'hue-rotate(90deg) contrast(1.2) brightness(1.1)',
        'hue-rotate(-90deg) contrast(0.8) brightness(0.9)',
        'hue-rotate(0deg) contrast(1) brightness(1)',
      ],
      transition: {
        duration: ANIMATION_DURATION.SHORT,
        times: [0, 0.3, 0.7, 1],
        ease: EASING.GLITCH,
      },
    },
    hover: {
      filter: 'hue-rotate(0deg) contrast(1.1) brightness(1.05)',
      transition: { duration: ANIMATION_DURATION.MICRO, ease: EASING.EASE_OUT },
    },
  };
  
  if (reducedMotion) {
    return (
      <div className={cn('relative', className)}>
        {children}
      </div>
    );
  }
  
  return (
    <motion.div
      ref={componentRef}
      className={cn('relative gpu-accelerated', className)}
      style={{ x, y, skewX, skewY, scale }}
      variants={glitchVariants}
      initial="idle"
      animate={isGlitching ? 'glitching' : 'idle'}
      whileHover="hover"
      onClick={triggerGlitch}
      {...props}
    >
      {/* Main content */}
      <div className="relative z-10">{children}</div>
      
      {/* RGB color separation layers */}
      {colorShift && performanceMode !== 'low' && (
        <>
          <motion.div
            className="absolute inset-0 opacity-50 mix-blend-screen pointer-events-none"
            style={{
              x: redOffset,
              filter: `hue-rotate(90deg) saturate(200%)`,
            }}
          >
            {children}
          </motion.div>
          <motion.div
            className="absolute inset-0 opacity-50 mix-blend-screen pointer-events-none"
            style={{
              x: greenOffset,
              filter: `hue-rotate(-90deg) saturate(150%)`,
            }}
          >
            {children}
          </motion.div>
        </>
      )}
      
      {/* Scan lines overlay */}
      {scanLines && performanceMode === 'high' && (
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          <div className="glitch-scanlines" />
        </div>
      )}
      
      {/* Data corruption overlay */}
      {isGlitching && performanceMode === 'high' && (
        <motion.div
          className="absolute inset-0 pointer-events-none text-green-400 text-xs font-mono overflow-hidden opacity-30"
          initial={{ opacity: 0 }}
          animate={{ opacity: 0.3 }}
          exit={{ opacity: 0 }}
        >
          <div className="absolute top-0 left-0 animate-pulse">
            [ERROR] SIGNAL_CORRUPTION_DETECTED
          </div>
          <div className="absolute top-4 right-0 animate-pulse delay-100">
            0x4E4F4953 0x45434E45
          </div>
          <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 animate-pulse delay-200">
            NEURAL_LINK_UNSTABLE
          </div>
        </motion.div>
      )}
    </motion.div>
  );
};