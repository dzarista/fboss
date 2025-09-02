import { useState } from 'react';
import { UploadIcon } from '../assets/icons/Icon';


export default function Sidebar({
  logs,
  onSelect,
  onUploadClick,
  onRemoveFile,
  statusClass,
  statusTitle,
  version,
}) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className={`sidebar${collapsed ? ' collapsed' : ''}`}>
      {/* collapse handle */}
      <div
        className="sidebar-collapse-handle"
        onClick={() => setCollapsed(c => !c)}
        title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
      />

      {/* all of this hides when collapsed */}
      {!collapsed && (
        <>
          <div className="sidebar-header">
            <h1 className="app-title">Showtech Viewer</h1>
            <div className={`status-indicator ${statusClass}`} title={statusTitle}></div>
            <div className="header-version" title={`Version ${version}`}>
              {version}
            </div>
          </div>

          <button
            className="upload-icon-button"
            onClick={onUploadClick}
            title="Upload Files"
          >
            <UploadIcon />
          </button>

          <div className="sidebar-title-row">
            <h2 className="sidebar-title">Files</h2>
          </div>

          <div className="sidebar-files">
            {logs.length === 0 ? (
              <p className="placeholder-text">No files uploaded</p>
            ) : (
              logs.map((log, idx) => {
                const hostname = log.metadata?.hostname;
                return (
                  <div
                    key={idx}
                    className="file-tab"
                  >
                    <div 
                      className="sidebar-file-info"
                      onDoubleClick={() => onSelect(idx)}
                    >
                      <span
                        className="file-name"
                        onDoubleClick={() => onSelect(idx)}
                      >
                        {log.name}
                      </span>
                      {hostname && (
                        <span className="file-hostname">
                          {hostname}
                        </span>
                      )}
                    </div>
                    <button
                      className="remove-file-button"
                      onClick={() => onRemoveFile(idx)}
                      aria-label={`Remove ${log.name}`}
                    >
                      &times;
                    </button>
                  </div>
                );
              })
            )}
          </div>
        </>
      )}
    </div>
  );
}
