# OneVice Page Specifications - Figma Implementation

**Version:** 1.0  
**Date:** September 2, 2025  
**Status:** Implementation Ready  
**Source:** Figma Design - OneVice AI Hub  
**Dependencies:** design-specifications.md, component-library.md

## 1. Overview

This document provides detailed specifications for each of the 5 pages in the OneVice AI Hub, extracted directly from Figma designs. Each page specification includes exact dimensions, layout patterns, component placements, and interaction behaviors.

## 2. Home Page Specifications

### 2.1 Layout Structure
- **Figma ID:** `2:671`
- **Dimensions:** 1440px × 4765px (extended scrolling page)
- **Layout Mode:** Column with hug sizing
- **Background:** Primary gradient system
- **Border:** 8px radius with #CED4DA 2px border

### 2.2 Content Architecture

```typescript
interface HomePageStructure {
  header: NavigationHeader;
  hero: HeroSection;
  features: FeatureShowcaseSection;
  testimonials: TestimonialSection;
  cta: CallToActionSection;
  footer: Footer;
}
```

### 2.3 Hero Section (Top 100vh)

```css
.hero-section {
  width: 1440px;
  height: 100vh;
  min-height: 800px;
  background: linear-gradient(90deg, rgba(10, 10, 11, 1) 0%, rgba(26, 26, 27, 1) 50%, rgba(17, 17, 17, 1) 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  position: relative;
}

.hero-content {
  max-width: 800px;
  text-align: center;
  z-index: 2;
}

.hero-title {
  font-family: var(--font-primary);
  font-size: clamp(3rem, 5vw, 5rem);
  font-weight: 800;
  color: var(--text-primary);
  line-height: 1.1;
  margin-bottom: 2rem;
}

.hero-subtitle {
  font-size: 1.5rem;
  color: var(--text-secondary);
  margin-bottom: 3rem;
  line-height: 1.4;
}
```

### 2.4 Feature Showcase Section (Middle sections)

```css
.feature-showcase {
  padding: 8rem 2rem;
  background: rgba(255, 255, 255, 0.02);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 3rem;
  max-width: 1200px;
  margin: 0 auto;
}

.feature-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 2.5rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.feature-card:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-4px);
}
```

### 2.5 Call to Action Section (Bottom)

```css
.cta-section {
  padding: 8rem 2rem;
  text-align: center;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(0, 0, 0, 0.1) 100%);
}

.cta-button {
  display: inline-flex;
  align-items: center;
  padding: 1.5rem 3rem;
  background: linear-gradient(135deg, #60A5FA 0%, #3B82F6 100%);
  color: white;
  font-weight: 600;
  border-radius: 12px;
  transition: all 0.3s ease;
  border: none;
  cursor: pointer;
}

.cta-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 40px rgba(96, 165, 250, 0.3);
}
```

## 3. Login Page Specifications

### 3.1 Layout Structure
- **Figma ID:** `39:100`
- **Dimensions:** 1440px × 1596px (compact page)
- **Layout Mode:** Column with hug sizing
- **Background:** Standard white with gradient body
- **Border:** 8px radius with #CED4DA 2px border

### 3.2 Authentication Layout

```css
.login-page {
  width: 1440px;
  height: 1596px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(90deg, rgba(10, 10, 11, 1) 0%, rgba(26, 26, 27, 1) 50%, rgba(17, 17, 17, 1) 100%);
  padding: 2rem;
}

.login-container {
  width: 100%;
  max-width: 480px;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 20px;
  padding: 3rem;
  box-shadow: 0 16px 64px rgba(0, 0, 0, 0.3);
}
```

### 3.3 Form Elements

```typescript
interface LoginFormStructure {
  logo: OneViceLogo;
  title: "Welcome to OneVice";
  subtitle: "AI-Powered Business Intelligence";
  emailField: GlassmorphicInput;
  passwordField: GlassmorphicInput;
  rememberMe: GlassmorphicCheckbox;
  loginButton: PrimaryButton;
  divider: OrDivider;
  ssoButtons: SSOButtonGroup;
  signupLink: TextLink;
}
```

```css
.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-input {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 1rem 1.5rem;
  color: var(--text-primary);
  font-size: 1rem;
  transition: all 0.3s ease;
}

.form-input:focus {
  outline: none;
  border-color: #60A5FA;
  background: rgba(255, 255, 255, 0.08);
  box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.1);
}
```

## 4. Leadership Dashboard Specifications

### 4.1 Layout Structure
- **Figma ID:** `2:1495`
- **Dimensions:** 1440px × 1440px (square layout)
- **Layout Mode:** Column with hug sizing
- **Background:** Leadership gradient (pure black to dark gray)
- **Special Note:** Uses unique gradient system

### 4.2 Dashboard Architecture

```typescript
interface LeadershipDashboardStructure {
  header: ExecutiveHeader;
  kpiGrid: KPICardGrid;
  chartSection: AnalyticsChartSection;
  teamOverview: TeamPerformanceSection;
  actionItems: ActionItemsList;
  sidebar: QuickActionsSidebar;
}
```

### 4.3 Executive Header

```css
.executive-header {
  width: 100%;
  height: 120px;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 3rem;
}

.executive-welcome {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text-primary);
}

.executive-metrics {
  display: flex;
  gap: 3rem;
}
```

### 4.4 KPI Grid Layout

```css
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 2rem;
  padding: 2rem 3rem;
  margin-bottom: 2rem;
}

.kpi-card {
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 2rem;
  text-align: center;
  transition: all 0.3s ease;
}

.kpi-value {
  font-size: 2.5rem;
  font-weight: 800;
  color: #60A5FA;
  margin-bottom: 0.5rem;
}

.kpi-label {
  font-size: 0.875rem;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 1px;
}
```

### 4.5 Leadership-Specific Background

```css
.leadership-page {
  background: linear-gradient(90deg, rgba(0, 0, 0, 1) 0%, rgba(17, 17, 17, 1) 50%, rgba(0, 0, 0, 1) 100%);
  min-height: 1440px;
}
```

## 5. Talent Discovery Page Specifications

### 5.1 Layout Structure
- **Figma ID:** `2:2162`
- **Dimensions:** 1440px × 1596px
- **Layout Mode:** Column with hug sizing
- **Background:** Standard gradient system
- **Focus:** Search and discovery interface

### 5.2 Search Interface

```typescript
interface TalentDiscoveryStructure {
  searchHeader: TalentSearchHeader;
  filterPanel: TalentFilterPanel;
  resultsGrid: TalentProfileGrid;
  pagination: PaginationControls;
  actionPanel: TalentActionPanel;
}
```

### 5.3 Search Header Component

```css
.talent-search-header {
  width: 100%;
  padding: 3rem 2rem;
  background: rgba(255, 255, 255, 0.02);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.search-container {
  max-width: 800px;
  margin: 0 auto;
  position: relative;
}

.talent-search-input {
  width: 100%;
  padding: 1.5rem 3rem 1.5rem 1.5rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 50px;
  color: var(--text-primary);
  font-size: 1.1rem;
}

.search-icon {
  position: absolute;
  right: 1.5rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-tertiary);
}
```

### 5.4 Talent Profile Cards

```css
.talent-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 2rem;
  padding: 2rem;
}

.talent-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 2rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
}

.talent-card:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3);
}
```

## 6. Bidding Platform Specifications

### 6.1 Layout Structure
- **Figma ID:** `2:2602`
- **Dimensions:** 1440px × 1596px
- **Layout Mode:** Column with hug sizing
- **Background:** Standard gradient system
- **Focus:** Real-time bidding interface

### 6.2 Bidding Interface

```typescript
interface BiddingPlatformStructure {
  biddingHeader: LiveBiddingHeader;
  projectDetails: ProjectDetailsPanel;
  biddingControls: BiddingControlsPanel;
  competitorPanel: CompetitorBidsPanel;
  timelineView: BiddingTimelineView;
  submitPanel: BidSubmissionPanel;
}
```

### 6.3 Live Bidding Header

```css
.bidding-header {
  width: 100%;
  padding: 2rem;
  background: rgba(255, 255, 255, 0.03);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.live-indicator {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.live-dot {
  width: 8px;
  height: 8px;
  background: #22C55E;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.time-remaining {
  font-size: 1.5rem;
  font-weight: 700;
  color: #F59E0B;
}
```

### 6.4 Bidding Controls

```css
.bidding-controls {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 2rem;
  padding: 2rem;
}

.bid-input-section {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 2rem;
}

.bid-amount-input {
  width: 100%;
  padding: 1.5rem;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 1.5rem;
  font-weight: 600;
  text-align: center;
}

.submit-bid-button {
  width: 100%;
  padding: 1.5rem;
  background: linear-gradient(135deg, #22C55E 0%, #16A34A 100%);
  color: white;
  font-size: 1.25rem;
  font-weight: 700;
  border-radius: 12px;
  border: none;
  cursor: pointer;
  transition: all 0.3s ease;
}

.submit-bid-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 40px rgba(34, 197, 94, 0.3);
}
```

## 7. Common Layout Patterns

### 7.1 Page Container Pattern

```css
.page-container {
  width: 1440px;
  max-width: 100vw;
  min-height: var(--page-height);
  background: var(--page-background);
  border: 2px solid var(--border-primary);
  border-radius: 8px;
  overflow-x: hidden;
  position: relative;
}

.page-body {
  width: 100%;
  height: 100%;
  background: var(--body-background);
  border: 2px solid var(--border-secondary);
  position: relative;
}
```

### 7.2 Section Spacing System

```css
/* Consistent section spacing across all pages */
.page-section {
  padding: 4rem 2rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.section-header {
  max-width: 1200px;
  margin: 0 auto 3rem;
  text-align: center;
}

.section-content {
  max-width: 1200px;
  margin: 0 auto;
}
```

## 8. Responsive Adaptations

### 8.1 Mobile Breakpoints

```css
@media (max-width: 768px) {
  .page-container {
    width: 100%;
    min-width: 320px;
    border-radius: 0;
    border-left: none;
    border-right: none;
  }
  
  .hero-section,
  .login-page,
  .leadership-page,
  .talent-discovery-page,
  .bidding-page {
    width: 100%;
    padding: 2rem 1rem;
  }
  
  .feature-grid,
  .kpi-grid,
  .talent-grid {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
}
```

### 8.2 Tablet Breakpoints

```css
@media (min-width: 769px) and (max-width: 1024px) {
  .page-container {
    width: 100%;
    max-width: 1024px;
  }
  
  .kpi-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .talent-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
```

## 9. Implementation Priority

### 9.1 Phase 1: Core Layout (Week 1)
1. Home page hero section
2. Navigation header component
3. Basic glassmorphic card system
4. Login page authentication layout

### 9.2 Phase 2: Dashboard Components (Week 2)
1. Leadership KPI grid
2. Talent search interface
3. Bidding controls panel
4. Common section patterns

### 9.3 Phase 3: Interactive Features (Week 3)
1. Form validation and states
2. Real-time bidding indicators
3. Search and filter functionality
4. Responsive adaptations

### 9.4 Phase 4: Polish and Animation (Week 4)
1. Hover states and micro-interactions
2. Page transitions
3. Loading states
4. Accessibility enhancements

---

*Each page specification ensures pixel-perfect implementation matching the Figma design. All dimensions, colors, and interactions are precisely documented for development teams.*