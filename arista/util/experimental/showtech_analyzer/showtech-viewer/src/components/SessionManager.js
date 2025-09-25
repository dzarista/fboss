import React, { useState, useEffect } from 'react';
import {
  listSessions,
  createSession,
  getSession,
  updateSession
} from '../utils/sessionApi';
import { PencilIcon } from '../assets/icons/Icon';
import LoadingSpinner from './LoadingSpinner';
import '../styles/components/SessionManager.css';

const SessionManager = ({
  onSessionLoad,
  onClose,
  currentSessionId = null,
  onSessionRename = null
}) => {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState(null);
  const [hasMore, setHasMore] = useState(true);
  const [offset, setOffset] = useState(0);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newSessionName, setNewSessionName] = useState('');
  const [newSessionDescription, setNewSessionDescription] = useState('');
  const [creating, setCreating] = useState(false);
  const [renamingSessionId, setRenamingSessionId] = useState(null);
  const [renameSessionName, setRenameSessionName] = useState('');
  const [loadingSessionId, setLoadingSessionId] = useState(null);
  const [scrollTimeout, setScrollTimeout] = useState(null);

  const SESSIONS_PER_PAGE = 20;

  useEffect(() => {
    loadSessions();
  }, []);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (scrollTimeout) {
        clearTimeout(scrollTimeout);
      }
    };
  }, [scrollTimeout]);

  const loadSessions = async (reset = true) => {
    try {
      if (reset) {
        setLoading(true);
        setOffset(0);
        setSessions([]);
      } else {
        setLoadingMore(true);
      }
      setError(null);

      const currentOffset = reset ? 0 : offset;
      const response = await listSessions(SESSIONS_PER_PAGE, currentOffset);
      const newSessions = response.sessions || [];

      if (reset) {
        setSessions(newSessions);
      } else {
        setSessions(prev => [...prev, ...newSessions]);
      }

      // Update pagination state
      setOffset(currentOffset + newSessions.length);
      setHasMore(newSessions.length === SESSIONS_PER_PAGE);

    } catch (err) {
      setError(`Failed to load sessions: ${err.message}`);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  const loadMoreSessions = async () => {
    if (!hasMore || loadingMore) return;
    await loadSessions(false);
  };

  const handleScroll = (e) => {
    // Clear existing timeout
    if (scrollTimeout) {
      clearTimeout(scrollTimeout);
    }

    // Throttle scroll events
    const timeout = setTimeout(() => {
      const { scrollTop, scrollHeight, clientHeight } = e.target;
      // Trigger when within 10px of the bottom
      const isAtBottom = scrollTop + clientHeight >= scrollHeight - 10;

      if (isAtBottom && hasMore && !loadingMore) {
        loadMoreSessions();
      }
    }, 100); // 100ms throttle

    setScrollTimeout(timeout);
  };

  const handleSessionSelect = async (sessionId) => {
    if (!sessionId) return;

    try {
      setLoadingSessionId(sessionId);
      const sessionData = await getSession(sessionId);
      onSessionLoad(sessionData);
      onClose();
    } catch (err) {
      setError(`Failed to load session: ${err.message}`);
    } finally {
      setLoadingSessionId(null);
    }
  };



  const handleCreateSession = async (e) => {
    e.preventDefault();
    if (!newSessionName.trim()) return;

    try {
      setCreating(true);
      const session = await createSession({
        name: newSessionName.trim(),
        description: newSessionDescription.trim()
      });
      
      // Reset form
      setNewSessionName('');
      setNewSessionDescription('');
      setShowCreateForm(false);
      
      // Reload sessions to show the new one
      await loadSessions(true);
      
      // Optionally load the new session immediately
      handleSessionSelect(session.session_id);
    } catch (err) {
      setError(`Failed to create session: ${err.message}`);
    } finally {
      setCreating(false);
    }
  };





  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const handleRenameStart = (sessionId, currentName) => {
    setRenamingSessionId(sessionId);
    setRenameSessionName(currentName);
  };

  const handleRenameCancel = () => {
    setRenamingSessionId(null);
    setRenameSessionName('');
  };

  const handleRenameSave = async (sessionId) => {
    if (!renameSessionName.trim()) {
      return;
    }

    try {
      await updateSession(sessionId, { name: renameSessionName.trim() });

      // Update the session in the local state
      setSessions(prevSessions =>
        prevSessions.map(session =>
          session.session_id === sessionId
            ? { ...session, name: renameSessionName.trim() }
            : session
        )
      );

      // If this is the current active session, notify App.js to update its state
      if (sessionId === currentSessionId && onSessionRename) {
        onSessionRename(sessionId, renameSessionName.trim());
      }

      setRenamingSessionId(null);
      setRenameSessionName('');
    } catch (err) {
      setError(`Failed to rename session: ${err.message}`);
    }
  };



  return (
    <div className="session-manager-overlay">
      <div className="session-manager">
        <div className="session-manager-header">
          <h2>Browse Sessions</h2>
          <div className="header-actions">
            {!showCreateForm ? (
              <button
                className="create-session-button"
                onClick={() => setShowCreateForm(true)}
              >
                + New Session
              </button>
            ) : null}
            <button className="close-button" onClick={onClose}>×</button>
          </div>
        </div>

        {error && (
          <div className="error-message">
            {error}
            <button onClick={() => setError(null)}>×</button>
          </div>
        )}

          <div className="create-section">
            {showCreateForm ? (
              <form onSubmit={handleCreateSession} className="create-session-form">
                <div className="form-inputs">
                  <input
                    type="text"
                    placeholder="Session name"
                    value={newSessionName}
                    onChange={(e) => setNewSessionName(e.target.value)}
                    required
                    autoFocus
                  />
                  <input
                    type="text"
                    placeholder="Description (optional)"
                    value={newSessionDescription}
                    onChange={(e) => setNewSessionDescription(e.target.value)}
                  />
                </div>
                <div className="form-buttons">
                  <button type="submit" className="create-button" disabled={creating || !newSessionName.trim()}>
                    {creating ? 'Creating...' : 'Create'}
                  </button>
                  <button
                    type="button"
                    className="cancel-button"
                    onClick={() => {
                      setShowCreateForm(false);
                      setNewSessionName('');
                      setNewSessionDescription('');
                    }}
                  >
                    Cancel
                  </button>
                </div>
              </form>
            ) : null}
        </div>

        <div className="session-divider"></div>

        <div className="sessions-list" onScroll={handleScroll}>
          {loadingSessionId && (
            <div className="session-loading-overlay">
              <LoadingSpinner message="Loading session..." size="medium" />
            </div>
          )}
          {loading && sessions.length === 0 ? (
            <div className="loading">Loading sessions...</div>
          ) : sessions.length === 0 ? (
            <div className="no-sessions">
              No sessions found. Create your first session!
            </div>
          ) : (
            <>
              {sessions.map((session) => (
                <div
                  key={session.session_id}
                  className={`session-item ${session.session_id === currentSessionId ? 'current' : ''}`}
                >
                  <div className="session-info">
                    {renamingSessionId === session.session_id ? (
                      <div className="rename-input-container">
                        <input
                          type="text"
                          value={renameSessionName}
                          onChange={(e) => setRenameSessionName(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              handleRenameSave(session.session_id);
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
                            onClick={() => handleRenameSave(session.session_id)}
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
                      <div className="session-name">
                        <span className="session-name-text">
                          {session.name}
                        </span>
                      </div>
                    )}
                    {session.description && (
                      <div className="session-description">{session.description}</div>
                    )}
                    <div className="session-meta">
                      <span className="file-count">{session.file_count} files</span>
                      <span className="created-date">Created: {formatDate(session.created_at)}</span>
                      {session.last_accessed !== session.created_at && (
                        <span className="accessed-date">Last accessed: {formatDate(session.last_accessed)}</span>
                      )}
                    </div>
                  </div>
                  <div className="session-actions">
                    <button
                      className="session-rename-button"
                      onClick={() => handleRenameStart(session.session_id, session.name)}
                      title="Rename Session"
                    >
                      <PencilIcon />
                    </button>
                    {session.session_id !== currentSessionId && (
                      <button
                        className={`load-button ${loadingSessionId === session.session_id ? 'loading' : ''}`}
                        onClick={() => handleSessionSelect(session.session_id)}
                        disabled={loadingSessionId === session.session_id}
                      >
                        {loadingSessionId === session.session_id ? (
                          <div className="button-loading">
                            <div className="button-spinner"></div>
                            Loading...
                          </div>
                        ) : (
                          'Load'
                        )}
                      </button>
                    )}
                  </div>
                </div>
              ))}
              {loadingMore && (
                <div className="loading-more">
                  <LoadingSpinner message="Loading more sessions..." size="small" />
                </div>
              )}
            </>
          )}
        </div>


      </div>
    </div>
  );
};

export default SessionManager;
