# OneVice Database Schema Specifications

**Version:** 1.0  
**Date:** September 1, 2025  
**Status:** Implementation Ready  
**Database Systems:** Neo4j 5.25.x + Redis 7.4.x

## 1. Overview

This document defines the comprehensive database schema for the OneVice platform, including the Neo4j graph database structure for entertainment industry knowledge, Redis caching schemas, and data migration strategies. The schema supports role-based access control, vector search integration, and entertainment industry-specific entity relationships.

## 2. Neo4j Graph Database Schema

### 2.1 Node Types and Properties

#### 2.1.1 Person Node

```cypher
// Core Person node with entertainment industry focus
CREATE CONSTRAINT person_id FOR (p:Person) REQUIRE p.id IS UNIQUE;
CREATE INDEX person_name FOR (p:Person) ON (p.name);
CREATE INDEX person_role FOR (p:Person) ON (p.roleType);
CREATE INDEX person_union FOR (p:Person) ON (p.unionStatus);

(:Person {
  id: String,                    // UUID: "person_123456"
  name: String,                  // "Daniel Russell"
  roleType: String,              // "Director" | "Creative Director" | "Talent" | "Client" | "Producer"
  unionStatus: String,           // "Union" | "Non-Union" | "Unknown"
  specializations: [String],     // ["Music Video", "Commercial", "Brand Film"]
  yearsActive: Integer,          // 15
  budgetRange: String,           // "$50k-250k"
  rateType: String,              // "Daily" | "Weekly" | "Project"
  dayRate: Float,                // 15000.00 (nullable)
  weeklyRate: Float,             // 75000.00 (nullable)
  projectMinimum: Float,         // 100000.00 (nullable)
  
  // Contact Information
  email: String,                 // "daniel@example.com" (nullable)
  phone: String,                 // "+1-555-0123" (nullable)
  website: String,               // "https://danielrussell.com" (nullable)
  representation: String,        // "CAA" (nullable)
  
  // Profile Information
  bio: String,                   // Long text biography
  location: String,              // "Los Angeles, CA"
  timezone: String,              // "America/Los_Angeles"
  languages: [String],           // ["English", "Spanish"]
  
  // Professional Information
  awards: [String],              // ["Cannes Lion Gold", "Grammy Nominated"]
  notableClients: [String],      // ["Nike", "Apple", "Warner Music"]
  portfolioUrl: String,          // "https://portfolio.danielrussell.com"
  
  // Availability and Preferences
  preferredGenres: [String],     // ["Hip-hop", "Pop", "Rock"]
  willingToTravel: Boolean,      // true
  maxProjectDuration: Integer,   // 30 (days)
  minNoticeDays: Integer,        // 14
  
  // System Fields
  createdAt: DateTime,           // 2025-01-01T00:00:00Z
  updatedAt: DateTime,           // 2025-09-01T12:00:00Z
  isActive: Boolean,             // true
  verificationStatus: String,    // "verified" | "pending" | "unverified"
  
  // Vector Embeddings for Semantic Search
  profileEmbedding: [Float],     // 1536-dimensional vector
  skillsEmbedding: [Float],      // 1536-dimensional vector
  
  // RBAC and Security
  visibilityLevel: Integer,      // 1-6 (aligns with data sensitivity)
  accessRestrictions: [String], // ["budget_info", "contact_info"]
  
  // Analytics
  queryFrequency: Integer,       // How often this person is searched
  lastQueried: DateTime,         // 2025-08-15T10:30:00Z
  popularityScore: Float         // 0.0 - 1.0
})
```

#### 2.1.2 Project Node

```cypher
// Project node with comprehensive entertainment industry data
CREATE CONSTRAINT project_id FOR (p:Project) REQUIRE p.id IS UNIQUE;
CREATE INDEX project_type FOR (p:Project) ON (p.type);
CREATE INDEX project_status FOR (p:Project) ON (p.status);
CREATE INDEX project_union FOR (p:Project) ON (p.unionStatus);
CREATE INDEX project_budget_tier FOR (p:Project) ON (p.budgetTier);

(:Project {
  id: String,                    // UUID: "proj_789012"
  name: String,                  // "Summer Campaign 2024"
  type: String,                  // "Music Video" | "Commercial" | "Brand Film"
  subtype: String,               // "National TV", "Social Media", "Cinema"
  status: String,                // "Planning" | "Pre-Production" | "In Production" | "Post Production" | "Completed" | "Cancelled"
  
  // Budget Information (RBAC Sensitive - Level 1)
  totalBudget: Float,            // 275000.00
  budgetTier: String,            // "$0-50k" | "$50k-100k" | "$100k-300k" | "$300k+"
  budgetBreakdown: {
    aboveLine: Float,            // 125000.00
    belowLine: Float,            // 100000.00
    postProduction: Float,       // 35000.00
    contingency: Float           // 15000.00
  },
  currency: String,              // "USD" | "CAD" | "GBP" | "EUR"
  
  // Production Details
  unionStatus: String,           // "Union" | "Non-Union" | "Mixed"
  duration: Integer,             // 3 (shoot days)
  crewSize: String,              // "Small" | "Medium" | "Large"
  equipmentLevel: String,        // "Basic" | "Standard" | "Premium"
  
  // Timeline
  pitchDate: Date,               // 2024-06-01
  awardDate: Date,               // 2024-06-15
  prepStartDate: Date,           // 2024-07-01
  shootStartDate: Date,          // 2024-07-15
  shootEndDate: Date,            // 2024-07-17
  deliveryDate: Date,            // 2024-08-15
  completionDate: Date,          // 2024-08-15
  
  // Location Information
  primaryLocation: String,       // "Los Angeles, CA"
  shootLocations: [String],      // ["Studio A", "Downtown LA", "Malibu Beach"]
  permitsRequired: [String],     // ["City of LA", "California State Parks"]
  
  // Creative Information
  genre: String,                 // "Hip-hop" | "Pop" | "Rock" | "Electronic"
  mood: [String],                // ["Energetic", "Dark", "Cinematic"]
  visualStyle: [String],         // ["High Fashion", "Street", "Minimalist"]
  concepts: [String],            // ["Performance", "Narrative", "Abstract"]
  
  // Technical Specifications
  deliverables: [String],        // ["4K Master", "HD Proxy", "Social Cuts"]
  aspectRatios: [String],        // ["16:9", "9:16", "1:1"]
  duration: Integer,             // 180 (seconds for music videos)
  
  // Performance Metrics
  views: Integer,                // 1500000 (if applicable)
  engagement: Float,             // 0.08 (engagement rate)
  awards: [String],              // ["Cannes Lions Bronze", "MTV VMA Nominee"]
  
  // System Fields
  createdAt: DateTime,
  updatedAt: DateTime,
  isActive: Boolean,
  
  // Vector Embeddings
  conceptEmbedding: [Float],     // For creative concept similarity
  technicalEmbedding: [Float],   // For technical requirements matching
  
  // RBAC Fields
  sensitivityLevel: Integer,     // 1-6
  accessGroups: [String],        // ["leadership", "assigned_team"]
  
  // Analytics
  searchFrequency: Integer,
  lastAccessed: DateTime,
  referenceValue: Float          // How often this project is used as reference
})
```

#### 2.1.3 Organization Node

```cypher
// Organization node for companies, agencies, and unions
CREATE CONSTRAINT org_id FOR (o:Organization) REQUIRE o.id IS UNIQUE;
CREATE INDEX org_name FOR (o:Organization) ON (o.name);
CREATE INDEX org_type FOR (o:Organization) ON (o.type);

(:Organization {
  id: String,                    // UUID: "org_456789"
  name: String,                  // "Atlantic Records"
  type: String,                  // "Record Label" | "Production Company" | "Agency" | "Client Brand" | "Union"
  subtype: String,               // "Major Label" | "Independent" | "Boutique Agency"
  
  // Basic Information
  industry: String,              // "Music" | "Advertising" | "Entertainment"
  tier: String,                  // "Enterprise" | "Mid-Market" | "Startup"
  size: String,                  // "1-50" | "51-200" | "201-1000" | "1000+"
  founded: Integer,              // 1955
  
  // Contact Information
  headquarters: String,          // "New York, NY"
  offices: [String],             // ["Los Angeles", "Nashville", "London"]
  website: String,               // "https://atlanticrecords.com"
  phone: String,                 // "+1-212-707-2000"
  
  // Business Information
  revenue: String,               // "$1B+" (ranges for privacy)
  marketCap: String,             // "$5B+" (for public companies)
  parentCompany: String,         // "Warner Music Group"
  subsidiaries: [String],        // ["Elektra Records", "Roadrunner Records"]
  
  // Entertainment Specific
  majorArtists: [String],        // ["Bruno Mars", "Ed Sheeran", "Cardi B"]
  genres: [String],              // ["Pop", "Hip-hop", "Rock", "R&B"]
  territories: [String],         // ["North America", "Europe", "Asia"]
  
  // Union Specific (for Union type organizations)
  unionCode: String,             // "IATSE" | "DGA" | "SAG-AFTRA" | "LOCAL_399"
  jurisdiction: [String],        // ["California", "New York", "Georgia"]
  memberCount: Integer,          // 150000
  
  // Financial Metrics (RBAC Level 1)
  averageBudget: Float,          // 500000.00
  budgetRange: {
    min: Float,                  // 100000.00
    max: Float                   // 2000000.00
  },
  paymentTerms: String,          // "Net 30" | "50% upfront" | "Milestone based"
  
  // Relationship Metrics
  projectCount: Integer,         // 156
  activeProjectCount: Integer,   // 23
  completionRate: Float,         // 0.94
  averageProjectDuration: Integer, // 45 (days)
  
  // System Fields
  createdAt: DateTime,
  updatedAt: DateTime,
  isActive: Boolean,
  
  // Vector Embeddings
  profileEmbedding: [Float],
  industryEmbedding: [Float],
  
  // RBAC
  accessLevel: Integer,          // 1-6
  
  // Analytics
  searchFrequency: Integer,
  partnershipValue: Float        // Internal scoring metric
})
```

#### 2.1.4 Document Node

```cypher
// Document node for archived materials and references
CREATE CONSTRAINT doc_id FOR (d:Document) REQUIRE d.id IS UNIQUE;
CREATE INDEX doc_type FOR (d:Document) ON (d.type);
CREATE INDEX doc_sensitivity FOR (d:Document) ON (d.sensitivityLevel);

(:Document {
  id: String,                    // UUID: "doc_345678"
  title: String,                 // "Drake - God's Plan Treatment"
  filename: String,              // "drakes_gods_plan_treatment_v3.pdf"
  type: String,                  // "Treatment" | "Pitch Deck" | "Budget" | "Contract" | "Call Sheet" | "Script"
  subtype: String,               // "Director Treatment" | "Agency Pitch" | "Final Budget"
  
  // File Information
  fileSize: Integer,             // 2457600 (bytes)
  mimeType: String,              // "application/pdf"
  pageCount: Integer,            // 24
  wordCount: Integer,            // 3500
  
  // Content
  fullTextContent: String,       // Extracted text content
  summary: String,               // AI-generated summary
  keyEntities: [String],         // ["Drake", "Director X", "OVO Sound"]
  keywords: [String],            // ["narrative", "performance", "toronto"]
  
  // Metadata
  author: String,                // "Director X"
  version: String,               // "v3.2"
  language: String,              // "en"
  createdDate: DateTime,         // Document creation date
  lastModified: DateTime,        // Last file modification
  
  // RBAC and Security (Critical)
  sensitivityLevel: Integer,     // 1-6 (1=most sensitive)
  accessGroups: [String],        // ["leadership", "project_team_abc123"]
  encryptionLevel: String,       // "none" | "basic" | "advanced"
  retentionPeriod: Integer,      // 2555 (days)
  
  // Project Association
  projectPhase: String,          // "Pitch" | "Pre-Production" | "Production" | "Post" | "Delivery"
  isConfidential: Boolean,       // true
  requiresNDA: Boolean,          // true
  
  // Processing Status
  processingStatus: String,      // "processed" | "processing" | "error" | "pending"
  extractionQuality: Float,      // 0.94 (OCR/extraction confidence)
  embeddingStatus: String,       // "complete" | "pending" | "failed"
  
  // System Fields
  uploadedBy: String,            // "user_123456"
  uploadedAt: DateTime,
  processedAt: DateTime,
  lastAccessed: DateTime,
  accessCount: Integer,          // 47
  
  // Vector Embeddings
  contentEmbedding: [Float],     // Full content embedding
  summaryEmbedding: [Float],     // Summary embedding for quick matching
  
  // Analytics
  relevanceScore: Float,         // 0.87 (how often referenced)
  queryFrequency: Integer,       // 234
  
  // File Storage
  storageLocation: String,       // "s3://onevice-docs/2025/09/doc_345678.pdf"
  thumbnailUrl: String,          // Preview image URL
  previewUrl: String             // Web preview URL
})
```

#### 2.1.5 CreativeConcept Node

```cypher
// Creative concept node for tracking ideas and themes
CREATE CONSTRAINT concept_id FOR (c:CreativeConcept) REQUIRE c.id IS UNIQUE;
CREATE INDEX concept_category FOR (c:CreativeConcept) ON (c.category);

(:CreativeConcept {
  id: String,                    // UUID: "concept_901234"
  name: String,                  // "Urban Rooftop Performance"
  concept: String,               // Detailed description
  category: String,              // "Visual Style" | "Narrative" | "Technical" | "Thematic" | "Location"
  subcategory: String,           // "Performance Style" | "Lighting Design" | "Color Palette"
  
  // Concept Details
  description: String,           // Full description
  visualReference: [String],     // URLs to reference images
  mood: [String],                // ["Energetic", "Urban", "Raw"]
  colors: [String],              // ["Deep Blues", "Neon Accents", "Golden Hour"]
  
  // Usage and Context
  genres: [String],              // ["Hip-hop", "R&B", "Pop"]
  projectTypes: [String],        // ["Music Video", "Commercial"]
  budgetRequirements: String,    // "Medium" | "High" | "Low"
  technicalComplexity: Integer, // 1-10
  
  // Popularity and Trends
  trendScore: Float,             // 0.85 (current popularity)
  seasonality: [String],         // ["Spring", "Summer"]
  demographics: [String],        // ["18-34", "Urban", "Music Lovers"]
  
  // System Fields
  createdAt: DateTime,
  updatedAt: DateTime,
  isActive: Boolean,
  
  // Vector Embeddings
  conceptEmbedding: [Float],
  visualEmbedding: [Float],
  
  // Analytics
  usageCount: Integer,           // 23 (times used in projects)
  successRate: Float,            // 0.78 (success rate of projects using this concept)
  averageBudgetImpact: Float     // 1.15 (multiplier effect on budget)
})
```

#### 2.1.6 Union Node

```cypher
// Union node for labor organization information
CREATE CONSTRAINT union_id FOR (u:Union) REQUIRE u.id IS UNIQUE;
CREATE INDEX union_code FOR (u:Union) ON (u.unionCode);

(:Union {
  id: String,                    // UUID: "union_567890"
  name: String,                  // "International Alliance of Theatrical Stage Employees"
  unionCode: String,             // "IATSE" | "DGA" | "SAG-AFTRA" | "LOCAL_399"
  localNumber: String,           // "Local 600" | "Local 399"
  
  // Jurisdiction
  territories: [String],         // ["California", "Nevada", "Arizona"]
  primaryCity: String,           // "Los Angeles"
  region: String,                // "West Coast" | "East Coast" | "Southeast"
  
  // Contact Information
  headquarters: String,          // "Los Angeles, CA"
  phone: String,                 // "+1-323-876-1500"
  website: String,               // "https://iatse.net"
  email: String,                 // "info@iatse.net"
  
  // Membership
  memberCount: Integer,          // 150000
  activeMembers: Integer,        // 125000
  
  // Rate Information (Current Year)
  currentRates: {
    scale: {                     // Union scale rates
      daily: Float,              // 450.00
      weekly: Float,             // 2250.00
      overtime: Float            // 67.50 (hourly overtime)
    },
    holidays: [String],          // ["New Year's Day", "Memorial Day", ...]
    holidayPremium: Float,       // 1.5 (multiplier)
    weekendPremium: Float        // 1.2 (multiplier)
  },
  
  // Rules and Regulations
  minimumCallTime: Integer,      // 8 (hours)
  maximumWorkHours: Integer,     // 14 (hours per day)
  requiredBreaks: [String],      // ["30min lunch after 6hrs", "15min every 4hrs"]
  overtimeThreshold: Integer,    // 8 (hours before overtime)
  doubleTimeThreshold: Integer,  // 12 (hours before double time)
  
  // Administrative
  pensionRate: Float,            // 0.185 (18.5% of gross wages)
  healthRate: Float,             // 0.09 (9% of gross wages)
  vacationRate: Float,           // 0.045 (4.5% of gross wages)
  
  // Project Requirements
  minimumCrewSize: Integer,      // 5 (for union projects)
  stewardRequired: Boolean,      // true
  reportingRequirements: [String], // ["Daily reports", "Overtime logs"]
  
  // System Fields
  createdAt: DateTime,
  updatedAt: DateTime,
  isActive: Boolean,
  ratesLastUpdated: DateTime,    // 2025-01-01T00:00:00Z
  
  // Analytics
  projectCount: Integer,         // Number of projects under this union
  complianceScore: Float         // 0.96 (compliance rate)
})
```

### 2.2 Relationship Types and Properties

#### 2.2.1 Person-Project Relationships

```cypher
// DIRECTED relationship: Person directed a project
(:Person)-[:DIRECTED {
  role: String,                  // "Director" | "Co-Director"
  creditOrder: Integer,          // 1 (primary), 2 (secondary), etc.
  compensation: Float,           // 75000.00 (RBAC Level 1)
  contractType: String,          // "Work for Hire" | "Buyout" | "Royalty"
  startDate: Date,               // 2024-07-01
  endDate: Date,                 // 2024-08-15
  dayCount: Integer,             // 45
  responsibilities: [String],    // ["Creative Vision", "On-Set Direction"]
  notes: String,                 // Additional notes
  performanceRating: Float,      // 4.5 (out of 5)
  wouldWorkAgain: Boolean,       // true
  createdAt: DateTime,
  updatedAt: DateTime
}]->(:Project)

// CREATIVE_DIRECTED relationship: Person was creative director
(:Person)-[:CREATIVE_DIRECTED {
  role: String,                  // "Creative Director" | "Associate Creative Director"
  agency: String,                // "Wieden+Kennedy" (if external)
  creditOrder: Integer,          // 1
  conceptOwnership: Float,       // 0.8 (percentage of creative ownership)
  approvalAuthority: Boolean,    // true
  clientFacing: Boolean,         // true
  compensation: Float,           // 50000.00 (RBAC Level 1)
  startDate: Date,
  endDate: Date,
  responsibilities: [String],    // ["Concept Development", "Client Presentation"]
  createdAt: DateTime,
  updatedAt: DateTime
}]->(:Project)

// PERFORMED_IN relationship: Talent performed in project
(:Person)-[:PERFORMED_IN {
  role: String,                  // "Lead Performer" | "Featured Artist" | "Background Talent"
  characterName: String,         // "The Protagonist" (if narrative)
  screenTime: Integer,           // 180 (seconds)
  compensation: Float,           // 25000.00 (RBAC Level 1)
  hasRoyalties: Boolean,         // true
  royaltyPercentage: Float,      // 2.5
  unionMember: Boolean,          // true
  unionLocal: String,            // "SAG-AFTRA"
  startDate: Date,
  endDate: Date,
  createdAt: DateTime
}]->(:Project)

// PRODUCED relationship: Person produced the project
(:Person)-[:PRODUCED {
  role: String,                  // "Executive Producer" | "Producer" | "Line Producer"
  creditOrder: Integer,          // 1
  responsibilities: [String],    // ["Budget Management", "Scheduling", "Logistics"]
  compensation: Float,           // 100000.00 (RBAC Level 1)
  profitParticipation: Float,    // 5.0 (percentage)
  startDate: Date,
  endDate: Date,
  createdAt: DateTime
}]->(:Project)
```

#### 2.2.2 Person-Organization Relationships

```cypher
// WORKS_FOR relationship: Employment or representation
(:Person)-[:WORKS_FOR {
  position: String,              // "Staff Director" | "Freelance" | "Represented Talent"
  department: String,            // "Creative Department" | "Production"
  startDate: Date,               // 2020-03-01
  endDate: Date,                 // null (current)
  isCurrent: Boolean,            // true
  contractType: String,          // "Full-time" | "Freelance" | "Retainer" | "Representation"
  exclusivity: String,           // "Exclusive" | "Non-exclusive" | "Category Exclusive"
  commissionRate: Float,         // 0.10 (10% for representation)
  territories: [String],         // ["North America", "Europe"]
  
  // Performance Metrics
  projectsCompleted: Integer,    // 23
  averageProjectValue: Float,    // 275000.00
  clientSatisfactionScore: Float, // 4.7
  
  createdAt: DateTime,
  updatedAt: DateTime
}]->(:Organization)

// COLLABORATED_WITH relationship: Person-to-Person collaborations
(:Person)-[:COLLABORATED_WITH {
  projects: [String],            // ["proj_123", "proj_456", "proj_789"]
  relationshipType: String,      // "Frequent" | "Occasional" | "One-time"
  totalProjects: Integer,        // 3
  successRate: Float,            // 0.85
  lastCollaboration: Date,       // 2024-08-15
  workingRelationship: String,   // "Excellent" | "Good" | "Challenging"
  complementarySkills: [String], // ["Technical", "Creative", "Leadership"]
  preferredRoles: [String],      // ["director_producer", "creative_director"]
  
  createdAt: DateTime,
  updatedAt: DateTime
}]->(:Person)
```

#### 2.2.3 Project-Organization Relationships

```cypher
// FOR_CLIENT relationship: Project done for client
(:Project)-[:FOR_CLIENT {
  contractValue: Float,          // 500000.00 (RBAC Level 1)
  contractType: String,          // "Fixed Price" | "Time and Materials" | "Cost Plus"
  paymentSchedule: String,       // "50% upfront, 50% on delivery"
  paymentStatus: String,         // "Paid" | "Outstanding" | "Overdue"
  clientContact: String,         // "John Smith"
  accountManager: String,        // "Jane Doe"
  
  // Contract Terms
  deliverables: [String],        // ["4K Master", "Social Media Cuts", "BTS"]
  revisionRounds: Integer,       // 3
  approvalProcess: [String],     // ["Creative Director", "Brand Manager", "Legal"]
  
  // Performance
  onTime: Boolean,               // true
  onBudget: Boolean,             // true
  clientSatisfaction: Float,     // 4.8
  repeatClient: Boolean,         // true
  
  startDate: Date,
  endDate: Date,
  createdAt: DateTime
}]->(:Organization)

// PRODUCED_BY relationship: Production company produced project
(:Project)-[:PRODUCED_BY {
  productionRole: String,        // "Lead Production" | "Co-Production" | "Service Production"
  ownershipPercentage: Float,    // 100.0
  profitParticipation: Float,    // 25.0
  responsibilities: [String],    // ["Crew", "Equipment", "Locations", "Post"]
  
  createdAt: DateTime
}]->(:Organization)
```

#### 2.2.4 Project-Union Relationships

```cypher
// UNION_PROJECT relationship: Project follows union rules
(:Project)-[:UNION_PROJECT {
  unionCode: String,             // "IATSE" | "DGA" | "SAG-AFTRA"
  contractNumber: String,        // "IATSE-2024-MV-001234"
  signatory: String,             // "London Alley Productions"
  
  // Compliance Information
  ratesUsed: {
    scale: Float,                // 450.00
    overtime: Float,             // 67.50
    doubletime: Float            // 90.00
  },
  totalUnionCosts: Float,        // 45000.00 (RBAC Level 1)
  pensionContributions: Float,   // 8325.00 (RBAC Level 1)
  healthContributions: Float,    // 4050.00 (RBAC Level 1)
  
  // Compliance Status
  complianceStatus: String,      // "Compliant" | "Under Review" | "Violation"
  filingStatus: String,          // "Filed" | "Pending" | "Overdue"
  reportsDue: Date,              // 2024-09-01
  
  createdAt: DateTime,
  updatedAt: DateTime
}]->(:Union)
```

#### 2.2.5 Document Relationships

```cypher
// DESCRIBES relationship: Document describes project/person
(:Document)-[:DESCRIBES {
  relevanceScore: Float,         // 0.92
  documentPhase: String,         // "Pitch" | "Pre-Production" | "Production"
  isMainDocument: Boolean,       // true
  extractedEntities: [String],   // Entities found in document
  createdAt: DateTime
}]->(:Project)

(:Document)-[:MENTIONS {
  mentionCount: Integer,         // 15
  contextType: String,           // "Positive" | "Neutral" | "Negative" | "Reference"
  relevanceScore: Float,         // 0.87
  pageNumbers: [Integer],        // [1, 5, 12, 18]
  createdAt: DateTime
}]->(:Person)
```

#### 2.2.6 Creative Concept Relationships

```cypher
// INCORPORATES relationship: Project incorporates creative concepts
(:Project)-[:INCORPORATES {
  prominence: String,            // "Primary" | "Secondary" | "Background"
  executionScore: Float,         // 0.89 (how well was it executed)
  budgetImpact: Float,           // 1.15 (multiplier effect on budget)
  clientReaction: String,        // "Positive" | "Neutral" | "Negative"
  
  createdAt: DateTime
}]->(:CreativeConcept)

// RELATED_TO relationship: Concept relationships
(:CreativeConcept)-[:RELATED_TO {
  relationshipType: String,      // "Similar" | "Complementary" | "Contrasting"
  strength: Float,               // 0.75
  contextualSimilarity: Float,   // 0.82
  visualSimilarity: Float,       // 0.68
  
  createdAt: DateTime
}]->(:CreativeConcept)
```

### 2.3 Vector Search Integration

#### 2.3.1 Vector Index Configuration

```cypher
// Create vector indexes for semantic search
CREATE VECTOR INDEX person_profile_vector 
FOR (p:Person) ON p.profileEmbedding 
OPTIONS {indexConfig: {
  `vector.dimensions`: 1536,
  `vector.similarity_function`: 'cosine'
}};

CREATE VECTOR INDEX person_skills_vector 
FOR (p:Person) ON p.skillsEmbedding 
OPTIONS {indexConfig: {
  `vector.dimensions`: 1536,
  `vector.similarity_function`: 'cosine'
}};

CREATE VECTOR INDEX project_concept_vector 
FOR (p:Project) ON p.conceptEmbedding 
OPTIONS {indexConfig: {
  `vector.dimensions`: 1536,
  `vector.similarity_function`: 'cosine'
}};

CREATE VECTOR INDEX document_content_vector 
FOR (d:Document) ON d.contentEmbedding 
OPTIONS {indexConfig: {
  `vector.dimensions`: 1536,
  `vector.similarity_function`: 'cosine'
}};

CREATE VECTOR INDEX concept_semantic_vector 
FOR (c:CreativeConcept) ON c.conceptEmbedding 
OPTIONS {indexConfig: {
  `vector.dimensions`: 1536,
  `vector.similarity_function`: 'cosine'
}};
```

#### 2.3.2 Hybrid Search Queries

```cypher
// Example: Find similar projects using vector + graph traversal
CALL db.index.vector.queryNodes('project_concept_vector', 5, $queryEmbedding)
YIELD node AS similarProject, score AS vectorScore
MATCH (similarProject)-[:INCORPORATES]->(concept:CreativeConcept)
MATCH (concept)<-[:INCORPORATES]-(relatedProject:Project)
WHERE relatedProject.budgetTier = $budgetTier
  AND relatedProject.type = $projectType
RETURN similarProject, relatedProject, vectorScore,
       collect(concept.name) AS sharedConcepts
ORDER BY vectorScore DESC
LIMIT 10;

// Example: Find talent with similar skills and experience
CALL db.index.vector.queryNodes('person_skills_vector', 10, $skillsEmbedding)
YIELD node AS person, score AS skillScore
MATCH (person)-[directed:DIRECTED]->(project:Project)
WHERE project.type = $projectType
  AND project.budgetTier IN $budgetTiers
  AND person.unionStatus = $unionStatus
WITH person, skillScore, count(directed) AS projectCount
RETURN person, skillScore, projectCount,
       [(person)-[:DIRECTED]->(p:Project) | p.name] AS recentProjects
ORDER BY skillScore DESC, projectCount DESC
LIMIT 20;
```

## 3. Redis Caching Schema

### 3.1 Session Management

```json
{
  "key_pattern": "session:{user_id}:{session_id}",
  "example_key": "session:user_123:sess_abc789",
  "ttl": 86400,
  "data_structure": "hash",
  "fields": {
    "user_id": "user_123",
    "session_id": "sess_abc789",
    "role": "Leadership",
    "permissions": "[\"read:all\", \"write:projects\"]",
    "data_sensitivity_level": 1,
    "last_activity": "2025-09-01T12:30:00Z",
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0...",
    "websocket_connections": "[\"ws_conn_1\", \"ws_conn_2\"]",
    "active_threads": "[\"thread_abc\", \"thread_def\"]",
    "preferences": "{\"theme\": \"dark\", \"default_agent\": \"sales_intelligence\"}"
  }
}
```

### 3.2 Query Result Caching

```json
{
  "key_pattern": "query:{agent}:{query_hash}:{user_role}",
  "example_key": "query:sales_intelligence:md5_abc123:Leadership",
  "ttl": 1800,
  "data_structure": "string",
  "value": {
    "query": "Research Cordae for music video pitch",
    "result": {
      "summary": "Cordae is a Grammy-nominated rapper...",
      "entities": [...],
      "confidence_score": 0.92,
      "processing_time_ms": 1847
    },
    "cached_at": "2025-09-01T12:00:00Z",
    "expires_at": "2025-09-01T12:30:00Z"
  }
}
```

### 3.3 WebSocket Connection Management

```json
{
  "key_pattern": "websocket:{connection_id}",
  "example_key": "websocket:ws_user123_thread456_1693574400",
  "ttl": 3600,
  "data_structure": "hash",
  "fields": {
    "connection_id": "ws_user123_thread456_1693574400",
    "user_id": "user_123",
    "thread_id": "thread_456",
    "role": "Director",
    "connected_at": "2025-09-01T12:00:00Z",
    "last_ping": "2025-09-01T12:29:45Z",
    "status": "connected",
    "selected_agent": "case_study",
    "message_queue": "[\"msg_1\", \"msg_2\"]",
    "rate_limit_count": 15,
    "rate_limit_reset": "2025-09-01T12:01:00Z"
  }
}
```

### 3.4 Union Rules Caching

```json
{
  "key_pattern": "union_rules:{union_code}:{state}:{year}",
  "example_key": "union_rules:IATSE:CA:2025",
  "ttl": 21600,
  "data_structure": "hash",
  "fields": {
    "union_code": "IATSE",
    "state": "CA",
    "year": 2025,
    "scale_rates": {
      "daily": 450.00,
      "weekly": 2250.00,
      "overtime": 67.50,
      "doubletime": 90.00
    },
    "holidays": "[\"2025-01-01\", \"2025-05-26\", ...]",
    "holiday_premium": 1.5,
    "weekend_premium": 1.2,
    "pension_rate": 0.185,
    "health_rate": 0.09,
    "vacation_rate": 0.045,
    "minimum_call": 8,
    "maximum_hours": 14,
    "overtime_threshold": 8,
    "doubletime_threshold": 12,
    "last_updated": "2025-01-01T00:00:00Z",
    "source_url": "https://iatse.net/rates/2025/california"
  }
}
```

### 3.5 Performance Metrics Caching

```json
{
  "key_pattern": "metrics:{metric_type}:{timeframe}:{timestamp}",
  "example_key": "metrics:agent_performance:5min:20250901_1200",
  "ttl": 300,
  "data_structure": "sorted_set",
  "members": {
    "sales_intelligence": 23.5,
    "case_study": 18.7,
    "talent_discovery": 31.2,
    "bidding_support": 12.8
  },
  "metadata": {
    "timestamp": "2025-09-01T12:00:00Z",
    "unit": "queries_per_minute",
    "total_queries": 86
  }
}
```

### 3.6 Chat History Caching

```json
{
  "key_pattern": "chat_history:{thread_id}",
  "example_key": "chat_history:thread_abc123",
  "ttl": 604800,
  "data_structure": "list",
  "values": [
    {
      "message_id": "msg_123",
      "role": "user",
      "content": "Research Cordae for music video",
      "timestamp": "2025-09-01T11:58:30Z",
      "user_id": "user_123"
    },
    {
      "message_id": "msg_124",
      "role": "assistant",
      "content": "Cordae is a Grammy-nominated rapper...",
      "timestamp": "2025-09-01T11:58:32Z",
      "agent": "sales_intelligence",
      "confidence_score": 0.92,
      "sources": ["neo4j", "industry_apis"]
    }
  ]
}
```

### 3.7 Rate Limiting

```json
{
  "key_pattern": "rate_limit:{user_id}:{endpoint}",
  "example_key": "rate_limit:user_123:agent_query",
  "ttl": 60,
  "data_structure": "string",
  "value": "15",
  "metadata": {
    "limit": 20,
    "window": 60,
    "reset_time": "2025-09-01T12:01:00Z"
  }
}
```

## 4. Data Migration Strategy

### 4.1 ETL Pipeline Architecture

#### Phase 1: Document Ingestion

```python
class DocumentIngestionPipeline:
    def __init__(self):
        self.supported_formats = ['.pdf', '.docx', '.pptx', '.txt', '.md']
        self.processors = {
            '.pdf': PDFProcessor(),
            '.docx': WordProcessor(),
            '.pptx': PowerPointProcessor(),
            '.txt': TextProcessor(),
            '.md': MarkdownProcessor()
        }
    
    def process_document_batch(self, document_paths: List[str]) -> List[ProcessedDocument]:
        """Process a batch of documents with error handling and progress tracking"""
        results = []
        
        for doc_path in document_paths:
            try:
                # 1. File validation
                self.validate_file(doc_path)
                
                # 2. Content extraction
                processor = self.get_processor(doc_path)
                content = processor.extract_content(doc_path)
                
                # 3. Metadata extraction
                metadata = self.extract_metadata(doc_path, content)
                
                # 4. Content cleaning and normalization
                cleaned_content = self.clean_content(content)
                
                # 5. Create processed document
                processed_doc = ProcessedDocument(
                    filename=Path(doc_path).name,
                    content=cleaned_content,
                    metadata=metadata,
                    processing_status='completed'
                )
                
                results.append(processed_doc)
                
            except Exception as e:
                # Log error and create failed document record
                error_doc = ProcessedDocument(
                    filename=Path(doc_path).name,
                    processing_status='failed',
                    error_message=str(e)
                )
                results.append(error_doc)
                
        return results
```

#### Phase 2: Entity Extraction

```python
class EntertainmentEntityExtractor:
    def __init__(self):
        self.llm_client = LocalLlamaClient()
        self.entity_types = [
            'PERSON', 'ORGANIZATION', 'PROJECT', 
            'LOCATION', 'MONEY', 'DATE', 'CREATIVE_CONCEPT'
        ]
        
    def extract_entities(self, document: ProcessedDocument) -> EntityExtractionResult:
        """Extract entertainment industry-specific entities"""
        
        # 1. Named Entity Recognition
        ner_results = self.extract_named_entities(document.content)
        
        # 2. Entertainment-specific entity classification
        classified_entities = self.classify_entertainment_entities(ner_results)
        
        # 3. Relationship extraction
        relationships = self.extract_relationships(document.content, classified_entities)
        
        # 4. Role disambiguation (Director vs Creative Director)
        disambiguated_roles = self.disambiguate_roles(classified_entities, document.content)
        
        # 5. Budget and financial information extraction
        financial_entities = self.extract_financial_information(document.content)
        
        return EntityExtractionResult(
            persons=disambiguated_roles.get('persons', []),
            organizations=classified_entities.get('organizations', []),
            projects=classified_entities.get('projects', []),
            creative_concepts=classified_entities.get('creative_concepts', []),
            financial_data=financial_entities,
            relationships=relationships,
            confidence_scores=self.calculate_confidence_scores()
        )
    
    def disambiguate_roles(self, entities: Dict, context: str) -> Dict:
        """Critical: Distinguish between Director and Creative Director roles"""
        
        director_indicators = [
            'directed by', 'director:', 'helm', 'behind the camera',
            'shot by', 'filmed by', 'execution', 'production'
        ]
        
        creative_director_indicators = [
            'creative director', 'concept by', 'creative lead', 
            'idea from', 'conceived by', 'creative vision', 'strategy'
        ]
        
        disambiguated = {'persons': []}
        
        for person in entities.get('persons', []):
            person_context = self.get_person_context(person['name'], context)
            
            # Analyze context to determine role
            director_score = self.calculate_indicator_score(
                person_context, director_indicators
            )
            creative_director_score = self.calculate_indicator_score(
                person_context, creative_director_indicators
            )
            
            # Assign role based on highest score
            if director_score > creative_director_score:
                person['role_type'] = 'Director'
            elif creative_director_score > director_score:
                person['role_type'] = 'Creative Director'
            else:
                person['role_type'] = 'Unknown'
            
            person['role_confidence'] = max(director_score, creative_director_score)
            disambiguated['persons'].append(person)
            
        return disambiguated
```

#### Phase 3: Graph Population

```python
class Neo4jGraphPopulator:
    def __init__(self, neo4j_driver):
        self.driver = neo4j_driver
        self.entity_deduplicator = EntityDeduplicator()
        
    def populate_graph(self, extraction_results: List[EntityExtractionResult]) -> PopulationResult:
        """Populate Neo4j graph with extracted entities and relationships"""
        
        stats = PopulationResult()
        
        with self.driver.session() as session:
            # 1. Create persons with role disambiguation
            for person_data in extraction_results.persons:
                deduplicated_person = self.entity_deduplicator.deduplicate_person(person_data)
                
                person_query = """
                MERGE (p:Person {name: $name})
                SET p.id = $id,
                    p.roleType = $role_type,
                    p.unionStatus = $union_status,
                    p.specializations = $specializations,
                    p.budgetRange = $budget_range,
                    p.profileEmbedding = $profile_embedding,
                    p.createdAt = datetime(),
                    p.updatedAt = datetime(),
                    p.verificationStatus = $verification_status,
                    p.visibilityLevel = $visibility_level
                RETURN p
                """
                
                session.run(person_query, **deduplicated_person)
                stats.persons_created += 1
            
            # 2. Create projects with budget sensitivity
            for project_data in extraction_results.projects:
                project_query = """
                MERGE (proj:Project {name: $name})
                SET proj.id = $id,
                    proj.type = $type,
                    proj.status = $status,
                    proj.totalBudget = $total_budget,
                    proj.budgetTier = $budget_tier,
                    proj.unionStatus = $union_status,
                    proj.sensitivityLevel = $sensitivity_level,
                    proj.conceptEmbedding = $concept_embedding,
                    proj.createdAt = datetime(),
                    proj.updatedAt = datetime()
                RETURN proj
                """
                
                session.run(project_query, **project_data)
                stats.projects_created += 1
            
            # 3. Create relationships with proper attribution
            for relationship in extraction_results.relationships:
                if relationship.type == 'DIRECTED':
                    rel_query = """
                    MATCH (p:Person {name: $person_name})
                    MATCH (proj:Project {name: $project_name})
                    MERGE (p)-[r:DIRECTED]->(proj)
                    SET r.role = $role,
                        r.compensation = $compensation,
                        r.startDate = date($start_date),
                        r.endDate = date($end_date),
                        r.createdAt = datetime()
                    RETURN r
                    """
                    
                    session.run(rel_query, **relationship.properties)
                    stats.relationships_created += 1
        
        return stats

class EntityDeduplicator:
    def __init__(self):
        self.name_similarity_threshold = 0.9
        self.fuzzy_matcher = FuzzyMatcher()
        
    def deduplicate_person(self, person_data: Dict) -> Dict:
        """Deduplicate person entities using fuzzy matching and context analysis"""
        
        # 1. Name normalization
        normalized_name = self.normalize_name(person_data['name'])
        
        # 2. Find potential duplicates
        potential_duplicates = self.find_similar_persons(normalized_name)
        
        # 3. Context-based disambiguation
        if potential_duplicates:
            best_match = self.disambiguate_by_context(person_data, potential_duplicates)
            if best_match:
                # Merge data with existing entity
                return self.merge_person_data(person_data, best_match)
        
        # 4. Create new entity
        person_data['id'] = f"person_{uuid.uuid4()}"
        person_data['name'] = normalized_name
        return person_data
```

### 4.2 Data Validation and Quality Assurance

```python
class DataQualityValidator:
    def __init__(self):
        self.validation_rules = {
            'person': PersonValidationRules(),
            'project': ProjectValidationRules(),
            'organization': OrganizationValidationRules()
        }
        
    def validate_entity_data(self, entity_type: str, data: Dict) -> ValidationResult:
        """Validate entity data against business rules"""
        
        validator = self.validation_rules[entity_type]
        issues = []
        
        # 1. Required field validation
        missing_fields = validator.check_required_fields(data)
        issues.extend(missing_fields)
        
        # 2. Data format validation
        format_issues = validator.validate_formats(data)
        issues.extend(format_issues)
        
        # 3. Business rule validation
        business_issues = validator.validate_business_rules(data)
        issues.extend(business_issues)
        
        # 4. Cross-reference validation
        reference_issues = validator.validate_references(data)
        issues.extend(reference_issues)
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            issues=issues,
            severity_counts={
                'error': len([i for i in issues if i.severity == 'error']),
                'warning': len([i for i in issues if i.severity == 'warning']),
                'info': len([i for i in issues if i.severity == 'info'])
            }
        )

class PersonValidationRules:
    def validate_business_rules(self, data: Dict) -> List[ValidationIssue]:
        """Validate person-specific business rules"""
        issues = []
        
        # Director vs Creative Director validation
        if data.get('roleType') == 'Director':
            if not self.has_director_indicators(data):
                issues.append(ValidationIssue(
                    field='roleType',
                    message='Person classified as Director but lacks director indicators',
                    severity='warning',
                    suggestion='Review role classification'
                ))
        
        # Union status validation
        if data.get('unionStatus') == 'Union' and not data.get('unionLocal'):
            issues.append(ValidationIssue(
                field='unionLocal',
                message='Union person should have union local specified',
                severity='error',
                suggestion='Add union local information'
            ))
        
        # Budget range validation
        budget_range = data.get('budgetRange')
        if budget_range and not self.is_valid_budget_range(budget_range):
            issues.append(ValidationIssue(
                field='budgetRange',
                message=f'Invalid budget range format: {budget_range}',
                severity='error',
                suggestion='Use format: $X-Y or $X+'
            ))
        
        return issues
```

## 5. Database Optimization and Performance

### 5.1 Neo4j Performance Optimization

#### Index Strategy

```cypher
-- Core entity indexes for fast lookups
CREATE INDEX person_name_text FOR (p:Person) ON (p.name);
CREATE INDEX person_role_union FOR (p:Person) ON (p.roleType, p.unionStatus);
CREATE INDEX project_type_budget FOR (p:Project) ON (p.type, p.budgetTier);
CREATE INDEX org_type_tier FOR (o:Organization) ON (o.type, o.tier);
CREATE INDEX doc_type_sensitivity FOR (d:Document) ON (d.type, d.sensitivityLevel);

-- Composite indexes for complex queries
CREATE INDEX person_role_specialization FOR (p:Person) ON (p.roleType, p.specializations);
CREATE INDEX project_status_union FOR (p:Project) ON (p.status, p.unionStatus);
CREATE INDEX project_date_range FOR (p:Project) ON (p.shootStartDate, p.shootEndDate);

-- Full-text search indexes
CREATE FULLTEXT INDEX person_search_index FOR (p:Person) ON EACH [p.name, p.bio, p.specializations];
CREATE FULLTEXT INDEX project_search_index FOR (p:Project) ON EACH [p.name, p.concepts, p.mood];
CREATE FULLTEXT INDEX document_search_index FOR (d:Document) ON EACH [d.title, d.fullTextContent, d.summary];
```

#### Query Performance Patterns

```cypher
-- Optimized talent discovery query with proper indexes
MATCH (p:Person)
WHERE p.roleType = $roleType
  AND p.unionStatus = $unionStatus
  AND any(spec IN p.specializations WHERE spec IN $requiredSpecializations)
OPTIONAL MATCH (p)-[directed:DIRECTED]->(project:Project)
WHERE project.budgetTier IN $budgetTiers
  AND project.completionDate >= date('2020-01-01')
WITH p, count(directed) AS projectCount,
     collect(project.name)[..5] AS recentProjects
WHERE projectCount >= $minProjects
RETURN p.id, p.name, p.unionStatus, p.budgetRange, projectCount, recentProjects
ORDER BY projectCount DESC
LIMIT $limit;

-- Memory-efficient pagination for large result sets
MATCH (p:Person)
WHERE p.roleType = $roleType
WITH p
ORDER BY p.name
SKIP $skip
LIMIT $pageSize
OPTIONAL MATCH (p)-[:DIRECTED]->(recent:Project)
WHERE recent.completionDate >= date('2023-01-01')
RETURN p, collect(recent.name)[..3] AS recentWork;
```

### 5.2 Redis Performance Optimization

#### Connection Pooling Configuration

```python
import redis
import os
from typing import Optional

class RemoteRedisConnectionManager:
    """Connection manager for Redis Cloud or AWS ElastiCache"""
    
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL")  # rediss://[user]:[pass]@[host]:6380
        self.pool_size = int(os.getenv("REDIS_POOL_SIZE", "20"))
        
        # Configure connection pool for remote Redis with TLS
        self.pool = redis.ConnectionPool.from_url(
            self.redis_url,
            max_connections=self.pool_size,
            socket_timeout=10,
            socket_connect_timeout=10,
            socket_keepalive=True,
            socket_keepalive_options={
                1: 1,  # TCP_KEEPIDLE
                2: 3,  # TCP_KEEPINTVL  
                3: 5,  # TCP_KEEPCNT
            },
            decode_responses=True,
            retry_on_timeout=True,
            retry_on_error=[redis.ConnectionError, redis.TimeoutError],
            health_check_interval=30,
            ssl_cert_reqs=None,  # Required for Redis Cloud
            ssl_check_hostname=False  # Required for some managed Redis services
        )
        
        self.redis_client = redis.Redis(connection_pool=self.pool)
        
    def get_client(self) -> redis.Redis:
        return self.redis_client
    
    def test_connection(self) -> bool:
        """Test remote Redis connection"""
        try:
            self.redis_client.ping()
            return True
        except (redis.ConnectionError, redis.TimeoutError):
            return False
```

#### Caching Strategies

```python
class IntelligentCacheManager:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.cache_strategies = {
            'query_results': {'ttl': 1800, 'strategy': 'user_role_aware'},
            'union_rules': {'ttl': 21600, 'strategy': 'versioned'},
            'session_data': {'ttl': 86400, 'strategy': 'sliding_expiration'},
            'metrics': {'ttl': 300, 'strategy': 'time_windowed'}
        }
    
    def cache_query_result(self, agent: str, query: str, user_role: str, result: Dict):
        """Cache query results with role-based keys"""
        query_hash = hashlib.md5(query.encode()).hexdigest()
        cache_key = f"query:{agent}:{query_hash}:{user_role}"
        
        cache_data = {
            'result': json.dumps(result),
            'cached_at': datetime.utcnow().isoformat(),
            'user_role': user_role,
            'query_hash': query_hash
        }
        
        ttl = self.cache_strategies['query_results']['ttl']
        self.redis.setex(cache_key, ttl, json.dumps(cache_data))
        
        # Also cache with role-agnostic key for partial matches
        generic_key = f"query:{agent}:{query_hash}:generic"
        generic_result = self.filter_result_for_generic_cache(result)
        self.redis.setex(generic_key, ttl // 2, json.dumps({
            'result': json.dumps(generic_result),
            'cached_at': datetime.utcnow().isoformat()
        }))
    
    def get_cached_query_result(self, agent: str, query: str, user_role: str) -> Optional[Dict]:
        """Retrieve cached query results with role fallback"""
        query_hash = hashlib.md5(query.encode()).hexdigest()
        
        # Try role-specific cache first
        role_specific_key = f"query:{agent}:{query_hash}:{user_role}"
        cached_data = self.redis.get(role_specific_key)
        
        if cached_data:
            return json.loads(cached_data)
        
        # Fall back to generic cache if available
        generic_key = f"query:{agent}:{query_hash}:generic"
        generic_data = self.redis.get(generic_key)
        
        if generic_data:
            # Apply role-based filtering to generic result
            generic_result = json.loads(generic_data)
            return self.apply_role_filtering(generic_result, user_role)
        
        return None
```

## 6. Remote Database Connection Patterns

### 6.1 Neo4j Aura Connection Management

```python
from neo4j import GraphDatabase
import os
from typing import Dict, List, Optional
import logging

class Neo4jAuraClient:
    """Connection client for Neo4j Aura remote database"""
    
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI")  # neo4j+s://[id].databases.neo4j.io:7687
        self.username = os.getenv("NEO4J_USERNAME", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD")
        
        if not all([self.uri, self.password]):
            raise ValueError("Neo4j Aura connection parameters missing")
            
        # Configure driver for remote connection with TLS
        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(self.username, self.password),
            max_connection_lifetime=3600,  # 1 hour
            max_connection_pool_size=50,
            connection_acquisition_timeout=60,
            encrypted=True  # Required for Neo4j Aura
        )
        
        self.logger = logging.getLogger(__name__)
    
    def test_connection(self) -> bool:
        """Test Neo4j Aura connection"""
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                return result.single()["test"] == 1
        except Exception as e:
            self.logger.error(f"Neo4j Aura connection test failed: {e}")
            return False
    
    def run_query(self, query: str, parameters: Dict = None) -> List[Dict]:
        """Execute Cypher query with connection retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with self.driver.session() as session:
                    result = session.run(query, parameters or {})
                    return [record.data() for record in result]
            except Exception as e:
                if attempt == max_retries - 1:
                    self.logger.error(f"Neo4j query failed after {max_retries} attempts: {e}")
                    raise
                self.logger.warning(f"Neo4j query attempt {attempt + 1} failed, retrying: {e}")
    
    def close(self):
        """Close Neo4j driver connection"""
        if self.driver:
            self.driver.close()
```

### 6.2 Supabase PostgreSQL Integration

```python
from supabase import create_client, Client
import os
import asyncpg
from typing import Dict, List, Optional

class SupabasePostgreSQLClient:
    """Connection client for Supabase PostgreSQL"""
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self.database_url = os.getenv("DATABASE_URL")
        
        if not all([self.supabase_url, self.supabase_key, self.database_url]):
            raise ValueError("Supabase connection parameters missing")
            
        # Initialize Supabase client
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
    async def get_async_pool(self):
        """Create async PostgreSQL connection pool"""
        return await asyncpg.create_pool(
            self.database_url,
            min_size=5,
            max_size=20,
            server_settings={
                'application_name': 'OneVice Backend',
            }
        )
    
    def test_connection(self) -> bool:
        """Test Supabase connection"""
        try:
            # Test with a simple query
            result = self.supabase.table("_supabase_migrations").select("*").limit(1).execute()
            return result.data is not None
        except Exception as e:
            return False
```

## 7. Backup and Disaster Recovery (Remote Services)

### 7.1 Managed Service Backup Strategy

```bash
#!/bin/bash
# Neo4j backup script with encryption and rotation

BACKUP_DIR="/backups/neo4j"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="onevice_neo4j_$DATE"
ENCRYPTION_KEY="/etc/onevice/backup.key"
RETENTION_DAYS=30

# Create backup
neo4j-admin database backup --database=neo4j \
  --to-path="$BACKUP_DIR/$BACKUP_NAME" \
  --verbose

# Encrypt backup
tar -czf "$BACKUP_DIR/$BACKUP_NAME.tar.gz" -C "$BACKUP_DIR" "$BACKUP_NAME"
openssl enc -aes-256-cbc -salt -in "$BACKUP_DIR/$BACKUP_NAME.tar.gz" \
  -out "$BACKUP_DIR/$BACKUP_NAME.tar.gz.enc" -pass file:"$ENCRYPTION_KEY"

# Clean up unencrypted files
rm -rf "$BACKUP_DIR/$BACKUP_NAME"
rm "$BACKUP_DIR/$BACKUP_NAME.tar.gz"

# Upload to cloud storage
aws s3 cp "$BACKUP_DIR/$BACKUP_NAME.tar.gz.enc" \
  "s3://onevice-backups/neo4j/$BACKUP_NAME.tar.gz.enc"

# Cleanup old backups
find "$BACKUP_DIR" -name "*.tar.gz.enc" -mtime +$RETENTION_DAYS -delete
```

### 6.2 Redis Persistence Configuration

```conf
# redis.conf optimized for OneVice
save 900 1      # Save if at least 1 key changed in 900 seconds
save 300 10     # Save if at least 10 keys changed in 300 seconds  
save 60 10000   # Save if at least 10000 keys changed in 60 seconds

# Enable AOF for durability
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb

# Memory optimization
maxmemory 8gb
maxmemory-policy allkeys-lru
maxmemory-samples 5

# Security
requirepass ${REDIS_PASSWORD}
rename-command FLUSHALL ""
rename-command FLUSHDB ""
rename-command CONFIG "CONFIG_67ac2f35"
```

---

**Document Status**: Ready for Implementation  
**Last Updated**: September 1, 2025  
**Next Review**: Upon completion of database implementation