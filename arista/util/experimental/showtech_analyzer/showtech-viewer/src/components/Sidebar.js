import { useState } from 'react';
import { UploadIcon, PencilIcon } from '../assets/icons/Icon';
import LoadingSpinner from './LoadingSpinner';


export default function Sidebar({
  logs,
  onSelect,
  onUploadClick,
  onRemoveFile,
  statusClass,
  statusTitle,
  version,
  currentSession,
  onSessionManagerClick,
  onSessionRename,
  loadingSession,
}) {
  const [collapsed, setCollapsed] = useState(false);
  const [isRenaming, setIsRenaming] = useState(false);
  const [renameValue, setRenameValue] = useState('');

  const handleRenameStart = () => {
    if (currentSession) {
      setIsRenaming(true);
      setRenameValue(currentSession.name);
    }
  };

  const handleRenameCancel = () => {
    setIsRenaming(false);
    setRenameValue('');
  };

  const handleRenameSave = () => {
    if (renameValue.trim() && onSessionRename) {
      onSessionRename(currentSession, renameValue.trim());
      setIsRenaming(false);
      setRenameValue('');
    }
  };

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

          {/* Session Management Section */}
          <div className="session-section">
            {currentSession ? (
              <div className="current-session">
                <div className="session-header">
                  <div className="session-label">Active Session:</div>
                  <button
                    className="session-manager-button"
                    onClick={onSessionManagerClick}
                    title="Manage Sessions"
                  >
                    Sessions
                  </button>
                </div>
                <div className="session-name-container">
                  {isRenaming ? (
                    <div className="rename-input-container">
                      <input
                        type="text"
                        value={renameValue}
                        onChange={(e) => setRenameValue(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            handleRenameSave();
                          } else if (e.key === 'Escape') {
                            handleRenameCancel();
                          }
                        }}
                        className="rename-input"
                        autoFocus
                      />
                      <div className="rename-buttons">
                        <button
                          className="rename-save-button"
                          onClick={handleRenameSave}
                        >
                          ✓
                        </button>
                        <button
                          className="rename-cancel-button"
                          onClick={handleRenameCancel}
                        >
                          ✕
                        </button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <div className="session-name" title={currentSession.name}>
                        {currentSession.name}
                      </div>
                      <button
                        className="session-rename-button"
                        onClick={handleRenameStart}
                        title="Rename Session"
                      >
                        <PencilIcon />
                      </button>
                    </>
                  )}
                </div>
              </div>
            ) : (
              <button
                className="session-manager-button primary"
                onClick={onSessionManagerClick}
                title="Choose or Create Session"
              >
                Choose Session
              </button>
            )}
          </div>

          <div className="sidebar-title-row">
            <div className="title-spacer"></div>
            <h2 className="sidebar-title">Files</h2>
            <button
              className="upload-icon-button"
              onClick={onUploadClick}
              title={currentSession ? "Add Files to Session" : "Upload Files (will create new session)"}
            >
              <UploadIcon />
            </button>
          </div>
          <div className="title-divider"></div>

          <div className="sidebar-files">
            {loadingSession ? (
              <div className="files-loading">
                <LoadingSpinner message="Loading Session..." size="small" />
              </div>
            ) : logs.length === 0 ? (
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
                      disabled={log.isRemoving}
                      aria-label={`Remove ${log.name}`}
                    >
                      {log.isRemoving ? '...' : '×'}
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
