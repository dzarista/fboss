# Frontend Architecture & Setup

## Overview

This document covers the frontend architecture of Showtech Viewer.

**Technology**
- **React 18** - Component-based UI framework
- **JavaScript ES6+** - Modern JavaScript features
- **CSS3** - Component-scoped styling

## Core Components

**App.js - Application Root**: Main application container and state management
**Sidebar.js - File Management Panel**: File upload and management interface
**Content.js - Main Content Display**: Primary data visualization and interaction area
**UploadModal.js - File Upload Interface**: File upload with drag & drop functionality
**SectionFilter.js - Navigation & Filtering** Section management and quick navigation

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

### API Communication (utils/api.js)

**Purpose**: Centralized backend communication with error handling and timeout management.

```javascript
// File upload with progress tracking
export const uploadFiles = async (files, onProgress) => {
  const formData = new FormData();
  // Implementation with fetch API and progress callbacks
};

// Health check for backend connectivity
export const checkBackendHealth = async () => {
  // Verify backend is running and responsive
};
```

## Setup
For complete deployment instructions including Docker setup and troubleshooting, see [`../deployment.md`](../deployment.md)