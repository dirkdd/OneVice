# OneVice Frontend Design Specifications - Figma Implementation

**Version:** 1.0  
**Date:** September 2, 2025  
**Status:** Implementation Ready  
**Source:** Figma Design - OneVice AI Hub  
**Figma URL:** https://www.figma.com/design/ZQFiaavkorum7oSDGJnW6d/OneVice-AI-Hub

## 1. Design System Overview

This document provides pixel-perfect specifications extracted from the OneVice AI Hub Figma design for exact implementation. All measurements, colors, and effects have been precisely documented to ensure visual fidelity.

### 1.1 Canvas Specifications
- **Total Pages:** 5 (Home, Login, Leadership, Talent Discovery, Bidding)
- **Base Width:** 1440px (desktop-first approach)
- **Base Border Radius:** 8px (frame level)
- **Border Style:** 2px solid

## 2. Color System - Exact Figma Values

### 2.1 Background Gradients (Primary System)

```css
/* Home Page Gradient */
--gradient-home: linear-gradient(90deg, rgba(10, 10, 11, 1) 0%, rgba(26, 26, 27, 1) 50%, rgba(17, 17, 17, 1) 100%);

/* Leadership Page Gradient */
--gradient-leadership: linear-gradient(90deg, rgba(0, 0, 0, 1) 0%, rgba(17, 17, 17, 1) 50%, rgba(0, 0, 0, 1) 100%);

/* Standard Page Background */
--bg-standard: #FFFFFF;
```

### 2.2 Border System - Exact Figma Colors

```css
/* Primary Border Colors (from Figma) */
--border-primary: #CED4DA;    /* Used for main frame borders */
--border-secondary: #E5E7EB;  /* Used for body container borders */

/* Border Specifications */
--border-width: 2px;          /* Standard border width */
--border-style: solid;        /* Standard border style */
```

### 2.3 Frame Fill System

```css
/* Frame Fill - Overlay Effect */
--frame-fill-overlay: rgba(0, 0, 0, 0.2), #FFFFFF;  /* Dual-layer fill system */

/* Body Container Background */
--body-bg-gradient: linear-gradient(90deg, rgba(10, 10, 11, 1) 0%, rgba(26, 26, 27, 1) 50%, rgba(17, 17, 17, 1) 100%);
--body-bg-leadership: linear-gradient(90deg, rgba(0, 0, 0, 1) 0%, rgba(17, 17, 17, 1) 50%, rgba(0, 0, 0, 1) 100%);
```

## 3. Layout System - Figma Measurements

### 3.1 Page Dimensions (Exact Figma Values)

```css
/* Home Page */
--home-width: 1440px;
--home-height: 4765px;    /* Extended page with multiple sections */

/* Login Page */
--login-width: 1440px;
--login-height: 1596px;

/* Leadership Dashboard */
--leadership-width: 1440px;
--leadership-height: 1440px; /* Square layout */

/* Talent Discovery */
--talent-width: 1440px;
--talent-height: 1596px;

/* Bidding Platform */
--bidding-width: 1440px;
--bidding-height: 1596px;
```

### 3.2 Layout Modes (From Figma Auto Layout)

```css
/* Column Layout (Primary) */
--layout-mode: column;
--layout-sizing-horizontal: hug;  /* Hug contents horizontally */
--layout-sizing-vertical: hug;    /* Hug contents vertically */

/* Body Container Layout */
--body-layout-mode: none;         /* Absolute positioning */
--body-sizing-horizontal: fixed;  /* Fixed width containers */
--body-sizing-vertical: fixed;    /* Fixed height containers */
```

### 3.3 Container Specifications

```css
/* Main Frame Container */
.main-frame {
  display: flex;
  flex-direction: column;
  width: fit-content;
  height: fit-content;
  padding: 0;
  border-radius: 8px;
  border: 2px solid #CED4DA;
  background: linear-gradient(rgba(0, 0, 0, 0.2), #FFFFFF);
}

/* Body Container */
.body-container {
  position: relative;
  width: 1440px;
  min-height: var(--page-height);
  border: 2px solid #E5E7EB;
  background: var(--body-bg-gradient);
}
```

## 4. Typography System

### 4.1 Font Family Specifications

```css
/* Primary Font Stack */
--font-primary: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;

/* Secondary Font Stack */
--font-secondary: 'Flood Std', Georgia, serif;

/* Font Loading */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
```

### 4.2 Text Hierarchy

```css
/* Text Colors for Dark Theme */
--text-primary: rgba(255, 255, 255, 0.95);
--text-secondary: rgba(255, 255, 255, 0.75);
--text-tertiary: rgba(255, 255, 255, 0.55);
--text-muted: rgba(255, 255, 255, 0.35);

/* Typography Scale */
--text-h1: clamp(2.5rem, 4vw, 4rem);
--text-h2: clamp(2rem, 3vw, 3rem);
--text-h3: clamp(1.5rem, 2.5vw, 2.5rem);
--text-body: 1rem;
--text-small: 0.875rem;
--text-xs: 0.75rem;
```

## 5. Glassmorphism Effects - Figma Implementation

### 5.1 Base Glassmorphic System

```css
/* Primary Glassmorphism */
.glassmorphic-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
}

/* Enhanced Glassmorphism (Interactive) */
.glassmorphic-card-enhanced {
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

/* Modal Glassmorphism */
.glassmorphic-modal {
  background: rgba(20, 20, 20, 0.85);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 20px;
  box-shadow: 0 16px 64px rgba(0, 0, 0, 0.5);
}
```

### 5.2 Hover States and Interactions

```css
/* Interactive Cards */
.glassmorphic-card-interactive {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
}

.glassmorphic-card-interactive:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-2px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
}

.glassmorphic-card-interactive:active {
  transform: translateY(-1px);
}
```

## 6. Component Specifications

### 6.1 Navigation Header

```css
.navigation-header {
  width: 100%;
  height: 78px;
  background: rgba(30, 30, 30, 0.65);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  position: sticky;
  top: 0;
  z-index: 1000;
}
```

### 6.2 Page-Specific Components

```css
/* Home Page Hero Section */
.hero-section {
  width: 100%;
  min-height: 100vh;
  background: var(--gradient-home);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

/* Leadership Dashboard Grid */
.leadership-grid {
  width: 100%;
  height: 1440px;
  background: var(--gradient-leadership);
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
  padding: 2rem;
}
```

## 7. Responsive Breakpoints

### 7.1 Breakpoint System

```css
/* Responsive Design System */
--breakpoint-mobile: 768px;
--breakpoint-tablet: 1024px;
--breakpoint-desktop: 1440px;
--breakpoint-large: 1920px;

/* Container Queries */
@container (max-width: 768px) {
  .body-container {
    width: 100%;
    min-width: 320px;
    padding: 1rem;
  }
}

@container (min-width: 1441px) {
  .body-container {
    max-width: 1440px;
    margin: 0 auto;
  }
}
```

## 8. Animation and Transitions

### 8.1 Standard Transitions

```css
/* Base Transition System */
--transition-fast: 0.15s cubic-bezier(0.4, 0, 0.2, 1);
--transition-normal: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
--transition-slow: 0.5s cubic-bezier(0.4, 0, 0.2, 1);

/* Page Transitions */
.page-enter {
  opacity: 0;
  transform: translateY(20px);
}

.page-enter-active {
  opacity: 1;
  transform: translateY(0);
  transition: opacity var(--transition-normal), transform var(--transition-normal);
}
```

## 9. Implementation Checklist

### 9.1 Critical Requirements

- [ ] Exact gradient implementations matching Figma values
- [ ] Precise border colors (#CED4DA, #E5E7EB) and 2px width
- [ ] Correct page dimensions (especially Home: 4765px height)
- [ ] Proper glassmorphism backdrop-filter support
- [ ] Font loading for Inter and Flood Std
- [ ] Dark theme color contrast ratios (WCAG AA)

### 9.2 Quality Assurance

- [ ] Cross-browser glassmorphism testing (Chrome, Firefox, Safari)
- [ ] Performance testing with backdrop-filter effects
- [ ] Mobile responsiveness validation
- [ ] Accessibility audit with screen readers
- [ ] Color contrast validation for all text elements

## 10. Browser Support

### 10.1 Minimum Requirements

```css
/* Feature Queries for Progressive Enhancement */
@supports (backdrop-filter: blur(12px)) {
  .glassmorphic-card {
    backdrop-filter: blur(12px);
  }
}

@supports not (backdrop-filter: blur(12px)) {
  .glassmorphic-card {
    background: rgba(255, 255, 255, 0.15);
  }
}
```

### 10.2 Browser Compatibility
- **Chrome/Edge:** Full support (recommended)
- **Firefox:** Partial support (requires -webkit-backdrop-filter)
- **Safari:** Full support
- **Mobile:** iOS 14+, Android Chrome 76+

---

*This specification document ensures pixel-perfect implementation of the OneVice AI Hub Figma design. All values are extracted directly from the Figma design system for maximum accuracy.*