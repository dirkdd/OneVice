# OneVice Frontend Implementation Guide

**Version:** 1.0  
**Date:** September 2, 2025  
**Status:** Implementation Ready  
**Dependencies:** technical-roadmap.md, design-specifications.md, component-library.md  
**Framework:** Next.js 15.4 + React 19 + TypeScript 5.6

## 1. Implementation Strategy Overview

This guide provides a systematic approach to implementing the OneVice frontend with pixel-perfect fidelity to the Figma designs. The implementation is structured in phases that align with the technical roadmap and prioritize user-critical functionality.

### 1.1 Alignment with Technical Roadmap

The frontend implementation maps to **Phase 3: Frontend Development** in the technical roadmap:

```
Technical Roadmap Phase 3 (Weeks 5-6):
├── Week 5 Day 1-2: Core Layout System → Foundation setup
├── Week 5 Day 3-5: Page Implementation → Static pages with Figma fidelity  
├── Week 6 Day 1-3: Interactive Components → Dashboard and AI interfaces
├── Week 6 Day 4-5: Backend Integration → API integration and real-time features
```

**Updated Timeline Alignment:**
- **Project Week 5 = Implementation Week 1**: Foundation, components, static pages
- **Project Week 6 = Implementation Week 2**: Interactive features, backend integration

### 1.2 Critical Success Factors

- **Pixel-Perfect Fidelity**: Match Figma designs exactly (colors, spacing, effects)
- **Performance Targets**: <2s page load, 60fps animations, <100ms interaction response
- **Accessibility Compliance**: WCAG 2.1 AA standards
- **Responsive Design**: Mobile-first approach with breakpoints at 768px, 1024px, 1440px
- **Browser Support**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+

## 2. Project Week 5: Foundation Layer (Implementation Week 1)

### 2.1 Development Environment Setup

#### 2.1.1 Project Initialization

```bash
# Navigate to frontend directory
cd frontend

# Verify Next.js 15.4 installation
npm list next
# Expected: next@15.4.0

# Install additional dependencies for glassmorphism and design system
npm install @headlessui/react@^1.7.0
npm install @heroicons/react@^2.0.0
npm install class-variance-authority@^0.7.0
npm install clsx@^2.0.0
npm install tailwind-merge@^2.0.0
npm install framer-motion@^10.16.0

# Install development dependencies
npm install -D @types/node@^20.0.0
npm install -D autoprefixer@^10.4.0
npm install -D postcss@^8.4.0

# Verify TypeScript 5.6
npm list typescript
# Expected: typescript@5.6.x
```

#### 2.1.2 Tailwind Configuration

```javascript
// tailwind.config.js - Update for OneVice design system
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        serif: ['Flood Std', 'Georgia', 'serif'],
      },
      colors: {
        // OneVice color system
        glass: {
          bg: 'rgba(255, 255, 255, 0.05)',
          border: 'rgba(255, 255, 255, 0.1)',
          elevated: 'rgba(255, 255, 255, 0.08)',
          modal: 'rgba(20, 20, 20, 0.85)',
        },
      },
      backgroundImage: {
        'gradient-home': 'linear-gradient(90deg, rgba(10, 10, 11, 1) 0%, rgba(26, 26, 27, 1) 50%, rgba(17, 17, 17, 1) 100%)',
        'gradient-leadership': 'linear-gradient(90deg, rgba(0, 0, 0, 1) 0%, rgba(17, 17, 17, 1) 50%, rgba(0, 0, 0, 1) 100%)',
      },
      backdropBlur: {
        'xs': '2px',
        'sm': '4px', 
        'md': '12px',
        'lg': '16px',
        'xl': '20px',
      },
      boxShadow: {
        'glass-sm': '0 4px 16px rgba(0, 0, 0, 0.1)',
        'glass-md': '0 8px 32px rgba(0, 0, 0, 0.2)', 
        'glass-lg': '0 12px 40px rgba(0, 0, 0, 0.3)',
        'glass-elevated': '0 8px 32px rgba(0, 0, 0, 0.3)',
        'glass-modal': '0 16px 64px rgba(0, 0, 0, 0.5)',
      },
      animation: {
        'pulse-slow': 'pulse 3s ease-in-out infinite',
        'float': 'float 3s ease-in-out infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-4px)' },
        },
      },
    },
  },
  plugins: [],
}
```

#### 2.1.3 Global Styles Setup

```css
/* app/globals.css - OneVice global styles */
@tailwind base;
@tailwind components;  
@tailwind utilities;

/* Import fonts */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

@layer base {
  :root {
    /* OneVice CSS Custom Properties */
    --gradient-home: linear-gradient(90deg, rgba(10, 10, 11, 1) 0%, rgba(26, 26, 27, 1) 50%, rgba(17, 17, 17, 1) 100%);
    --gradient-leadership: linear-gradient(90deg, rgba(0, 0, 0, 1) 0%, rgba(17, 17, 17, 1) 50%, rgba(0, 0, 0, 1) 100%);
    
    /* Border colors from Figma */
    --border-primary: #CED4DA;
    --border-secondary: #E5E7EB;
    
    /* Text colors for dark theme */
    --text-primary: rgba(255, 255, 255, 0.95);
    --text-secondary: rgba(255, 255, 255, 0.75);
    --text-tertiary: rgba(255, 255, 255, 0.55);
    --text-muted: rgba(255, 255, 255, 0.35);
  }

  html {
    scroll-behavior: smooth;
    overflow-x: hidden;
  }

  body {
    background: var(--gradient-home);
    color: var(--text-primary);
    font-family: 'Inter', system-ui, sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }
  
  /* Glassmorphism support fallbacks */
  @supports not (backdrop-filter: blur(12px)) {
    .backdrop-blur-md {
      background-color: rgba(255, 255, 255, 0.15) !important;
    }
  }
}

@layer components {
  /* Base glassmorphic card */
  .glassmorphic-card {
    @apply bg-white/5 backdrop-blur-md border border-white/10 rounded-xl;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }
  
  /* Interactive glassmorphic card */
  .glassmorphic-card-interactive {
    @apply glassmorphic-card cursor-pointer;
  }
  
  .glassmorphic-card-interactive:hover {
    @apply bg-white/8 border-white/20 transform -translate-y-0.5;
  }
  
  /* Navigation header styles */
  .nav-header {
    @apply sticky top-0 z-50 w-full h-[78px] bg-gray-900/65 backdrop-blur-md border-b border-white/10;
  }
}
```

### 2.2 Core Component Implementation

#### 2.2.1 Layout Components (Priority 1 - Day 1-2)

```typescript
// Implementation checklist
const Week1Priority1Tasks = [
  {
    component: 'app/layout.tsx',
    description: 'Root layout with font loading and metadata',
    estimatedTime: '2 hours',
    figmaReference: 'Global layout patterns'
  },
  {
    component: 'components/ui/GlassmorphicCard.tsx', 
    description: 'Base glassmorphic card component',
    estimatedTime: '4 hours',
    figmaReference: 'All card patterns across pages'
  },
  {
    component: 'components/layout/NavigationHeader.tsx',
    description: 'Main navigation header',  
    estimatedTime: '6 hours',
    figmaReference: 'Header component on all pages'
  },
  {
    component: 'lib/utils.ts',
    description: 'Utility functions (cn, etc.)',
    estimatedTime: '1 hour',
    figmaReference: 'N/A - utility functions'
  }
];
```

#### 2.2.2 Page Structure Setup (Priority 1 - Day 3-4)

```bash
# Create page structure
mkdir -p app/{home,login,leadership,talent,bidding}
mkdir -p components/{ui,layout,form,chat,dashboard,talent,bidding}

# Create page files
touch app/page.tsx  # Home page
touch app/login/page.tsx
touch app/leadership/page.tsx  
touch app/talent/page.tsx
touch app/bidding/page.tsx

# Create component files
touch components/ui/{GlassmorphicCard,LoadingSpinner,EmptyState}.tsx
touch components/form/{GlassmorphicInput,PrimaryButton}.tsx
touch components/layout/{NavigationHeader,PageContainer}.tsx
```

#### 2.2.3 Home Page Implementation (Priority 1 - Day 4-5)

```typescript
// app/page.tsx - Home page implementation
import { NavigationHeader } from '@/components/layout/NavigationHeader';
import { GlassmorphicCard } from '@/components/ui/GlassmorphicCard';
import { PrimaryButton } from '@/components/form/PrimaryButton';

export default function HomePage() {
  return (
    <div className="min-h-screen">
      {/* Page Container - Exact Figma dimensions */}
      <div 
        className="w-full max-w-[1440px] mx-auto bg-gradient-home"
        style={{ minHeight: '4765px' }} // Exact Figma height
      >
        <NavigationHeader />
        
        {/* Hero Section */}
        <section className="min-h-screen flex items-center justify-center px-8">
          <div className="max-w-4xl mx-auto text-center">
            <h1 className="text-6xl font-bold mb-6 bg-gradient-to-r from-white to-white/80 bg-clip-text text-transparent">
              OneVice AI Hub
            </h1>
            <p className="text-xl text-white/75 mb-8 leading-relaxed">
              AI-Powered Business Intelligence for the Entertainment Industry
            </p>
            <div className="flex gap-4 justify-center">
              <PrimaryButton variant="primary" size="lg">
                Get Started
              </PrimaryButton>
              <PrimaryButton variant="secondary" size="lg">
                Watch Demo
              </PrimaryButton>
            </div>
          </div>
        </section>

        {/* Feature Showcase Section */}
        <section className="py-32 px-8">
          <div className="max-w-7xl mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-4xl font-bold mb-6">Intelligent Business Solutions</h2>
              <p className="text-xl text-white/60">
                Powered by advanced AI agents specialized for entertainment industry
              </p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {features.map((feature) => (
                <GlassmorphicCard 
                  key={feature.id}
                  variant="interactive"
                  className="p-8"
                >
                  <div className="text-center">
                    <feature.icon className="w-12 h-12 text-blue-400 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold mb-3">{feature.title}</h3>
                    <p className="text-white/60">{feature.description}</p>
                  </div>
                </GlassmorphicCard>
              ))}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

const features = [
  {
    id: 'sales',
    title: 'Sales Intelligence',
    description: 'AI-powered client research and relationship mapping',
    icon: ChartBarIcon,
  },
  {
    id: 'talent',
    title: 'Talent Discovery',
    description: 'Find and connect with top entertainment professionals',
    icon: UsersIcon,
  },
  {
    id: 'bidding',
    title: 'Smart Bidding',
    description: 'Optimize project bids with AI insights',
    icon: CurrencyDollarIcon,
  },
];
```

### 2.3 Authentication Implementation (Priority 2 - Day 6-7)

#### 2.3.1 Login Page Structure

```typescript
// app/login/page.tsx - Login page matching Figma design
export default function LoginPage() {
  return (
    <div 
      className="w-full max-w-[1440px] mx-auto bg-gradient-home flex items-center justify-center px-4"
      style={{ minHeight: '1596px' }} // Exact Figma height
    >
      <GlassmorphicCard 
        variant="modal"
        className="w-full max-w-md p-8"
      >
        <div className="text-center mb-8">
          <OneViceLogo className="h-12 mx-auto mb-4" />
          <h1 className="text-2xl font-bold mb-2">Welcome to OneVice</h1>
          <p className="text-white/60">AI-Powered Business Intelligence</p>
        </div>

        <LoginForm />
      </GlassmorphicCard>
    </div>
  );
}
```

## 3. Project Week 6: Interactive Features (Implementation Week 2)

### 3.1 AI Interface Components (Week 6 - Day 1-2)

#### 3.1.1 KPI Grid Implementation

```typescript
// app/leadership/page.tsx - Leadership dashboard
export default function LeadershipPage() {
  return (
    <div 
      className="w-full max-w-[1440px] mx-auto bg-gradient-leadership"
      style={{ minHeight: '1440px' }} // Exact Figma square layout
    >
      <NavigationHeader />
      
      {/* Executive Header */}
      <div className="h-[120px] bg-black/80 backdrop-blur-md border-b border-white/5 px-12 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Executive Dashboard</h1>
          <p className="text-white/60">Real-time business intelligence overview</p>
        </div>
        <div className="flex gap-8">
          <MetricBadge label="Revenue" value="$2.4M" trend="+12%" />
          <MetricBadge label="Projects" value="47" trend="+8%" />
        </div>
      </div>

      {/* KPI Grid */}
      <div className="p-12">
        <div className="grid grid-cols-4 gap-8 mb-8">
          {kpiMetrics.map((kpi) => (
            <KPICard key={kpi.id} {...kpi} />
          ))}
        </div>
        
        {/* Charts Section */}
        <div className="grid grid-cols-2 gap-8">
          <AnalyticsChart />
          <TeamPerformanceChart />
        </div>
      </div>
    </div>
  );
}
```

### 3.2 Talent Discovery Interface (Priority 3 - Day 4-5)

#### 3.2.1 Search Interface

```typescript
// app/talent/page.tsx - Talent discovery page
export default function TalentPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [talents, setTalents] = useState<TalentProfile[]>([]);
  
  return (
    <div 
      className="w-full max-w-[1440px] mx-auto bg-gradient-home"
      style={{ minHeight: '1596px' }} // Exact Figma height
    >
      <NavigationHeader />
      
      {/* Search Header */}
      <div className="py-12 px-8 bg-white/2 border-b border-white/10">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-3xl font-bold text-center mb-8">
            Discover Top Talent
          </h1>
          
          <div className="relative">
            <GlassmorphicInput
              type="text"
              placeholder="Search for talent by role, skill, or location..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              variant="pill"
              size="lg"
              icon={MagnifyingGlassIcon}
            />
          </div>
        </div>
      </div>

      {/* Talent Grid */}
      <div className="p-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {talents.map((talent) => (
            <TalentCard
              key={talent.id}
              profile={talent}
              onSelect={handleTalentSelect}
              onContact={handleTalentContact}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
```

### 3.3 Bidding Platform (Priority 3 - Day 6-7)

#### 3.3.1 Real-time Bidding Interface

```typescript
// app/bidding/page.tsx - Bidding platform
export default function BiddingPage() {
  const [timeRemaining, setTimeRemaining] = useState(3600); // 1 hour
  const [currentBid, setCurrentBid] = useState(50000);
  
  return (
    <div 
      className="w-full max-w-[1440px] mx-auto bg-gradient-home"
      style={{ minHeight: '1596px' }} // Exact Figma height
    >
      <NavigationHeader />
      
      {/* Live Bidding Header */}
      <div className="py-8 px-8 bg-white/3 border-b border-white/10">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse" />
            <span className="text-lg font-semibold">Live Bidding</span>
            <span className="text-white/60">Project #2024-101</span>
          </div>
          
          <div className="text-right">
            <div className="text-2xl font-bold text-yellow-400">
              {formatTime(timeRemaining)}
            </div>
            <div className="text-sm text-white/60">Time Remaining</div>
          </div>
        </div>
      </div>

      {/* Bidding Interface */}
      <div className="p-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2">
            <ProjectDetailsPanel />
            <CompetitorBidsPanel />
          </div>
          
          <div>
            <BiddingControlPanel
              projectId="2024-101"
              currentBid={currentBid}
              minimumBid={55000}
              timeRemaining={timeRemaining}
              onSubmitBid={handleSubmitBid}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
```

## 4. Project Week 7-8: Integration and Polish (Overlap with Phase 4)

### 4.1 Real-time WebSocket Integration (Priority 4 - Day 1-2)

#### 4.1.1 WebSocket Hook Implementation

```typescript
// hooks/useWebSocket.ts - Real-time updates
import { useEffect, useState, useRef } from 'react';

interface WebSocketMessage {
  type: 'bid_update' | 'chat_message' | 'system_notification';
  payload: any;
  timestamp: string;
}

export function useWebSocket(url: string, userId: string) {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    const connectWebSocket = () => {
      const ws = new WebSocket(`${url}?userId=${userId}`);

      ws.onopen = () => {
        setIsConnected(true);
        setSocket(ws);
        console.log('WebSocket connected');
      };

      ws.onmessage = (event) => {
        const message: WebSocketMessage = JSON.parse(event.data);
        setMessages(prev => [...prev, message]);
      };

      ws.onclose = () => {
        setIsConnected(false);
        setSocket(null);
        
        // Auto-reconnect after 3 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          connectWebSocket();
        }, 3000);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    };

    connectWebSocket();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (socket) {
        socket.close();
      }
    };
  }, [url, userId]);

  const sendMessage = (message: Omit<WebSocketMessage, 'timestamp'>) => {
    if (socket && isConnected) {
      socket.send(JSON.stringify({
        ...message,
        timestamp: new Date().toISOString(),
      }));
    }
  };

  return {
    isConnected,
    messages,
    sendMessage,
  };
}
```

### 4.2 Form Validation and State Management (Priority 4 - Day 3-4)

#### 4.2.1 Form Validation Hook

```typescript
// hooks/useFormValidation.ts - Form validation logic
import { useState, useCallback } from 'react';
import { z } from 'zod';

export function useFormValidation<T>(schema: z.ZodSchema<T>) {
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isValid, setIsValid] = useState(false);

  const validate = useCallback((data: Partial<T>) => {
    try {
      schema.parse(data);
      setErrors({});
      setIsValid(true);
      return true;
    } catch (error) {
      if (error instanceof z.ZodError) {
        const newErrors: Record<string, string> = {};
        error.errors.forEach((err) => {
          if (err.path.length > 0) {
            newErrors[err.path[0].toString()] = err.message;
          }
        });
        setErrors(newErrors);
        setIsValid(false);
        return false;
      }
      return false;
    }
  }, [schema]);

  return {
    errors,
    isValid,
    validate,
    clearErrors: () => setErrors({}),
  };
}
```

### 4.3 Animation and Micro-interactions (Priority 4 - Day 5-7)

#### 4.3.1 Framer Motion Integration

```typescript
// components/ui/AnimatedCard.tsx - Animated glassmorphic card
import { motion } from 'framer-motion';
import { GlassmorphicCard } from './GlassmorphicCard';

interface AnimatedCardProps {
  children: React.ReactNode;
  delay?: number;
  direction?: 'up' | 'down' | 'left' | 'right';
  duration?: number;
}

export const AnimatedCard: React.FC<AnimatedCardProps> = ({
  children,
  delay = 0,
  direction = 'up',
  duration = 0.6,
}) => {
  const directionMap = {
    up: { y: 40, x: 0 },
    down: { y: -40, x: 0 },
    left: { x: 40, y: 0 },
    right: { x: -40, y: 0 },
  };

  return (
    <motion.div
      initial={{ 
        opacity: 0, 
        ...directionMap[direction] 
      }}
      whileInView={{ 
        opacity: 1, 
        x: 0, 
        y: 0 
      }}
      transition={{ 
        duration, 
        delay,
        ease: [0.21, 0.47, 0.32, 0.98] 
      }}
      viewport={{ once: true, margin: "-50px" }}
    >
      {children}
    </motion.div>
  );
};
```

## 5. Project Week 9-10: Production Polish (Overlap with Phase 5)

### 5.1 Performance Optimization (Priority 5 - Day 1-2)

#### 5.1.1 Code Splitting and Lazy Loading

```typescript
// Lazy load heavy components
import { lazy, Suspense } from 'react';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

const ChatInterface = lazy(() => import('@/components/chat/ChatInterface'));
const AnalyticsChart = lazy(() => import('@/components/dashboard/AnalyticsChart'));
const BiddingControlPanel = lazy(() => import('@/components/bidding/BiddingControlPanel'));

// Usage example
export function LazyLoadedComponent() {
  return (
    <Suspense fallback={<LoadingSpinner size="lg" />}>
      <ChatInterface />
    </Suspense>
  );
}
```

#### 5.1.2 Image Optimization

```typescript
// next.config.js - Image optimization
/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    domains: ['your-api-domain.com'],
    formats: ['image/webp', 'image/avif'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1440, 1920],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },
  experimental: {
    optimizeCss: true,
    optimizePackageImports: ['@heroicons/react'],
  },
};

module.exports = nextConfig;
```

### 5.2 Accessibility Implementation (Priority 5 - Day 3-4)

#### 5.2.1 Keyboard Navigation

```typescript
// hooks/useKeyboardNavigation.ts - Keyboard navigation support
import { useEffect, useCallback } from 'react';

export function useKeyboardNavigation(
  items: HTMLElement[],
  onSelect?: (index: number) => void
) {
  const [focusedIndex, setFocusedIndex] = useState(0);

  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    switch (event.key) {
      case 'ArrowDown':
      case 'ArrowRight':
        event.preventDefault();
        setFocusedIndex(prev => (prev + 1) % items.length);
        break;
      case 'ArrowUp':
      case 'ArrowLeft':
        event.preventDefault();
        setFocusedIndex(prev => (prev - 1 + items.length) % items.length);
        break;
      case 'Enter':
      case ' ':
        event.preventDefault();
        onSelect?.(focusedIndex);
        break;
      case 'Escape':
        setFocusedIndex(0);
        items[0]?.blur();
        break;
    }
  }, [items, focusedIndex, onSelect]);

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  useEffect(() => {
    items[focusedIndex]?.focus();
  }, [focusedIndex, items]);

  return focusedIndex;
}
```

#### 5.2.2 Screen Reader Support

```typescript
// components/ui/ScreenReaderOnly.tsx - Screen reader announcements
export const ScreenReaderOnly: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <span className="sr-only">
      {children}
    </span>
  );
};

// components/ui/LiveRegion.tsx - Live announcements
export const LiveRegion: React.FC<{
  message: string;
  politeness?: 'polite' | 'assertive';
}> = ({ message, politeness = 'polite' }) => {
  return (
    <div
      role="status"
      aria-live={politeness}
      aria-atomic="true"
      className="sr-only"
    >
      {message}
    </div>
  );
};
```

### 5.3 Testing Implementation (Priority 5 - Day 5-7)

#### 5.3.1 Component Testing Setup

```bash
# Install testing dependencies
npm install -D @testing-library/react@^13.0.0
npm install -D @testing-library/jest-dom@^6.0.0
npm install -D @testing-library/user-event@^14.0.0
npm install -D jest@^29.0.0
npm install -D jest-environment-jsdom@^29.0.0
```

#### 5.3.2 Example Component Test

```typescript
// __tests__/components/GlassmorphicCard.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { GlassmorphicCard } from '@/components/ui/GlassmorphicCard';

describe('GlassmorphicCard', () => {
  it('renders children correctly', () => {
    render(
      <GlassmorphicCard data-testid="test-card">
        <p>Test content</p>
      </GlassmorphicCard>
    );

    expect(screen.getByText('Test content')).toBeInTheDocument();
    expect(screen.getByTestId('test-card')).toBeInTheDocument();
  });

  it('applies interactive variant classes', () => {
    render(
      <GlassmorphicCard variant="interactive" data-testid="interactive-card">
        Content
      </GlassmorphicCard>
    );

    const card = screen.getByTestId('interactive-card');
    expect(card).toHaveClass('cursor-pointer');
  });

  it('handles click events', async () => {
    const handleClick = jest.fn();
    const user = userEvent.setup();

    render(
      <GlassmorphicCard onClick={handleClick} data-testid="clickable-card">
        Content
      </GlassmorphicCard>
    );

    await user.click(screen.getByTestId('clickable-card'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

## 6. Quality Assurance Checklist

### 6.1 Pixel-Perfect Verification

```typescript
// Quality assurance checklist for each component
const PixelPerfectChecklist = {
  colors: {
    gradients: [
      'Home page background matches Figma gradient exactly',
      'Leadership page uses black-to-gray gradient',
      'Border colors use #CED4DA and #E5E7EB',
    ],
    glassmorphism: [
      'Card backgrounds use rgba(255, 255, 255, 0.05)',
      'Border opacity matches Figma (0.1 for default)',
      'Backdrop blur is 12px for default cards',
    ],
  },
  dimensions: {
    pages: [
      'Home page: 1440px × 4765px',
      'Login page: 1440px × 1596px', 
      'Leadership page: 1440px × 1440px',
      'Talent page: 1440px × 1596px',
      'Bidding page: 1440px × 1596px',
    ],
    components: [
      'Navigation header: 78px height',
      'Border radius: 8px for frames, 12px for cards',
      'Border width: 2px for main borders',
    ],
  },
  typography: [
    'Inter font loads correctly',
    'Text hierarchy matches design specs',
    'Line heights and spacing are accurate',
  ],
  interactions: [
    'Hover states transform translateY(-2px)',
    'Transition duration: 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
    'Glass effects maintain blur on interaction',
  ],
};
```

### 6.2 Performance Targets

```typescript
const PerformanceTargets = {
  pageLoad: '<2 seconds initial load',
  interactions: '<100ms response time',
  animations: '60 FPS smooth animations',
  bundleSize: '<500KB gzipped main bundle',
  accessibility: 'WCAG 2.1 AA compliance',
  browserSupport: 'Chrome 90+, Firefox 88+, Safari 14+, Edge 90+',
};
```

## 7. Deployment Preparation

### 7.1 Build Optimization

```bash
# Production build commands
npm run build
npm run start

# Analyze bundle size
npx @next/bundle-analyzer

# Performance audit
npm install -g lighthouse
lighthouse http://localhost:3000 --output=json --output=html
```

### 7.2 Environment Configuration

```bash
# .env.local for development
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
NEXT_PUBLIC_ENVIRONMENT=development

# .env.production for production  
NEXT_PUBLIC_API_URL=https://api.onevice.com
NEXT_PUBLIC_WS_URL=wss://api.onevice.com/ws
NEXT_PUBLIC_ENVIRONMENT=production
```

---

*This implementation guide ensures systematic development of the OneVice frontend with pixel-perfect fidelity to Figma designs, aligned with the technical roadmap timeline and quality standards.*