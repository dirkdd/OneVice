# OneVice Frontend Development Roadmap

**Version:** 1.0  
**Date:** September 2, 2025  
**Status:** Implementation Ready  
**Dependencies:** technical-roadmap.md, frontend/design-specifications.md  
**Framework:** Next.js 15.4 + React 19 + TypeScript 5.6

## 1. Frontend Development Overview

This roadmap provides a detailed 2-week frontend development timeline that integrates with the main technical roadmap **Phase 3: Frontend Development (Weeks 5-6)**. The frontend development runs parallel to advanced backend features and ensures pixel-perfect Figma implementation.

### 1.1 Integration with Main Roadmap

```
Main Project Timeline:
├── Phase 1: Foundation (Weeks 1-2) - Infrastructure, Auth, Database
├── Phase 2: AI System (Weeks 3-5) - LangGraph, Agents, Memory
├── Phase 3: Frontend Development (Weeks 5-6) ← THIS ROADMAP
├── Phase 4: Advanced Features (Weeks 7-8) - Vector Search, Integration
└── Phase 5: Production (Weeks 9-10) - Deployment, Monitoring
```

### 1.2 Critical Success Metrics

- **Pixel-Perfect Fidelity**: 100% visual match to Figma designs
- **Performance**: <2s page load, 60fps animations, <100ms interactions
- **Accessibility**: WCAG 2.1 AA compliance across all components
- **Integration**: Seamless backend API integration with error handling
- **Responsive**: Mobile-first design with 768px, 1024px, 1440px breakpoints

## 2. Week 5: Foundation and Static Pages

### 2.1 Monday (Week 5, Day 1): Environment and Design System

#### Morning (9:00-12:00): Project Setup
```bash
# Verify Next.js 15.4 installation and dependencies
cd frontend
npm list next  # Verify next@15.4.0
npm list react  # Verify react@19.x

# Install OneVice design system dependencies
npm install @headlessui/react@^1.7.0
npm install @heroicons/react@^2.0.0  
npm install class-variance-authority@^0.7.0
npm install clsx@^2.0.0
npm install tailwind-merge@^2.0.0
npm install framer-motion@^10.16.0

# Install form and validation libraries
npm install react-hook-form@^7.45.0
npm install @hookform/resolvers@^3.3.0
npm install zod@^3.22.0

# Install testing dependencies
npm install -D @testing-library/react@^14.0.0
npm install -D @testing-library/jest-dom@^6.1.0
npm install -D @testing-library/user-event@^14.4.0
```

#### Afternoon (13:00-17:00): Design System Configuration
```javascript
// tailwind.config.js - OneVice configuration
module.exports = {
  content: ['./app/**/*.{js,ts,jsx,tsx,mdx}', './components/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        serif: ['Flood Std', 'Georgia', 'serif'],
      },
      backgroundImage: {
        'gradient-home': 'linear-gradient(90deg, rgba(10, 10, 11, 1) 0%, rgba(26, 26, 27, 1) 50%, rgba(17, 17, 17, 1) 100%)',
        'gradient-leadership': 'linear-gradient(90deg, rgba(0, 0, 0, 1) 0%, rgba(17, 17, 17, 1) 50%, rgba(0, 0, 0, 1) 100%)',
      },
      backdropBlur: {
        'xs': '2px', 'sm': '4px', 'md': '12px', 'lg': '16px', 'xl': '20px',
      },
      boxShadow: {
        'glass-elevated': '0 8px 32px rgba(0, 0, 0, 0.3)',
        'glass-modal': '0 16px 64px rgba(0, 0, 0, 0.5)',
      },
    },
  },
};
```

**Deliverables:**
- ✅ Environment configured with all dependencies
- ✅ Tailwind configured with OneVice design tokens
- ✅ Font loading (Inter + Flood Std) implemented
- ✅ CSS custom properties for Figma values

### 2.2 Tuesday (Week 5, Day 2): Core Components

#### Morning (9:00-12:00): GlassmorphicCard Component
```typescript
// components/ui/GlassmorphicCard.tsx
interface GlassmorphicCardProps {
  variant?: 'default' | 'elevated' | 'interactive' | 'modal' | 'kpi';
  size?: 'sm' | 'md' | 'lg' | 'xl';
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}

export const GlassmorphicCard: React.FC<GlassmorphicCardProps> = ({
  variant = 'default',
  size = 'md',
  children,
  className,
  onClick,
}) => {
  const variants = {
    default: 'bg-white/5 backdrop-blur-[12px] border-white/10',
    elevated: 'bg-white/8 backdrop-blur-[16px] border-white/15 shadow-glass-elevated',
    interactive: 'bg-white/5 backdrop-blur-[12px] border-white/10 hover:bg-white/8 hover:border-white/20 hover:-translate-y-0.5 cursor-pointer',
    modal: 'bg-black/85 backdrop-blur-[20px] border-white/15 shadow-glass-modal',
    kpi: 'bg-white/3 backdrop-blur-[8px] border-white/5 text-center',
  };

  const sizes = {
    sm: 'p-3', md: 'p-6', lg: 'p-8', xl: 'p-12',
  };

  return (
    <div
      className={cn(
        'border rounded-xl transition-all duration-300',
        variants[variant],
        sizes[size],
        className
      )}
      onClick={onClick}
    >
      {children}
    </div>
  );
};
```

#### Afternoon (13:00-17:00): Navigation and Layout
```typescript
// components/layout/NavigationHeader.tsx
interface NavigationHeaderProps {
  user?: { name: string; role: UserRole; avatar?: string };
  currentPage?: 'home' | 'login' | 'leadership' | 'talent' | 'bidding';
}

export const NavigationHeader: React.FC<NavigationHeaderProps> = ({ user, currentPage }) => {
  return (
    <header className="sticky top-0 z-50 w-full h-[78px] bg-gray-900/65 backdrop-blur-[12px] border-b border-white/10">
      <div className="flex items-center justify-between h-full px-6 max-w-[1440px] mx-auto">
        {/* Logo */}
        <div className="flex items-center">
          <OneViceLogo className="h-8 w-auto" />
          <span className="ml-3 text-xl font-bold text-white">OneVice</span>
        </div>

        {/* Navigation */}
        <nav className="hidden md:flex items-center space-x-1">
          {/* Navigation items based on user role */}
        </nav>

        {/* User Profile */}
        {user && (
          <UserProfileDropdown user={user} />
        )}
      </div>
    </header>
  );
};
```

**Deliverables:**
- ✅ GlassmorphicCard with all variants implemented
- ✅ NavigationHeader with RBAC integration
- ✅ Layout components (PageContainer, Section)
- ✅ Component tests written and passing

### 2.3 Wednesday (Week 5, Day 3): Page Layouts

#### Morning (9:00-12:00): Home Page Implementation
```typescript
// app/page.tsx - Home page (1440x4765px)
export default function HomePage() {
  return (
    <div className="min-h-screen">
      <div 
        className="w-full max-w-[1440px] mx-auto bg-gradient-home"
        style={{ minHeight: '4765px' }} // Exact Figma height
      >
        <NavigationHeader currentPage="home" />
        
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
              <PrimaryButton variant="primary" size="lg">Get Started</PrimaryButton>
              <PrimaryButton variant="secondary" size="lg">Watch Demo</PrimaryButton>
            </div>
          </div>
        </section>

        {/* Feature sections with exact spacing */}
      </div>
    </div>
  );
}
```

#### Afternoon (13:00-17:00): Login Page Implementation  
```typescript
// app/login/page.tsx - Login page (1440x1596px)
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

**Deliverables:**
- ✅ Home page with exact 4765px height and Figma gradients
- ✅ Login page with centered modal layout
- ✅ Responsive design for mobile/tablet breakpoints
- ✅ Navigation integration with page states

### 2.4 Thursday (Week 5, Day 4): Dashboard Pages

#### Morning (9:00-12:00): Leadership Dashboard
```typescript
// app/leadership/page.tsx - Square layout (1440x1440px)
export default function LeadershipPage() {
  return (
    <div 
      className="w-full max-w-[1440px] mx-auto bg-gradient-leadership"
      style={{ minHeight: '1440px' }} // Exact square Figma layout
    >
      <NavigationHeader currentPage="leadership" />
      
      {/* Executive Header */}
      <div className="h-[120px] bg-black/80 backdrop-blur-md border-b border-white/5 px-12 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Executive Dashboard</h1>
          <p className="text-white/60">Real-time business intelligence overview</p>
        </div>
      </div>

      {/* KPI Grid */}
      <div className="p-12">
        <div className="grid grid-cols-4 gap-8 mb-8">
          {kpiMetrics.map((kpi) => (
            <KPICard key={kpi.id} {...kpi} />
          ))}
        </div>
      </div>
    </div>
  );
}
```

#### Afternoon (13:00-17:00): Talent and Bidding Pages
```typescript
// app/talent/page.tsx - Talent discovery (1440x1596px)
// app/bidding/page.tsx - Bidding platform (1440x1596px)

// Both pages use standard 1596px height with search/control interfaces
```

**Deliverables:**
- ✅ Leadership dashboard with square 1440px layout
- ✅ Talent discovery page with search interface layout
- ✅ Bidding platform page with control panel layout
- ✅ All pages match exact Figma dimensions

### 2.5 Friday (Week 5, Day 5): Form Components and Polish

#### Morning (9:00-12:00): Form Components
```typescript
// components/form/GlassmorphicInput.tsx
// components/form/PrimaryButton.tsx
// components/form/FormField.tsx

// Comprehensive form system with validation
```

#### Afternoon (13:00-17:00): Testing and Polish
```bash
# Run test suite
npm run test

# Visual regression testing
npm run test:visual

# Performance testing
npm run lighthouse

# Accessibility testing  
npm run test:a11y
```

**Deliverables:**
- ✅ Complete form component library
- ✅ All tests passing (unit + integration)
- ✅ Performance audit passing
- ✅ Accessibility compliance validated

## 3. Week 6: Interactive Features and Integration

### 3.1 Monday (Week 6, Day 1): AI Interface Components

#### Morning (9:00-12:00): ChatInterface Component
```typescript
// components/chat/ChatInterface.tsx
interface ChatInterfaceProps {
  threadId: string;
  userId: string;
  userRole: UserRole;
  onMessageSend?: (message: string) => void;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  threadId, userId, userRole, onMessageSend
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);

  return (
    <GlassmorphicCard variant="elevated" className="flex flex-col h-full">
      {/* Chat header with agent selector */}
      <div className="flex items-center justify-between p-4 border-b border-white/10">
        <AgentSelector userRole={userRole} />
        <LiveIndicator isConnected={true} />
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
      </div>

      {/* Input */}
      <ChatInput onSend={onMessageSend} disabled={isStreaming} />
    </GlassmorphicCard>
  );
};
```

#### Afternoon (13:00-17:00): Dashboard Components
```typescript
// components/dashboard/KPICard.tsx
// components/dashboard/AnalyticsChart.tsx
// components/dashboard/MetricsBadge.tsx
```

**Deliverables:**
- ✅ ChatInterface with streaming message support
- ✅ Dashboard KPI cards with trend indicators
- ✅ Agent selector with role-based filtering
- ✅ Message bubbles with metadata display

### 3.2 Tuesday (Week 6, Day 2): Real-time Features

#### Morning (9:00-12:00): WebSocket Integration
```typescript
// hooks/useWebSocket.ts
export function useWebSocket(url: string, userId: string) {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);

  useEffect(() => {
    const ws = new WebSocket(`${url}?userId=${userId}`);
    
    ws.onopen = () => {
      setIsConnected(true);
      setSocket(ws);
    };

    ws.onmessage = (event) => {
      const message: WebSocketMessage = JSON.parse(event.data);
      setMessages(prev => [...prev, message]);
    };

    ws.onclose = () => {
      setIsConnected(false);
      // Auto-reconnect logic
    };

    return () => ws.close();
  }, [url, userId]);

  return { socket, isConnected, messages };
}
```

#### Afternoon (13:00-17:00): Bidding Components
```typescript
// components/bidding/BiddingControlPanel.tsx
// components/bidding/LiveBidTracker.tsx
// components/bidding/TimeRemaining.tsx
```

**Deliverables:**
- ✅ WebSocket hook with auto-reconnection
- ✅ Real-time bid tracking components
- ✅ Live timer with countdown display
- ✅ Connection status indicators

### 3.3 Wednesday (Week 6, Day 3): Backend Integration

#### Morning (9:00-12:00): API Integration
```typescript
// hooks/useAPI.ts
export function useAPI() {
  const { getToken } = useAuth();

  const apiClient = useMemo(() => 
    axios.create({
      baseURL: process.env.NEXT_PUBLIC_API_URL,
      timeout: 10000,
      headers: {
        'Authorization': `Bearer ${getToken()}`,
        'Content-Type': 'application/json',
      },
    })
  , [getToken]);

  return {
    agents: {
      sales: (query: string) => apiClient.post('/agents/sales', { query }),
      talent: (filters: TalentFilters) => apiClient.post('/agents/talent', filters),
      bidding: (project: string) => apiClient.get(`/agents/bidding/${project}`),
      leadership: (metrics: string[]) => apiClient.get('/agents/leadership', { params: { metrics } }),
    },
    auth: {
      profile: () => apiClient.get('/auth/profile'),
      permissions: () => apiClient.get('/auth/permissions'),
    },
  };
}
```

#### Afternoon (13:00-17:00): Error Handling and Loading States
```typescript
// hooks/useApiWithState.ts
export function useApiWithState<T>(apiCall: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const execute = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await apiCall();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    } finally {
      setLoading(false);
    }
  }, [apiCall]);

  return { data, loading, error, execute };
}
```

**Deliverables:**
- ✅ Complete API integration with authentication
- ✅ Error handling with user-friendly messages
- ✅ Loading states for all async operations
- ✅ Retry logic for failed requests

### 3.4 Thursday (Week 6, Day 4): Talent Discovery Features

#### Morning (9:00-12:00): TalentCard Component
```typescript
// components/talent/TalentCard.tsx
interface TalentCardProps {
  profile: TalentProfile;
  onSelect?: (profile: TalentProfile) => void;
  onContact?: (profile: TalentProfile) => void;
  selected?: boolean;
}

export const TalentCard: React.FC<TalentCardProps> = ({
  profile, onSelect, onContact, selected = false
}) => {
  return (
    <GlassmorphicCard
      variant={selected ? "elevated" : "interactive"}
      hover={!selected}
      onClick={() => onSelect?.(profile)}
      className={cn("cursor-pointer", selected && "ring-2 ring-blue-400/50")}
    >
      {/* Profile header with avatar and availability */}
      {/* Skills and experience display */}
      {/* Action buttons */}
    </GlassmorphicCard>
  );
};
```

#### Afternoon (13:00-17:00): Search and Filter System
```typescript
// components/talent/TalentSearch.tsx
// components/talent/TalentFilters.tsx
// hooks/useTalentSearch.ts
```

**Deliverables:**
- ✅ TalentCard with hover states and selection
- ✅ Search interface with real-time filtering
- ✅ Advanced filters (skills, location, availability)
- ✅ Pagination for large result sets

### 3.5 Friday (Week 6, Day 5): Integration Testing and Polish

#### Morning (9:00-12:00): Integration Testing
```bash
# End-to-end testing
npm run test:e2e

# Integration testing with backend APIs
npm run test:integration

# Performance testing under load
npm run test:performance
```

#### Afternoon (13:00-17:00): Final Polish and Optimization
```typescript
// Performance optimizations
// Lazy loading implementation
// Bundle size optimization
// Final accessibility audit
```

**Deliverables:**
- ✅ All integration tests passing
- ✅ Performance benchmarks met
- ✅ Bundle size optimized (<500KB gzipped)
- ✅ Full accessibility compliance

## 4. Quality Assurance Checklist

### 4.1 Visual Fidelity Verification
- [ ] Home page: 1440×4765px with exact Figma gradients
- [ ] Login page: 1440×1596px centered modal layout  
- [ ] Leadership: 1440×1440px square with leadership gradient
- [ ] Talent/Bidding: 1440×1596px with correct layouts
- [ ] Border colors: #CED4DA (frames), #E5E7EB (containers)
- [ ] Glassmorphism: backdrop-blur-[12px] default, proper opacity
- [ ] Typography: Inter font loaded, correct hierarchy

### 4.2 Performance Validation
- [ ] Page load: <2 seconds initial load
- [ ] Interactions: <100ms response time
- [ ] Animations: 60 FPS smooth animations
- [ ] Bundle size: <500KB gzipped main bundle
- [ ] Core Web Vitals: LCP <2.5s, FID <100ms, CLS <0.1

### 4.3 Integration Testing
- [ ] Authentication flow: Clerk + RBAC working
- [ ] API calls: All endpoints responding correctly
- [ ] WebSocket: Real-time updates functioning
- [ ] Error handling: Graceful error states displayed
- [ ] Loading states: Proper loading indicators

### 4.4 Accessibility Compliance
- [ ] WCAG 2.1 AA compliance across all pages
- [ ] Keyboard navigation working
- [ ] Screen reader compatibility
- [ ] Color contrast ratios meeting standards
- [ ] Focus management proper

## 5. Risk Mitigation and Contingencies

### 5.1 Backend API Delays
**Risk**: Backend APIs not ready by Week 5
**Mitigation**: 
- Implement mock APIs for frontend development
- Use MSW (Mock Service Worker) for realistic API simulation
- Prioritize static page development first

### 5.2 Figma Design Changes
**Risk**: Design updates during development
**Mitigation**:
- Lock Figma designs before Week 5 start
- Use design tokens for easy updates
- Maintain design-code mapping document

### 5.3 Performance Issues
**Risk**: Glassmorphism effects causing performance problems
**Mitigation**:
- Implement fallbacks for unsupported browsers
- Use feature detection for backdrop-filter
- Optimize CSS with will-change properties

### 5.4 Integration Complexity
**Risk**: Backend-frontend integration taking longer than expected
**Mitigation**:
- Plan integration points in advance
- Use TypeScript interfaces shared between teams
- Implement comprehensive error boundaries

## 6. Success Metrics

### 6.1 Development Metrics
- **Code Coverage**: >90% test coverage
- **Component Completion**: 100% of specified components
- **Page Implementation**: 5/5 pages pixel-perfect
- **Integration Points**: All backend APIs connected

### 6.2 Quality Metrics
- **Performance Score**: >90 Lighthouse score
- **Accessibility Score**: 100% WCAG 2.1 AA compliance
- **Visual Regression**: 0% pixel diff from Figma
- **Cross-browser**: Support Chrome 90+, Firefox 88+, Safari 14+

---

**Document Status**: Frontend Roadmap Complete  
**Dependencies**: Requires technical-roadmap.md and backend API specifications  
**Execution**: Ready for Week 5 implementation start  
**Review Required**: Design and backend team alignment confirmation