# OneVice Component Library Specifications

**Version:** 1.0  
**Date:** September 2, 2025  
**Status:** Implementation Ready  
**Framework:** Next.js 15.4 + React 19 + TypeScript 5.6  
**Dependencies:** design-specifications.md, page-specifications.md

## 1. Component Library Overview

This document defines the complete React component library for OneVice, providing reusable components that match the Figma design specifications exactly. All components support dark theme, glassmorphism effects, and accessibility standards.

## 2. Core Foundation Components

### 2.1 GlassmorphicCard Component

#### TypeScript Interface

```typescript
interface GlassmorphicCardProps {
  children: React.ReactNode;
  variant?: 'default' | 'elevated' | 'interactive' | 'modal' | 'kpi';
  size?: 'sm' | 'md' | 'lg' | 'xl';
  hover?: boolean;
  onClick?: () => void;
  className?: string;
  blurIntensity?: 'light' | 'medium' | 'heavy';
  border?: boolean;
  shadow?: 'none' | 'sm' | 'md' | 'lg';
  'data-testid'?: string;
}

interface GlassmorphicCardVariants {
  default: {
    background: 'rgba(255, 255, 255, 0.05)';
    border: 'rgba(255, 255, 255, 0.1)';
    backdropBlur: '12px';
    borderRadius: '12px';
  };
  elevated: {
    background: 'rgba(255, 255, 255, 0.08)';
    border: 'rgba(255, 255, 255, 0.15)';
    backdropBlur: '16px';
    borderRadius: '16px';
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)';
  };
  interactive: {
    background: 'rgba(255, 255, 255, 0.05)';
    border: 'rgba(255, 255, 255, 0.1)';
    backdropBlur: '12px';
    borderRadius: '12px';
    cursor: 'pointer';
    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
    hoverBackground: 'rgba(255, 255, 255, 0.08)';
    hoverBorder: 'rgba(255, 255, 255, 0.2)';
    hoverTransform: 'translateY(-2px)';
  };
  modal: {
    background: 'rgba(20, 20, 20, 0.85)';
    border: 'rgba(255, 255, 255, 0.15)';
    backdropBlur: '20px';
    borderRadius: '20px';
    boxShadow: '0 16px 64px rgba(0, 0, 0, 0.5)';
  };
  kpi: {
    background: 'rgba(255, 255, 255, 0.03)';
    border: 'rgba(255, 255, 255, 0.05)';
    backdropBlur: '8px';
    borderRadius: '12px';
    textAlign: 'center';
  };
}
```

#### Component Implementation

```tsx
// components/ui/GlassmorphicCard.tsx
import { cn } from '@/lib/utils';
import { forwardRef } from 'react';

export const GlassmorphicCard = forwardRef<
  HTMLDivElement,
  GlassmorphicCardProps
>(({
  children,
  variant = 'default',
  size = 'md',
  hover = false,
  onClick,
  className = '',
  blurIntensity = 'medium',
  border = true,
  shadow = 'none',
  'data-testid': testId,
  ...props
}, ref) => {
  const baseClasses = 'glassmorphic-card transition-all duration-300';
  
  const variantClasses = {
    default: 'bg-white/5 border-white/10 backdrop-blur-[12px] rounded-xl',
    elevated: 'bg-white/8 border-white/15 backdrop-blur-[16px] rounded-2xl shadow-glass-elevated',
    interactive: 'bg-white/5 border-white/10 backdrop-blur-[12px] rounded-xl cursor-pointer hover:bg-white/8 hover:border-white/20 hover:-translate-y-0.5',
    modal: 'bg-black/85 border-white/15 backdrop-blur-[20px] rounded-[20px] shadow-glass-modal',
    kpi: 'bg-white/3 border-white/5 backdrop-blur-[8px] rounded-xl text-center',
  };

  const sizeClasses = {
    sm: 'p-3',
    md: 'p-6',
    lg: 'p-8',
    xl: 'p-12',
  };

  const shadowClasses = {
    none: '',
    sm: 'shadow-glass-sm',
    md: 'shadow-glass-md',
    lg: 'shadow-glass-lg',
  };

  return (
    <div
      ref={ref}
      className={cn(
        baseClasses,
        variantClasses[variant],
        sizeClasses[size],
        shadowClasses[shadow],
        border && 'border',
        hover && 'hover:transform hover:scale-[1.02]',
        className
      )}
      onClick={onClick}
      data-testid={testId}
      {...props}
    >
      {children}
    </div>
  );
});

GlassmorphicCard.displayName = 'GlassmorphicCard';
```

### 2.2 NavigationHeader Component

#### TypeScript Interface

```typescript
interface NavigationHeaderProps {
  user?: {
    id: string;
    name: string;
    role: 'Leadership' | 'Director' | 'Salesperson' | 'Creative Director';
    avatar?: string;
  };
  currentPage?: 'home' | 'login' | 'leadership' | 'talent' | 'bidding';
  onNavigate?: (page: string) => void;
  onProfileClick?: () => void;
  onLogout?: () => void;
  className?: string;
}

interface NavigationItem {
  id: string;
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  roles?: string[];
  badge?: number;
}
```

#### Component Implementation

```tsx
// components/layout/NavigationHeader.tsx
import { cn } from '@/lib/utils';
import { GlassmorphicCard } from '@/components/ui/GlassmorphicCard';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';

export const NavigationHeader: React.FC<NavigationHeaderProps> = ({
  user,
  currentPage,
  onNavigate,
  onProfileClick,
  onLogout,
  className,
}) => {
  const navigationItems: NavigationItem[] = [
    {
      id: 'home',
      label: 'Home',
      href: '/',
      icon: HomeIcon,
    },
    {
      id: 'leadership',
      label: 'Leadership',
      href: '/leadership',
      icon: ChartBarIcon,
      roles: ['Leadership', 'Director'],
    },
    {
      id: 'talent',
      label: 'Talent Discovery',
      href: '/talent',
      icon: UsersIcon,
    },
    {
      id: 'bidding',
      label: 'Bidding',
      href: '/bidding',
      icon: CurrencyDollarIcon,
    },
  ];

  return (
    <header className={cn(
      'sticky top-0 z-50 w-full h-[78px]',
      'bg-gray-900/65 backdrop-blur-[12px]',
      'border-b border-white/10',
      className
    )}>
      <div className="flex items-center justify-between h-full px-6 max-w-[1440px] mx-auto">
        {/* Logo */}
        <div className="flex items-center">
          <OneViceLogo className="h-8 w-auto" />
          <span className="ml-3 text-xl font-bold text-white">OneVice</span>
        </div>

        {/* Navigation */}
        <nav className="hidden md:flex items-center space-x-1">
          {navigationItems.map((item) => {
            const isVisible = !item.roles || (user && item.roles.includes(user.role));
            const isActive = currentPage === item.id;
            
            if (!isVisible) return null;

            return (
              <button
                key={item.id}
                onClick={() => onNavigate?.(item.id)}
                className={cn(
                  'flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-all',
                  isActive
                    ? 'bg-white/10 text-white border border-white/20'
                    : 'text-white/75 hover:text-white hover:bg-white/5'
                )}
              >
                <item.icon className="w-4 h-4 mr-2" />
                {item.label}
                {item.badge && (
                  <span className="ml-2 px-2 py-0.5 bg-blue-500 text-white text-xs rounded-full">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* User Profile */}
        {user && (
          <div className="flex items-center space-x-4">
            <GlassmorphicCard
              variant="interactive"
              size="sm"
              onClick={onProfileClick}
              className="flex items-center space-x-3 px-3 py-2"
            >
              <Avatar className="h-8 w-8">
                <AvatarImage src={user.avatar} alt={user.name} />
                <AvatarFallback>{user.name.charAt(0)}</AvatarFallback>
              </Avatar>
              <div className="text-left">
                <div className="text-sm font-medium text-white">{user.name}</div>
                <div className="text-xs text-white/60">{user.role}</div>
              </div>
            </GlassmorphicCard>
          </div>
        )}
      </div>
    </header>
  );
};
```

### 2.3 ChatInterface Component

#### TypeScript Interface

```typescript
interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: string;
  agent?: 'sales_intelligence' | 'case_study' | 'talent_discovery' | 'bidding_support';
  status?: 'sending' | 'sent' | 'delivered' | 'error';
  metadata?: {
    confidence_score?: number;
    processing_time_ms?: number;
    sources?: string[];
    chunk_index?: number;
    total_chunks?: number;
  };
}

interface ChatInterfaceProps {
  threadId: string;
  userId: string;
  userRole: 'Leadership' | 'Director' | 'Salesperson' | 'Creative Director';
  initialMessages?: Message[];
  onMessageSend?: (message: string) => void;
  onAgentSelect?: (agent: string) => void;
  className?: string;
  autoFocus?: boolean;
  placeholder?: string;
  maxHeight?: string;
  enableFileUpload?: boolean;
  enableVoiceInput?: boolean;
  streamingEnabled?: boolean;
}
```

#### Component Implementation

```tsx
// components/chat/ChatInterface.tsx
import { useState, useRef, useEffect } from 'react';
import { GlassmorphicCard } from '@/components/ui/GlassmorphicCard';
import { MessageBubble } from './MessageBubble';
import { ChatInput } from './ChatInput';
import { AgentSelector } from './AgentSelector';

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  threadId,
  userId,
  userRole,
  initialMessages = [],
  onMessageSend,
  onAgentSelect,
  className,
  autoFocus = true,
  placeholder = "Ask OneVice AI anything...",
  maxHeight = "600px",
  enableFileUpload = true,
  enableVoiceInput = true,
  streamingEnabled = true,
}) => {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [isStreaming, setIsStreaming] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<string>('sales_intelligence');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (content: string) => {
    const newMessage: Message = {
      id: `msg_${Date.now()}`,
      content,
      role: 'user',
      timestamp: new Date().toISOString(),
      status: 'sending',
    };

    setMessages(prev => [...prev, newMessage]);
    onMessageSend?.(content);
  };

  return (
    <GlassmorphicCard
      variant="elevated"
      className={cn("flex flex-col h-full", className)}
      style={{ maxHeight }}
    >
      {/* Chat Header */}
      <div className="flex items-center justify-between p-4 border-b border-white/10">
        <div className="flex items-center space-x-3">
          <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse" />
          <h3 className="text-lg font-semibold text-white">OneVice AI</h3>
        </div>
        <AgentSelector
          selectedAgent={selectedAgent}
          onAgentChange={setSelectedAgent}
          userRole={userRole}
        />
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <MessageBubble
            key={message.id}
            message={message}
            isStreaming={isStreaming && message.role === 'assistant'}
          />
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Chat Input */}
      <div className="p-4 border-t border-white/10">
        <ChatInput
          onSend={handleSendMessage}
          placeholder={placeholder}
          autoFocus={autoFocus}
          enableFileUpload={enableFileUpload}
          enableVoiceInput={enableVoiceInput}
          disabled={isStreaming}
        />
      </div>
    </GlassmorphicCard>
  );
};
```

### 2.4 KPICard Component (Leadership Dashboard)

#### TypeScript Interface

```typescript
interface KPICardProps {
  title: string;
  value: string | number;
  unit?: string;
  trend?: {
    direction: 'up' | 'down' | 'neutral';
    percentage: number;
    period: string;
  };
  icon?: React.ComponentType<{ className?: string }>;
  color?: 'blue' | 'green' | 'yellow' | 'red' | 'purple';
  loading?: boolean;
  onClick?: () => void;
  className?: string;
}
```

#### Component Implementation

```tsx
// components/dashboard/KPICard.tsx
import { cn } from '@/lib/utils';
import { GlassmorphicCard } from '@/components/ui/GlassmorphicCard';
import { TrendingUpIcon, TrendingDownIcon } from '@heroicons/react/24/outline';

export const KPICard: React.FC<KPICardProps> = ({
  title,
  value,
  unit,
  trend,
  icon: Icon,
  color = 'blue',
  loading = false,
  onClick,
  className,
}) => {
  const colorMap = {
    blue: 'text-blue-400',
    green: 'text-green-400',
    yellow: 'text-yellow-400',
    red: 'text-red-400',
    purple: 'text-purple-400',
  };

  const trendColorMap = {
    up: 'text-green-400',
    down: 'text-red-400',
    neutral: 'text-gray-400',
  };

  return (
    <GlassmorphicCard
      variant="kpi"
      hover={!!onClick}
      onClick={onClick}
      className={cn("relative", className)}
    >
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/20 rounded-xl">
          <div className="w-6 h-6 border-2 border-white/30 border-t-white animate-spin rounded-full" />
        </div>
      )}

      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium text-white/60 uppercase tracking-wide">
            {title}
          </h3>
          {Icon && <Icon className="w-6 h-6 text-white/40" />}
        </div>

        {/* Value */}
        <div className="space-y-1">
          <div className="flex items-baseline justify-center space-x-1">
            <span className={cn("text-3xl font-bold", colorMap[color])}>
              {value}
            </span>
            {unit && (
              <span className="text-lg text-white/60 font-medium">{unit}</span>
            )}
          </div>

          {/* Trend */}
          {trend && (
            <div className="flex items-center justify-center space-x-1">
              {trend.direction === 'up' && (
                <TrendingUpIcon className="w-4 h-4 text-green-400" />
              )}
              {trend.direction === 'down' && (
                <TrendingDownIcon className="w-4 h-4 text-red-400" />
              )}
              <span className={cn("text-sm font-medium", trendColorMap[trend.direction])}>
                {trend.percentage}%
              </span>
              <span className="text-xs text-white/40">
                vs {trend.period}
              </span>
            </div>
          )}
        </div>
      </div>
    </GlassmorphicCard>
  );
};
```

## 3. Form Components

### 3.1 GlassmorphicInput Component

#### TypeScript Interface

```typescript
interface GlassmorphicInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  icon?: React.ComponentType<{ className?: string }>;
  variant?: 'default' | 'search' | 'pill';
  size?: 'sm' | 'md' | 'lg';
}
```

#### Component Implementation

```tsx
// components/form/GlassmorphicInput.tsx
import { forwardRef } from 'react';
import { cn } from '@/lib/utils';

export const GlassmorphicInput = forwardRef<
  HTMLInputElement,
  GlassmorphicInputProps
>(({
  label,
  error,
  icon: Icon,
  variant = 'default',
  size = 'md',
  className,
  ...props
}, ref) => {
  const variantClasses = {
    default: 'rounded-lg',
    search: 'rounded-full',
    pill: 'rounded-full px-6',
  };

  const sizeClasses = {
    sm: 'px-3 py-2 text-sm',
    md: 'px-4 py-3 text-base',
    lg: 'px-6 py-4 text-lg',
  };

  return (
    <div className="space-y-1">
      {label && (
        <label className="block text-sm font-medium text-white/80 mb-2">
          {label}
        </label>
      )}
      
      <div className="relative">
        {Icon && (
          <Icon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-white/40" />
        )}
        
        <input
          ref={ref}
          className={cn(
            'w-full bg-white/5 border border-white/10',
            'text-white placeholder-white/40',
            'backdrop-blur-[12px]',
            'focus:outline-none focus:ring-2 focus:ring-blue-400/30 focus:border-blue-400/50',
            'transition-all duration-300',
            variantClasses[variant],
            sizeClasses[size],
            Icon && 'pl-10',
            error && 'border-red-400/50 focus:border-red-400/70 focus:ring-red-400/30',
            className
          )}
          {...props}
        />
      </div>

      {error && (
        <p className="text-sm text-red-400 mt-1">{error}</p>
      )}
    </div>
  );
});

GlassmorphicInput.displayName = 'GlassmorphicInput';
```

### 3.2 PrimaryButton Component

#### TypeScript Interface

```typescript
interface PrimaryButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'success' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg' | 'xl';
  loading?: boolean;
  icon?: React.ComponentType<{ className?: string }>;
  iconPosition?: 'left' | 'right';
  fullWidth?: boolean;
}
```

#### Component Implementation

```tsx
// components/form/PrimaryButton.tsx
import { forwardRef } from 'react';
import { cn } from '@/lib/utils';

export const PrimaryButton = forwardRef<
  HTMLButtonElement,
  PrimaryButtonProps
>(({
  variant = 'primary',
  size = 'md',
  loading = false,
  icon: Icon,
  iconPosition = 'left',
  fullWidth = false,
  children,
  className,
  disabled,
  ...props
}, ref) => {
  const variantClasses = {
    primary: 'bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white shadow-blue-500/25',
    secondary: 'bg-white/10 hover:bg-white/20 text-white border border-white/20 hover:border-white/30',
    success: 'bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white shadow-green-500/25',
    danger: 'bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white shadow-red-500/25',
    ghost: 'hover:bg-white/5 text-white/80 hover:text-white',
  };

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2.5 text-base',
    lg: 'px-6 py-3 text-lg',
    xl: 'px-8 py-4 text-xl',
  };

  return (
    <button
      ref={ref}
      className={cn(
        'inline-flex items-center justify-center font-semibold rounded-xl',
        'transition-all duration-300 backdrop-blur-[12px]',
        'hover:transform hover:-translate-y-0.5 hover:shadow-lg',
        'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-transparent',
        'disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:transform-none',
        variantClasses[variant],
        sizeClasses[size],
        fullWidth && 'w-full',
        className
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading && (
        <div className="w-4 h-4 border-2 border-current border-t-transparent animate-spin rounded-full mr-2" />
      )}
      
      {Icon && iconPosition === 'left' && !loading && (
        <Icon className="w-5 h-5 mr-2" />
      )}
      
      {children}
      
      {Icon && iconPosition === 'right' && !loading && (
        <Icon className="w-5 h-5 ml-2" />
      )}
    </button>
  );
});

PrimaryButton.displayName = 'PrimaryButton';
```

## 4. Page-Specific Components

### 4.1 TalentCard Component

#### TypeScript Interface

```typescript
interface TalentProfile {
  id: string;
  name: string;
  role: string;
  company: string;
  avatar?: string;
  location: string;
  skills: string[];
  experience: number;
  rating: number;
  availability: 'available' | 'busy' | 'unavailable';
  hourlyRate?: number;
  portfolio: {
    projects: number;
    completionRate: number;
  };
}

interface TalentCardProps {
  profile: TalentProfile;
  onSelect?: (profile: TalentProfile) => void;
  onContact?: (profile: TalentProfile) => void;
  selected?: boolean;
  className?: string;
}
```

#### Component Implementation

```tsx
// components/talent/TalentCard.tsx
import { GlassmorphicCard } from '@/components/ui/GlassmorphicCard';
import { PrimaryButton } from '@/components/form/PrimaryButton';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { StarIcon, MapPinIcon } from '@heroicons/react/24/solid';

export const TalentCard: React.FC<TalentCardProps> = ({
  profile,
  onSelect,
  onContact,
  selected = false,
  className,
}) => {
  const availabilityColors = {
    available: 'bg-green-400',
    busy: 'bg-yellow-400',
    unavailable: 'bg-red-400',
  };

  return (
    <GlassmorphicCard
      variant={selected ? "elevated" : "interactive"}
      hover={!selected}
      onClick={() => onSelect?.(profile)}
      className={cn(
        "cursor-pointer transition-all duration-300",
        selected && "ring-2 ring-blue-400/50",
        className
      )}
    >
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-3">
            <div className="relative">
              <Avatar className="h-12 w-12">
                <AvatarImage src={profile.avatar} alt={profile.name} />
                <AvatarFallback>{profile.name.charAt(0)}</AvatarFallback>
              </Avatar>
              <div className={cn(
                "absolute -bottom-1 -right-1 w-4 h-4 rounded-full border-2 border-gray-900",
                availabilityColors[profile.availability]
              )} />
            </div>
            
            <div>
              <h3 className="text-lg font-semibold text-white">{profile.name}</h3>
              <p className="text-white/60">{profile.role}</p>
              <p className="text-sm text-white/40">{profile.company}</p>
            </div>
          </div>

          <div className="flex items-center space-x-1">
            <StarIcon className="w-4 h-4 text-yellow-400" />
            <span className="text-sm font-medium text-white">{profile.rating}</span>
          </div>
        </div>

        {/* Location */}
        <div className="flex items-center space-x-1 text-white/60">
          <MapPinIcon className="w-4 h-4" />
          <span className="text-sm">{profile.location}</span>
        </div>

        {/* Skills */}
        <div className="flex flex-wrap gap-2">
          {profile.skills.slice(0, 4).map((skill) => (
            <span
              key={skill}
              className="px-2 py-1 bg-white/10 text-white/80 text-xs rounded-md"
            >
              {skill}
            </span>
          ))}
          {profile.skills.length > 4 && (
            <span className="px-2 py-1 bg-white/5 text-white/60 text-xs rounded-md">
              +{profile.skills.length - 4} more
            </span>
          )}
        </div>

        {/* Stats */}
        <div className="flex justify-between text-sm">
          <div className="text-center">
            <div className="text-white font-medium">{profile.experience}y</div>
            <div className="text-white/60">Experience</div>
          </div>
          <div className="text-center">
            <div className="text-white font-medium">{profile.portfolio.projects}</div>
            <div className="text-white/60">Projects</div>
          </div>
          <div className="text-center">
            <div className="text-white font-medium">{profile.portfolio.completionRate}%</div>
            <div className="text-white/60">Success</div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex space-x-2 pt-2">
          <PrimaryButton
            variant="primary"
            size="sm"
            fullWidth
            onClick={(e) => {
              e.stopPropagation();
              onContact?.(profile);
            }}
          >
            Contact
          </PrimaryButton>
          <PrimaryButton
            variant="secondary"
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              onSelect?.(profile);
            }}
          >
            View Profile
          </PrimaryButton>
        </div>
      </div>
    </GlassmorphicCard>
  );
};
```

### 4.2 BiddingControlPanel Component

#### TypeScript Interface

```typescript
interface BiddingControlPanelProps {
  projectId: string;
  currentBid?: number;
  minimumBid: number;
  timeRemaining: number;
  userBid?: number;
  onSubmitBid: (amount: number) => void;
  onWithdrawBid: () => void;
  disabled?: boolean;
  loading?: boolean;
}
```

#### Component Implementation

```tsx
// components/bidding/BiddingControlPanel.tsx
import { useState } from 'react';
import { GlassmorphicCard } from '@/components/ui/GlassmorphicCard';
import { PrimaryButton } from '@/components/form/PrimaryButton';
import { GlassmorphicInput } from '@/components/form/GlassmorphicInput';

export const BiddingControlPanel: React.FC<BiddingControlPanelProps> = ({
  projectId,
  currentBid,
  minimumBid,
  timeRemaining,
  userBid,
  onSubmitBid,
  onWithdrawBid,
  disabled = false,
  loading = false,
}) => {
  const [bidAmount, setBidAmount] = useState<string>('');
  const [error, setError] = useState<string>('');

  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleSubmitBid = () => {
    const amount = parseFloat(bidAmount);
    
    if (isNaN(amount) || amount < minimumBid) {
      setError(`Minimum bid is $${minimumBid.toLocaleString()}`);
      return;
    }
    
    if (currentBid && amount <= currentBid) {
      setError(`Bid must be higher than current bid of $${currentBid.toLocaleString()}`);
      return;
    }

    setError('');
    onSubmitBid(amount);
    setBidAmount('');
  };

  return (
    <div className="space-y-4">
      {/* Time Remaining */}
      <GlassmorphicCard variant="elevated" className="text-center">
        <div className="flex items-center justify-center space-x-2 mb-2">
          <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
          <span className="text-sm text-white/60">Time Remaining</span>
        </div>
        <div className="text-2xl font-bold text-yellow-400">
          {formatTime(timeRemaining)}
        </div>
      </GlassmorphicCard>

      {/* Current Bid */}
      {currentBid && (
        <GlassmorphicCard variant="default">
          <div className="text-center">
            <div className="text-sm text-white/60 mb-1">Current Highest Bid</div>
            <div className="text-xl font-bold text-green-400">
              ${currentBid.toLocaleString()}
            </div>
          </div>
        </GlassmorphicCard>
      )}

      {/* Bid Input */}
      <GlassmorphicCard variant="elevated">
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-white">Place Your Bid</h3>
          
          <GlassmorphicInput
            type="number"
            value={bidAmount}
            onChange={(e) => setBidAmount(e.target.value)}
            placeholder={`Minimum: $${minimumBid.toLocaleString()}`}
            error={error}
            disabled={disabled || loading}
            size="lg"
          />

          <div className="flex space-x-2">
            <PrimaryButton
              variant="success"
              size="lg"
              fullWidth
              onClick={handleSubmitBid}
              loading={loading}
              disabled={disabled || !bidAmount}
            >
              Submit Bid
            </PrimaryButton>
            
            {userBid && (
              <PrimaryButton
                variant="danger"
                size="lg"
                onClick={onWithdrawBid}
                disabled={disabled || loading}
              >
                Withdraw
              </PrimaryButton>
            )}
          </div>
        </div>
      </GlassmorphicCard>
    </div>
  );
};
```

## 5. Utility Components

### 5.1 LoadingSpinner Component

```tsx
// components/ui/LoadingSpinner.tsx
interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  color?: 'white' | 'blue' | 'green' | 'yellow' | 'red';
  className?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  color = 'white',
  className,
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
    xl: 'w-12 h-12',
  };

  const colorClasses = {
    white: 'border-white/30 border-t-white',
    blue: 'border-blue-200 border-t-blue-500',
    green: 'border-green-200 border-t-green-500',
    yellow: 'border-yellow-200 border-t-yellow-500',
    red: 'border-red-200 border-t-red-500',
  };

  return (
    <div
      className={cn(
        'animate-spin rounded-full border-2',
        sizeClasses[size],
        colorClasses[color],
        className
      )}
    />
  );
};
```

### 5.2 EmptyState Component

```tsx
// components/ui/EmptyState.tsx
interface EmptyStateProps {
  icon?: React.ComponentType<{ className?: string }>;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon: Icon,
  title,
  description,
  action,
  className,
}) => {
  return (
    <div className={cn("text-center py-12", className)}>
      {Icon && (
        <Icon className="w-16 h-16 text-white/20 mx-auto mb-4" />
      )}
      
      <h3 className="text-xl font-semibold text-white mb-2">{title}</h3>
      
      {description && (
        <p className="text-white/60 mb-6 max-w-sm mx-auto">{description}</p>
      )}
      
      {action && (
        <PrimaryButton onClick={action.onClick}>
          {action.label}
        </PrimaryButton>
      )}
    </div>
  );
};
```

## 6. Tailwind CSS Configuration

### 6.1 Custom Tailwind Classes

```javascript
// tailwind.config.js additions
module.exports = {
  theme: {
    extend: {
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
};
```

## 7. Component Export Index

```tsx
// components/index.ts
export { GlassmorphicCard } from './ui/GlassmorphicCard';
export { NavigationHeader } from './layout/NavigationHeader';
export { ChatInterface } from './chat/ChatInterface';
export { KPICard } from './dashboard/KPICard';
export { GlassmorphicInput } from './form/GlassmorphicInput';
export { PrimaryButton } from './form/PrimaryButton';
export { TalentCard } from './talent/TalentCard';
export { BiddingControlPanel } from './bidding/BiddingControlPanel';
export { LoadingSpinner } from './ui/LoadingSpinner';
export { EmptyState } from './ui/EmptyState';
```

---

*This component library provides all necessary components for pixel-perfect implementation of the OneVice Figma designs, with full TypeScript support, accessibility compliance, and responsive design patterns.*