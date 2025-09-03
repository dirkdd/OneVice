# OneVice Figma-to-Code Alignment Guide

**Version:** 1.0  
**Date:** September 2, 2025  
**Status:** Implementation Ready  
**Figma URL:** https://www.figma.com/design/ZQFiaavkorum7oSDGJnW6d/OneVice-AI-Hub  
**Dependencies:** design-specifications.md, page-specifications.md, component-library.md

## 1. Figma Design System Mapping

This document provides the exact mapping between Figma design elements and their corresponding code implementations, ensuring pixel-perfect accuracy during development.

### 1.1 Figma File Structure Analysis

```typescript
interface FigmaFileStructure {
  canvas: "Page 1";
  totalPages: 5;
  pages: {
    home: { id: "2:671", dimensions: "1440x4765" };
    login: { id: "39:100", dimensions: "1440x1596" };
    leadership: { id: "2:1495", dimensions: "1440x1440" };
    talentDiscovery: { id: "2:2162", dimensions: "1440x1596" };
    bidding: { id: "2:2602", dimensions: "1440x1596" };
  };
  globalStyles: {
    layoutModes: ["column", "none"];
    fillSystems: ["gradient", "solid", "overlay"];
    borderSystem: { primary: "#CED4DA", secondary: "#E5E7EB" };
  };
}
```

### 1.2 Design Token Extraction Map

| Figma Property | Figma Value | CSS Implementation | Usage |
|---|---|---|---|
| **Layout Modes** | | | |
| `layout_4Z7B5M` | column, hug-hug | `flex-col w-fit h-fit` | Main frame containers |
| `layout_XO2K23` | none, fixed 1440x4765 | `relative w-[1440px] h-[4765px]` | Home page body |
| `layout_06GMX4` | none, fixed 1440x1596 | `relative w-[1440px] h-[1596px]` | Login/Talent/Bidding |
| `layout_66AK7L` | none, fixed 1440x1440 | `relative w-[1440px] h-[1440px]` | Leadership page |
| **Fill Systems** | | | |
| `fill_4RSQ38` | rgba(0,0,0,0.2), #FFFFFF | `bg-gradient-to-r from-black/20 to-white` | Frame overlay |
| `fill_QCVE4N` | Home gradient | `bg-gradient-home` | Home page background |
| `fill_HTV17W` | Leadership gradient | `bg-gradient-leadership` | Leadership background |
| `fill_0R9DYN` | #FFFFFF | `bg-white` | Standard white fill |
| **Stroke Systems** | | | |
| `stroke_BALVYR` | #CED4DA, 2px | `border-2 border-[#CED4DA]` | Primary frame border |
| `stroke_TE1W12` | #E5E7EB | `border-[#E5E7EB]` | Body container border |

## 2. Page-by-Page Figma Mapping

### 2.1 Home Page (2:671) - Figma to Code

#### 2.1.1 Figma Frame Structure
```
Frame: "Home" (2:671)
├── Properties: 1440x4765px, column layout, hug sizing
├── Fills: rgba(0,0,0,0.2) + #FFFFFF overlay
├── Strokes: 2px #CED4DA border, 8px radius
└── Body: "body" (2:672)
    ├── Properties: 1440x4765px, none layout, fixed sizing  
    ├── Fills: Home gradient (rgba(10,10,11) to rgba(17,17,17))
    └── Strokes: 2px #E5E7EB border
```

#### 2.1.2 Code Implementation Mapping

```tsx
// Direct Figma-to-code mapping for Home page
export default function HomePage() {
  return (
    // Main Frame (2:671) - Column layout with hug sizing
    <div className="flex flex-col w-fit h-fit border-2 border-[#CED4DA] rounded-lg bg-gradient-to-r from-black/20 to-white">
      
      {/* Body Container (2:672) - Fixed dimensions with home gradient */}
      <div 
        className="relative w-[1440px] border-2 border-[#E5E7EB] bg-gradient-home"
        style={{ height: '4765px' }} // Exact Figma height
      >
        {/* Page content goes here */}
      </div>
    </div>
  );
}

// CSS Custom Properties mapping
:root {
  --gradient-home: linear-gradient(90deg, rgba(10, 10, 11, 1) 0%, rgba(26, 26, 27, 1) 50%, rgba(17, 17, 17, 1) 100%);
}

.bg-gradient-home {
  background: var(--gradient-home);
}
```

### 2.2 Login Page (39:100) - Figma to Code

#### 2.2.1 Figma Frame Structure
```
Frame: "Login" (39:100)
├── Properties: 1440x1596px, column layout, hug sizing
├── Fills: #FFFFFF
├── Strokes: 2px #CED4DA border, 8px radius
└── Body: "body" (39:101)
    ├── Properties: 1440x1596px, none layout, fixed sizing
    ├── Fills: Home gradient (same as home page)
    └── Strokes: 2px #E5E7EB border
```

#### 2.2.2 Code Implementation Mapping

```tsx
// Login page with exact Figma dimensions
export default function LoginPage() {
  return (
    // Main Frame (39:100) - White background with border
    <div className="flex flex-col w-fit h-fit border-2 border-[#CED4DA] rounded-lg bg-white">
      
      {/* Body Container (39:101) - Compact height with home gradient */}
      <div 
        className="relative w-[1440px] border-2 border-[#E5E7EB] bg-gradient-home flex items-center justify-center"
        style={{ height: '1596px' }} // Exact Figma height
      >
        {/* Centered login form */}
        <div className="w-full max-w-md">
          <LoginForm />
        </div>
      </div>
    </div>
  );
}
```

### 2.3 Leadership Dashboard (2:1495) - Figma to Code

#### 2.3.1 Figma Frame Structure
```
Frame: "Leadership" (2:1495)
├── Properties: 1440x1440px, column layout, hug sizing (SQUARE)
├── Fills: #FFFFFF  
├── Strokes: 2px #CED4DA border, 8px radius
└── Body: "body" (2:1496)
    ├── Properties: 1440x1440px, none layout, fixed sizing
    ├── Fills: Leadership gradient (rgba(0,0,0) to rgba(17,17,17))
    └── Strokes: 2px #E5E7EB border
```

#### 2.3.2 Code Implementation Mapping

```tsx
// Leadership page with unique square layout and gradient
export default function LeadershipPage() {
  return (
    // Main Frame (2:1495) - Square aspect ratio
    <div className="flex flex-col w-fit h-fit border-2 border-[#CED4DA] rounded-lg bg-white">
      
      {/* Body Container (2:1496) - Square dimensions with leadership gradient */}
      <div 
        className="relative w-[1440px] h-[1440px] border-2 border-[#E5E7EB] bg-gradient-leadership"
      >
        {/* Dashboard grid content */}
      </div>
    </div>
  );
}

// Leadership-specific gradient
:root {
  --gradient-leadership: linear-gradient(90deg, rgba(0, 0, 0, 1) 0%, rgba(17, 17, 17, 1) 50%, rgba(0, 0, 0, 1) 100%);
}
```

### 2.4 Talent Discovery (2:2162) - Figma to Code

#### 2.4.1 Figma Frame Structure
```
Frame: "Talent Discovery" (2:2162)
├── Properties: 1440x1596px, column layout, hug sizing
├── Fills: #FFFFFF
├── Strokes: 2px #CED4DA border, 8px radius  
└── Body: "body" (2:2163)
    ├── Properties: 1440x1596px, none layout, fixed sizing
    ├── Fills: Home gradient (same as home/login)
    └── Strokes: 2px #E5E7EB border
```

#### 2.4.2 Code Implementation Mapping

```tsx
// Talent page with search-focused layout
export default function TalentPage() {
  return (
    // Main Frame (2:2162) - Standard frame setup
    <div className="flex flex-col w-fit h-fit border-2 border-[#CED4DA] rounded-lg bg-white">
      
      {/* Body Container (2:2163) - Medium height for search interface */}
      <div 
        className="relative w-[1440px] border-2 border-[#E5E7EB] bg-gradient-home"
        style={{ height: '1596px' }} // Exact Figma height
      >
        {/* Search and talent grid */}
      </div>
    </div>
  );
}
```

### 2.5 Bidding Platform (2:2602) - Figma to Code

#### 2.5.1 Figma Frame Structure
```
Frame: "Bidding" (2:2602)
├── Properties: 1440x1596px, column layout, hug sizing
├── Fills: #FFFFFF
├── Strokes: 2px #CED4DA border, 8px radius
└── Body: "body" (2:2603)  
    ├── Properties: 1440x1596px, none layout, fixed sizing
    ├── Fills: Home gradient (same as home/login/talent)
    └── Strokes: 2px #E5E7EB border
```

#### 2.5.2 Code Implementation Mapping

```tsx
// Bidding page with real-time interface layout
export default function BiddingPage() {
  return (
    // Main Frame (2:2602) - Standard frame setup
    <div className="flex flex-col w-fit h-fit border-2 border-[#CED4DA] rounded-lg bg-white">
      
      {/* Body Container (2:2603) - Medium height for bidding interface */}
      <div 
        className="relative w-[1440px] border-2 border-[#E5E7EB] bg-gradient-home"
        style={{ height: '1596px' }} // Exact Figma height  
      >
        {/* Bidding controls and timeline */}
      </div>
    </div>
  );
}
```

## 3. Global Styles Mapping

### 3.1 Figma Global Variables to CSS

```css
/* globals.css - Direct Figma variable mapping */

/* Layout System from Figma */
.layout-column-hug {
  display: flex;
  flex-direction: column;
  width: fit-content;
  height: fit-content;
}

.layout-none-fixed {
  position: relative;
}

/* Fill System from Figma */
.fill-home-gradient {
  background: linear-gradient(90deg, rgba(10, 10, 11, 1) 0%, rgba(26, 26, 27, 1) 50%, rgba(17, 17, 17, 1) 100%);
}

.fill-leadership-gradient {  
  background: linear-gradient(90deg, rgba(0, 0, 0, 1) 0%, rgba(17, 17, 17, 1) 50%, rgba(0, 0, 0, 1) 100%);
}

.fill-frame-overlay {
  background: linear-gradient(rgba(0, 0, 0, 0.2), #FFFFFF);
}

/* Stroke System from Figma */
.stroke-primary {
  border: 2px solid #CED4DA;
}

.stroke-secondary {
  border: 2px solid #E5E7EB;  
}

/* Frame Border Radius */
.frame-radius {
  border-radius: 8px;
}
```

### 3.2 Tailwind Configuration Alignment

```javascript
// tailwind.config.js - Figma-aligned configuration
module.exports = {
  theme: {
    extend: {
      // Exact Figma dimensions
      width: {
        'figma-page': '1440px',
      },
      height: {
        'figma-home': '4765px',
        'figma-login': '1596px', 
        'figma-leadership': '1440px',
        'figma-talent': '1596px',
        'figma-bidding': '1596px',
      },
      
      // Figma color system
      colors: {
        'figma-border-primary': '#CED4DA',
        'figma-border-secondary': '#E5E7EB',
      },
      
      // Figma gradients
      backgroundImage: {
        'figma-home': 'linear-gradient(90deg, rgba(10, 10, 11, 1) 0%, rgba(26, 26, 27, 1) 50%, rgba(17, 17, 17, 1) 100%)',
        'figma-leadership': 'linear-gradient(90deg, rgba(0, 0, 0, 1) 0%, rgba(17, 17, 17, 1) 50%, rgba(0, 0, 0, 1) 100%)',
        'figma-overlay': 'linear-gradient(rgba(0, 0, 0, 0.2), #FFFFFF)',
      },
      
      // Figma border radius
      borderRadius: {
        'figma-frame': '8px',
        'figma-card': '12px',
      },
      
      // Figma border widths
      borderWidth: {
        'figma': '2px',
      },
    },
  },
};
```

## 4. Component Alignment Map

### 4.1 Glassmorphic Card Figma Mapping

```typescript
// Component props mapping to Figma properties
interface FigmaCardMapping {
  figmaId: string;
  figmaProperties: {
    background: string;
    border: string;  
    borderRadius: string;
    backdropFilter?: string;
  };
  codeImplementation: GlassmorphicCardProps;
}

const figmaCardMappings: FigmaCardMapping[] = [
  {
    figmaId: "glassmorphic-default",
    figmaProperties: {
      background: "rgba(255, 255, 255, 0.05)",
      border: "1px solid rgba(255, 255, 255, 0.1)", 
      borderRadius: "12px",
      backdropFilter: "blur(12px)",
    },
    codeImplementation: {
      variant: "default",
      size: "md",
    },
  },
  {
    figmaId: "glassmorphic-elevated",
    figmaProperties: {
      background: "rgba(255, 255, 255, 0.08)",
      border: "1px solid rgba(255, 255, 255, 0.15)",
      borderRadius: "16px", 
      backdropFilter: "blur(16px)",
    },
    codeImplementation: {
      variant: "elevated",
      size: "lg",
    },
  },
];
```

### 4.2 Typography Figma Mapping

```css
/* Typography system matching Figma text styles */
.figma-text-h1 {
  font-family: 'Inter', sans-serif;
  font-size: clamp(3rem, 5vw, 5rem);
  font-weight: 800;
  line-height: 1.1;
  color: rgba(255, 255, 255, 0.95);
}

.figma-text-h2 {
  font-family: 'Inter', sans-serif;
  font-size: clamp(2rem, 3vw, 3rem);
  font-weight: 700;
  line-height: 1.2;
  color: rgba(255, 255, 255, 0.95);
}

.figma-text-body {
  font-family: 'Inter', sans-serif;
  font-size: 1rem;
  font-weight: 400;
  line-height: 1.5;
  color: rgba(255, 255, 255, 0.75);
}

.figma-text-small {
  font-family: 'Inter', sans-serif;
  font-size: 0.875rem;
  font-weight: 400;
  line-height: 1.4;
  color: rgba(255, 255, 255, 0.55);
}
```

## 5. Responsive Design Mapping

### 5.1 Figma Breakpoint Strategy

```typescript
// Responsive strategy for Figma's fixed-width designs
interface ResponsiveStrategy {
  figmaDesktop: "1440px fixed width";
  codeImplementation: {
    mobile: "320px - 767px (stack vertically, reduce padding)";
    tablet: "768px - 1023px (2-column grid, medium padding)";  
    desktop: "1024px+ (match Figma exactly)";
    large: "1441px+ (center container, max-width 1440px)";
  };
}

const responsiveMappings = {
  // Home page responsive mapping
  home: {
    figmaHeight: '4765px',
    responsiveHeights: {
      mobile: 'auto (content-driven)',
      tablet: 'auto (content-driven)', 
      desktop: '4765px (match Figma)',
    },
  },
  
  // Leadership page responsive mapping
  leadership: {
    figmaHeight: '1440px', // Square layout
    responsiveHeights: {
      mobile: 'auto (vertical stack)',
      tablet: 'auto (2-column grid)',
      desktop: '1440px (square maintained)',
    },
  },
};
```

### 5.2 Responsive CSS Implementation

```css
/* Mobile-first responsive implementation */
@media (max-width: 767px) {
  /* Stack Figma layouts vertically */
  .figma-page {
    width: 100%;
    min-width: 320px;
    height: auto;
    padding: 1rem;
  }
  
  /* Maintain Figma gradients */
  .bg-figma-home,
  .bg-figma-leadership {
    background-size: cover;
    background-position: center;
  }
}

@media (min-width: 768px) and (max-width: 1023px) {
  /* Tablet adaptations */
  .figma-page {
    width: 100%;
    max-width: 1024px;
    margin: 0 auto;
  }
}

@media (min-width: 1024px) {
  /* Match Figma exactly */
  .figma-page {
    width: 1440px;
  }
  
  /* Maintain exact Figma heights */
  .figma-home-body {
    height: 4765px;
  }
  
  .figma-leadership-body {
    height: 1440px;
  }
  
  .figma-standard-body {
    height: 1596px;
  }
}

@media (min-width: 1441px) {
  /* Center for large screens */
  .figma-container {
    max-width: 1440px;
    margin: 0 auto;
  }
}
```

## 6. Quality Assurance Checklist

### 6.1 Figma-to-Code Verification

```typescript
interface QualityChecklist {
  dimensions: {
    homePage: "✓ 1440px × 4765px exactly";
    loginPage: "✓ 1440px × 1596px exactly"; 
    leadershipPage: "✓ 1440px × 1440px exactly (square)";
    talentPage: "✓ 1440px × 1596px exactly";
    biddingPage: "✓ 1440px × 1596px exactly";
  };
  
  gradients: {
    homeGradient: "✓ rgba(10,10,11) → rgba(26,26,27) → rgba(17,17,17)";
    leadershipGradient: "✓ rgba(0,0,0) → rgba(17,17,17) → rgba(0,0,0)";
    overlayGradient: "✓ rgba(0,0,0,0.2) to #FFFFFF";
  };
  
  borders: {
    frameBorder: "✓ 2px solid #CED4DA";
    bodyBorder: "✓ 2px solid #E5E7EB";
    borderRadius: "✓ 8px for frames";
  };
  
  layout: {
    columnLayout: "✓ flex-col w-fit h-fit";
    fixedLayout: "✓ relative positioning";
    hugContent: "✓ width/height fit-content";
  };
}
```

### 6.2 Visual Regression Testing

```bash
# Visual regression test commands
npm install -D @percy/cli @percy/playwright

# Run visual tests against Figma designs  
npx percy exec -- npx playwright test --config=percy.config.ts

# Figma design comparison
npx percy snapshot ./dist --name "Home Page" --widths=1440
npx percy snapshot ./dist/login --name "Login Page" --widths=1440
npx percy snapshot ./dist/leadership --name "Leadership Dashboard" --widths=1440
```

### 6.3 Cross-Browser Figma Alignment

```typescript
// Browser compatibility for Figma effects
const browserSupport = {
  gradients: "All modern browsers ✓",
  borderRadius: "All modern browsers ✓", 
  flexbox: "All modern browsers ✓",
  backdropFilter: {
    chrome: "✓ Full support",
    firefox: "✓ With -webkit-backdrop-filter",
    safari: "✓ Full support", 
    edge: "✓ Chromium-based full support",
  },
};
```

## 7. Development Workflow

### 7.1 Figma-to-Code Process

```bash
# Step 1: Extract Figma tokens
figma-tokens extract --file-key=ZQFiaavkorum7oSDGJnW6d --output=./tokens

# Step 2: Generate CSS custom properties
node scripts/generate-figma-css.js

# Step 3: Validate against Figma
npm run test:visual-regression  

# Step 4: Build and deploy
npm run build
npm run deploy
```

### 7.2 Figma Updates Workflow

```bash
# When Figma designs are updated:
# 1. Re-export design tokens
# 2. Update CSS custom properties 
# 3. Run visual regression tests
# 4. Update this alignment document
# 5. Deploy changes

git add .
git commit -m "feat: update Figma alignment for design system v2"
git push origin feature/figma-update
```

---

*This Figma-to-code alignment guide ensures pixel-perfect implementation of the OneVice AI Hub design. All measurements, colors, and layouts are mapped directly from Figma to maintain visual fidelity.*