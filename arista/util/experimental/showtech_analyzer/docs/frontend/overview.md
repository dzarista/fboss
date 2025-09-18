# Frontend Architecture & Setup

## Overview

This document covers the frontend architecture of Showtech Viewer.

**Technology**: React, JavaScript, CSS, Docker

## Core Components
- **App.js - Application Root**: Main application container and state management
- **Sidebar.js - File Management Panel**: File upload and session management interface
- **Content.js - Main Content Display**: Primary data visualization and interaction area
- **UploadModal.js - File Upload Interface**: File upload with drag & drop functionality
- **SectionFilter.js - Navigation & Filtering**: Section management and quick navigation
- **SessionManager.js - Session Management**: Session creation, listing, and management
- **SystemSummary.js - Hardware Overview**: Visual hardware status and monitoring

## Styling System

### CSS Architecture

The frontend uses a **component-scoped CSS** approach where each React component has its own dedicated stylesheet in the `styles/components/` directory.

#### **File Organization**
```
styles/
├── base.css             # CSS resets and base element styles
├── themes.css           # CSS variables and theme definitions
└── components/          # Component-specific styles
    ├── App.css          # Root application layout
    └-- ...
```

#### **Styling Conventions**

**CSS Variables (themes.css)**
```css
:root {
  --bg-primary: #ffffff;
  --bg-secondary: #f8fafc;
  --text-primary: #1f2937;
  --text-secondary: #6b7280;
  --accent-button: #2563eb;
  --border-default: #e5e7eb;
  --error-color: #dc2626;
  --success-color: #059669;
}
```
**Base Styles (base.css)**
- CSS resets and normalization
- Base element styling (typography, forms, buttons)
- Default spacing and layout foundations

## Utility Functions

### API Communication
- **`utils/api.js`**: File upload and backend health checks
- **`utils/sessionApi.js`**: Session management (create, list, update, delete)
- **`utils/urlManager.js`**: URL state management and deep linking
- **`utils/extractors.js`**: Data extraction utilities
- **`utils/app_utils.js`**: General application utilities

## Setup
For complete deployment instructions including Docker setup and troubleshooting, see [`../deployment.md`](../deployment.md)