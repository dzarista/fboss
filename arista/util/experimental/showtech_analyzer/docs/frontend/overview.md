# Frontend Architecture & Setup

## Overview

This document covers the React-based frontend architecture, including component structure, file organization, styling system, and setup instructions. The frontend provides an interactive interface for uploading, visualizing, and analyzing diagnostic log files.

**Technology Stack:**
- **React 18** - Component-based UI framework
- **JavaScript ES6+** - Modern JavaScript features
- **CSS3** - Component-scoped styling
- **Browser APIs** - localStorage for caching, File API for uploads

## Component Architecture

### Component Hierarchy

```
App.js (Root)
├── Sidebar.js (File Management)
│   └── UploadModal.js (File Upload)
├── Content.js (Main Display)
│   ├── SectionContentRenderer (Data Visualization)
│   ├── ErrorSummaryModal (Anomaly Reporting)
│   └── I2CBitRangeModal (I2C Analysis)
└── SectionFilter.js (Navigation & Filtering)
```

### Core Components

#### **App.js - Application Root**
- **Purpose**: Main application container and state management
- **Responsibilities**:
  - Global state management (files, active selections, UI state)
  - Coordinate communication between sidebar, content, and filter components
  - Handle dual-file viewing logic and active window management
  - Manage modal visibility and global UI interactions

#### **Sidebar.js - File Management Panel**
- **Purpose**: File upload and management interface
- **Responsibilities**:
  - Display uploaded files list with file names
  - Handle file selection via double-click interaction
  - Trigger upload modal and manage file removal
  - Provide visual feedback for active file selection

#### **Content.js - Main Content Display**
- **Purpose**: Primary data visualization and interaction area
- **Responsibilities**:
  - Render parsed log file sections in structured formats
  - Support dual-file side-by-side viewing with independent scrolling
  - Implement anomaly detection and error highlighting
  - Provide section navigation, font controls, and fullscreen mode

#### **UploadModal.js - File Upload Interface**
- **Purpose**: File upload with drag & drop functionality
- **Responsibilities**:
  - Handle drag and drop file uploads with visual feedback
  - Support traditional browse button file selection
  - Process ZIP files and individual log files
  - Display upload progress and error handling

#### **SectionFilter.js - Navigation & Filtering**
- **Purpose**: Section management and quick navigation
- **Responsibilities**:
  - Toggle section visibility with persistent state per file
  - Provide quick navigation to specific sections
  - Bulk expand/collapse controls for all sections
  - Cache filter preferences in browser storage

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
    ├── Sidebar.css      # File management panel
    ├── Content.css      # Main content area and tables
    ├── UploadModal.css  # File upload interface
    └── SectionFilter.css # Navigation sidebar
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

**Component-Scoped Classes**
- Each component prefixes its CSS classes with the component name
- Example: `.sidebar-container`, `.content-section`, `.upload-modal-backdrop`
- Prevents style conflicts and maintains clear ownership

**Base Styles (base.css)**
- CSS resets and normalization
- Base element styling (typography, forms, buttons)
- Default spacing and layout foundations

**Responsive Design**
- Mobile-first approach with progressive enhancement
- Flexible layouts using CSS Grid and Flexbox
- Breakpoints defined in themes.css for consistency

### Styling Patterns

#### **Table Styling (Content.css)**
- **Base tables**: Clean, minimal styling with hover effects
- **Critical rows**: Red background for anomaly highlighting
- **Disabled rows**: Grey background for inactive ports
- **Interactive elements**: Hover states and click feedback

#### **Modal Styling (UploadModal.css)**
- **Backdrop**: Semi-transparent overlay with blur effect
- **Drag states**: Visual feedback during file drag operations
- **Progress indicators**: Loading states and upload feedback

#### **Layout Styling (App.css)**
- **Grid system**: Three-column layout (sidebar, content, filter)
- **Responsive behavior**: Collapsible sidebars on smaller screens
- **Z-index management**: Proper layering for modals and overlays

## State Management

### React State Architecture

The application uses **React hooks** for state management with a combination of local component state and lifted state for shared data.

#### **Global State (App.js)**
```javascript
// File management
const [uploadedFiles, setUploadedFiles] = useState([]);
const [activeFiles, setActiveFiles] = useState([null, null]);

// UI state
const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
const [fontSize, setFontSize] = useState(14);

// Filter state
const [filterStates, setFilterStates] = useState({});
```

#### **Local Component State**
- **Content.js**: Section expansion, fullscreen mode, error detection
- **UploadModal.js**: File selection, upload progress, drag states
- **SectionFilter.js**: Filter visibility, navigation state

#### **Persistent State (Browser Storage)**
- **File cache**: Uploaded files stored in localStorage
- **Filter preferences**: Per-file section visibility states
- **User preferences**: Font size, UI settings

### Data Flow Patterns

#### **File Upload Flow**
1. **User Action**: Drag/drop or browse files in UploadModal
2. **API Call**: Send files to backend via `api.js`
3. **Response Processing**: Parse JSON response and validate data
4. **State Update**: Add files to `uploadedFiles` state
5. **Cache Storage**: Store files in browser localStorage
6. **UI Update**: Refresh file list and enable selection

#### **File Selection Flow**
1. **User Action**: Double-click file in Sidebar
2. **State Update**: Update `activeFiles` array
3. **Content Rendering**: Content.js receives new file data
4. **Section Processing**: Parse and render file sections
5. **Filter Application**: Apply cached filter states
6. **UI Update**: Display structured content with highlighting

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

**Features**:
- **Timeout handling**: 30-second timeout for large file uploads
- **Error handling**: Graceful degradation for network issues
- **Progress tracking**: Upload progress callbacks for UI feedback
- **Request formatting**: Proper multipart/form-data for file uploads

### File Caching (utils/fileCache.js)

**Purpose**: Browser localStorage management for persistent file storage.

```javascript
// Save files to browser cache
export const saveFilesToCache = (files) => {
  // Store files with metadata and timestamps
};

// Retrieve cached files on app load
export const loadFilesFromCache = () => {
  // Load and validate cached file data
};

// Clear cache when storage quota exceeded
export const clearOldFiles = (daysOld = 7) => {
  // Remove files older than specified days
};
```

**Features**:
- **Quota management**: Automatic cleanup when storage limits reached
- **Data validation**: Verify cached data integrity on load
- **Metadata tracking**: Store upload timestamps and file sizes
- **Error recovery**: Handle corrupted cache data gracefully

## Setup
For complete deployment instructions including Docker setup and troubleshooting, see [`../deployment.md`](../deployment.md)