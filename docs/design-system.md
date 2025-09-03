# OneVice Design System

**Version:** 1.0  
**Date:** September 1, 2025  
**Status:** Implementation Ready  
**Project:** OneVice AI-Powered Business Intelligence Hub

## 1. OneVice Branding

### 1.1 Project Identity
- **Project Name**: OneVice
- **Full Title**: OneVice AI-Powered Business Intelligence Hub
- **Design Philosophy**: Dark, modern, glassmorphic
- **Target Experience**: Professional, sophisticated, AI-native interface

### 1.2 Brand Guidelines
- **Tone**: Professional, cutting-edge, trustworthy
- **Visual Language**: Clean lines, subtle transparency, depth through layering
- **Interactive Style**: Smooth animations, responsive feedback, intuitive navigation
- **Accessibility**: WCAG 2.1 AA compliant, keyboard navigation, high contrast options

## 2. Color System

### 2.1 OneVice Primary Gradients

```css
/* Primary Background Gradients */
--gradient-primary: linear-gradient(90deg, rgba(10, 10, 11, 1) 0%, rgba(26, 26, 27, 1) 50%, rgba(17, 17, 17, 1) 100%);
--gradient-leadership: linear-gradient(90deg, rgba(0, 0, 0, 1) 0%, rgba(17, 17, 17, 1) 50%, rgba(0, 0, 0, 1) 100%);
--gradient-overlay: linear-gradient(90deg, rgba(0, 0, 0, 0) 40%, rgba(255, 255, 255, 0.01) 50%, rgba(0, 0, 0, 0) 60%);
--gradient-section: linear-gradient(90deg, rgba(255, 255, 255, 0.02) 0%, rgba(0, 0, 0, 0) 33%, rgba(255, 255, 255, 0.02) 67%, rgba(0, 0, 0, 0) 100%);
```

### 2.2 Glassmorphism System

```css
/* Glassmorphic Components */
--header-bg: rgba(30, 30, 30, 0.65);
--header-border: rgba(255, 255, 255, 0.1);
--backdrop-blur: 12px;

/* Card Backgrounds */
--card-bg: rgba(255, 255, 255, 0.05);
--card-border: rgba(255, 255, 255, 0.1);
--card-hover-bg: rgba(255, 255, 255, 0.08);

/* Modal & Dialog */
--modal-bg: rgba(20, 20, 20, 0.85);
--modal-border: rgba(255, 255, 255, 0.15);
```

### 2.3 Border System

```css
/* Border Colors */
--border-primary: #CED4DA;
--border-secondary: #E5E7EB;
--border-subtle: rgba(255, 255, 255, 0.1);
--border-accent: rgba(255, 255, 255, 0.2);

/* Border Widths */
--border-width-thin: 1px;
--border-width-medium: 2px;
--border-width-thick: 3px;
```

### 2.4 Text Colors

```css
/* Text Hierarchy */
--text-primary: rgba(255, 255, 255, 0.95);
--text-secondary: rgba(255, 255, 255, 0.75);
--text-tertiary: rgba(255, 255, 255, 0.55);
--text-muted: rgba(255, 255, 255, 0.35);

/* Accent Colors */
--text-accent: #60A5FA;
--text-success: #34D399;
--text-warning: #FBBF24;
--text-error: #F87171;
```

## 3. Layout System

### 3.1 Container Specifications

```css
/* Main Container */
--container-max-width: 1440px;
--container-padding: 2rem;

/* Page Layout */
--header-height: 78px;
--content-padding: 2rem;
--section-spacing: 4rem;

/* Responsive Breakpoints */
--breakpoint-mobile: 768px;
--breakpoint-tablet: 1024px;
--breakpoint-desktop: 1440px;
```

### 3.2 Page Specifications

#### Home Page
- **Total Height**: 4765px
- **Sections**: 6 total sections
- **Structure**:
  - Header: 78px (y: 0)
  - Hero Section: 600px (y: 78)
  - Section 2: 590px (y: 678)
  - Section 3: 902px (y: 1268)
  - Section 4: 807px (y: 2170)
  - Section 5: 764px (y: 2977)
  - Section 6: 605px (y: 3741)

#### Login Page
- **Total Height**: 1596px
- **Structure**:
  - Header: 78px
  - Main content area: 1518px
  - Footer section: 46px (y: 1472)

#### Leadership Dashboard
- **Total Height**: 1440px
- **Structure**:
  - Header: 78px
  - Dashboard content: 1367px (y: 70)

#### Talent Discovery & Bidding Pages
- **Total Height**: 1596px each
- **Structure**:
  - Header: 78px
  - Main interface: 1518px

### 3.3 Component Dimensions

```css
/* Border Radius */
--radius-small: 4px;
--radius-medium: 8px;
--radius-large: 12px;
--radius-xl: 16px;

/* Card Dimensions */
--card-padding: 1.5rem;
--card-gap: 1rem;
--card-min-height: 200px;

/* Form Elements */
--input-height: 48px;
--button-height: 48px;
--button-padding: 1rem 1.5rem;
```

## 4. Typography System

### 4.1 Font Stack

```css
/* Primary Font Family */
--font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
--font-family-mono: 'SF Mono', Consolas, 'Liberation Mono', Menlo, monospace;
```

### 4.2 Type Scale

```css
/* Heading Sizes */
--text-6xl: 3.75rem;  /* 60px */
--text-5xl: 3rem;     /* 48px */
--text-4xl: 2.25rem;  /* 36px */
--text-3xl: 1.875rem; /* 30px */
--text-2xl: 1.5rem;   /* 24px */
--text-xl: 1.25rem;   /* 20px */

/* Body Sizes */
--text-lg: 1.125rem;  /* 18px */
--text-base: 1rem;    /* 16px */
--text-sm: 0.875rem;  /* 14px */
--text-xs: 0.75rem;   /* 12px */

/* Line Heights */
--leading-none: 1;
--leading-tight: 1.25;
--leading-normal: 1.5;
--leading-relaxed: 1.625;
```

### 4.3 Font Weights

```css
--font-thin: 100;
--font-light: 300;
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
--font-extrabold: 800;
```

## 5. Component System

### 5.1 Button Variants

```css
/* Primary Button */
.btn-primary {
  background: linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%);
  color: var(--text-primary);
  border: none;
  border-radius: var(--radius-medium);
  padding: var(--button-padding);
  height: var(--button-height);
}

/* Secondary Button */
.btn-secondary {
  background: var(--card-bg);
  color: var(--text-secondary);
  border: 1px solid var(--border-subtle);
  backdrop-filter: blur(var(--backdrop-blur));
}

/* Ghost Button */
.btn-ghost {
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid transparent;
}
```

### 5.2 Glassmorphic Card

```css
.glassmorphic-card {
  background: var(--card-bg);
  backdrop-filter: blur(var(--backdrop-blur));
  border: 1px solid var(--card-border);
  border-radius: var(--radius-medium);
  padding: var(--card-padding);
  transition: all 0.3s ease;
}

.glassmorphic-card:hover {
  background: var(--card-hover-bg);
  border-color: var(--border-accent);
  transform: translateY(-2px);
}
```

### 5.3 Header Component

```css
.header {
  height: var(--header-height);
  background: var(--header-bg);
  backdrop-filter: blur(var(--backdrop-blur));
  border-bottom: 1px solid var(--header-border);
  position: sticky;
  top: 0;
  z-index: 100;
}
```

## 6. Animation System

### 6.1 Transition Timing

```css
/* Standard Transitions */
--transition-fast: 150ms ease;
--transition-normal: 300ms ease;
--transition-slow: 500ms ease;

/* Easing Functions */
--ease-in: cubic-bezier(0.4, 0, 1, 1);
--ease-out: cubic-bezier(0, 0, 0.2, 1);
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
--ease-bounce: cubic-bezier(0.68, -0.55, 0.265, 1.55);
```

### 6.2 Animation Presets

```css
/* Fade In */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* Slide Up */
@keyframes slideUp {
  from { 
    opacity: 0; 
    transform: translateY(20px); 
  }
  to { 
    opacity: 1; 
    transform: translateY(0); 
  }
}

/* Glass Shine Effect */
@keyframes glassShine {
  0% { 
    transform: translateX(-100%) skewX(-15deg); 
  }
  100% { 
    transform: translateX(200%) skewX(-15deg); 
  }
}
```

## 7. Dark Theme Specifications

### 7.1 Background Hierarchy

```css
/* Background Layers */
--bg-primary: #0A0A0B;      /* Darkest - main background */
--bg-secondary: #111111;    /* Card backgrounds */
--bg-tertiary: #1A1A1B;     /* Elevated elements */
--bg-quaternary: #262626;   /* Input fields, modals */

/* Surface Colors */
--surface-1: rgba(255, 255, 255, 0.02);
--surface-2: rgba(255, 255, 255, 0.05);
--surface-3: rgba(255, 255, 255, 0.08);
--surface-4: rgba(255, 255, 255, 0.12);
```

### 7.2 Interactive States

```css
/* Hover States */
--hover-overlay: rgba(255, 255, 255, 0.05);
--hover-border: rgba(255, 255, 255, 0.2);

/* Focus States */
--focus-ring: rgba(59, 130, 246, 0.5);
--focus-border: #3B82F6;

/* Active States */
--active-overlay: rgba(255, 255, 255, 0.1);
--active-border: rgba(255, 255, 255, 0.3);
```

## 8. Accessibility Guidelines

### 8.1 Color Contrast
- **Minimum Contrast**: 4.5:1 for normal text
- **Large Text**: 3:1 minimum contrast ratio
- **Interactive Elements**: Minimum 3:1 contrast with surrounding colors

### 8.2 Focus Management
- **Visible Focus Indicators**: All interactive elements must have clear focus states
- **Keyboard Navigation**: Tab order follows logical flow
- **Skip Links**: Provide skip-to-content options

### 8.3 Screen Reader Support
- **Semantic HTML**: Use proper heading hierarchy and ARIA labels
- **Alternative Text**: All images have descriptive alt text
- **State Announcements**: Dynamic content changes are announced

## 9. Implementation Notes

### 9.1 CSS Custom Properties Setup
```css
:root {
  /* Import all design tokens */
  @import './tokens/colors.css';
  @import './tokens/typography.css';
  @import './tokens/spacing.css';
  @import './tokens/animations.css';
}

/* Dark theme enforcement */
[data-theme="dark"] {
  color-scheme: dark;
}
```

### 9.2 Component Guidelines
- **Consistent Naming**: Use BEM methodology for CSS classes
- **Modular Architecture**: Each component should be self-contained
- **Responsive Design**: Mobile-first approach with graceful desktop enhancement
- **Performance**: Optimize animations for 60 FPS performance

## 10. Usage Examples

### 10.1 Basic Card Implementation
```tsx
<div className="glassmorphic-card">
  <h3 className="text-xl font-semibold text-primary mb-4">
    OneVice Dashboard
  </h3>
  <p className="text-secondary leading-relaxed">
    Access your AI-powered business intelligence tools.
  </p>
</div>
```

### 10.2 Header Implementation
```tsx
<header className="header">
  <div className="container mx-auto px-4 h-full flex items-center justify-between">
    <div className="text-2xl font-bold text-primary">OneVice</div>
    <nav className="flex items-center space-x-6">
      <a href="#" className="text-secondary hover:text-primary transition-colors">
        Dashboard
      </a>
      <button className="btn-primary">Login</button>
    </nav>
  </div>
</header>
```

---

**Document Status**: Ready for Implementation  
**Last Updated**: September 1, 2025  
**Next Review**: Upon completion of Phase 1 implementation