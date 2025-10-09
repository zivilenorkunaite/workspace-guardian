import React, { useState, useEffect } from 'react'
import { 
  RefreshCw, Shield, ShieldOff, CheckCircle, 
  XCircle, AlertTriangle, Activity 
} from 'lucide-react'
import WorkspaceSelector from './components/WorkspaceSelector'
import AppList from './components/AppList'
import ApprovalModal from './components/ApprovalModal'
import RevokeModal from './components/RevokeModal'
import StatsBar from './components/StatsBar'
import Settings from './components/Settings'
import { fetchWorkspaces, fetchApps, refreshApps } from './services/api'
import './styles/App.css'

function App() {
  const [workspaces, setWorkspaces] = useState([])
  const [selectedWorkspace, setSelectedWorkspace] = useState(null)
  const [apps, setApps] = useState([])
  const [stats, setStats] = useState({ 
    apps: { total: 0, approved: 0 },
    endpoints: { total: 0, approved: 0 },
    vectorSearch: { total: 0, approved: 0 },
    lakehousePostgres: { total: 0, approved: 0 }
  })
  const [loading, setLoading] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState(null)
  const [showApprovalModal, setShowApprovalModal] = useState(false)
  const [showRevokeModal, setShowRevokeModal] = useState(false)
  const [selectedApp, setSelectedApp] = useState(null)

  // Load workspaces on mount
  useEffect(() => {
    loadWorkspaces()
  }, [])

  // Load apps when workspace changes
  useEffect(() => {
    if (selectedWorkspace) {
      loadApps(selectedWorkspace.workspace_id)
    }
  }, [selectedWorkspace])

  const loadWorkspaces = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await fetchWorkspaces()
      setWorkspaces(data)
      
      // Auto-select first workspace
      if (data.length > 0) {
        setSelectedWorkspace(data[0])
      }
    } catch (err) {
      setError('Failed to load workspaces: ' + err.message)
      console.error('Error loading workspaces:', err)
    } finally {
      setLoading(false)
    }
  }

  const loadApps = async (workspaceId) => {
    try {
      setLoading(true)
      setError(null)
      const data = await fetchApps(workspaceId)
      setApps(data.apps)
      
      // Split stats by type
      const databricksApps = data.apps.filter(app => app.type === 'app')
      const servingEndpoints = data.apps.filter(app => app.type === 'serving_endpoint')
      const vectorSearch = data.apps.filter(app => app.type === 'vector_search')
      const lakehousePostgres = data.apps.filter(app => app.type === 'lakehouse_postgres')
      
      setStats({
        apps: {
          total: databricksApps.length,
          approved: databricksApps.filter(app => app.is_approved).length
        },
        endpoints: {
          total: servingEndpoints.length,
          approved: servingEndpoints.filter(app => app.is_approved).length
        },
        vectorSearch: {
          total: vectorSearch.length,
          approved: vectorSearch.filter(app => app.is_approved).length
        },
        lakehousePostgres: {
          total: lakehousePostgres.length,
          approved: lakehousePostgres.filter(app => app.is_approved).length
        }
      })
    } catch (err) {
      setError('Failed to load apps: ' + err.message)
      console.error('Error loading apps:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = async () => {
    if (!selectedWorkspace) return
    
    try {
      setRefreshing(true)
      setError(null)
      await refreshApps(selectedWorkspace.workspace_id)
      await loadApps(selectedWorkspace.workspace_id)
    } catch (err) {
      setError('Failed to refresh apps: ' + err.message)
      console.error('Error refreshing apps:', err)
    } finally {
      setRefreshing(false)
    }
  }

  const handleApprove = (app) => {
    setSelectedApp(app)
    setShowApprovalModal(true)
  }

  const handleRevoke = (app) => {
    setSelectedApp(app)
    setShowRevokeModal(true)
  }

  const handleApprovalSuccess = () => {
    setShowApprovalModal(false)
    setSelectedApp(null)
    // Reload apps to get updated approval status
    if (selectedWorkspace) {
      loadApps(selectedWorkspace.workspace_id)
    }
  }

  const handleApprovalCancel = () => {
    setShowApprovalModal(false)
    setSelectedApp(null)
  }

  const handleRevokeSuccess = () => {
    setShowRevokeModal(false)
    setSelectedApp(null)
    // Reload apps to get updated approval status
    if (selectedWorkspace) {
      loadApps(selectedWorkspace.workspace_id)
    }
  }

  const handleRevokeCancel = () => {
    setShowRevokeModal(false)
    setSelectedApp(null)
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <div className="header-top">
            <div className="header-title">
              <Shield className="header-icon" size={32} />
              <h1>Workspace Guardian</h1>
            </div>
            <Settings />
          </div>
          <div className="header-subtitle">
            Databricks Resources Monitor & Approval Management
          </div>
        </div>
      </header>

      <main className="app-main">
        <div className="controls-bar">
          <WorkspaceSelector
            workspaces={workspaces}
            selectedWorkspace={selectedWorkspace}
            onSelect={setSelectedWorkspace}
            disabled={loading}
          />
          
          <button 
            className="refresh-button"
            onClick={handleRefresh}
            disabled={!selectedWorkspace || refreshing || loading}
          >
            <RefreshCw 
              size={18} 
              className={refreshing ? 'spinning' : ''} 
            />
            {refreshing ? 'Refreshing...' : 'Refresh Apps'}
          </button>
        </div>

        {error && (
          <div className="error-banner">
            <AlertTriangle size={20} />
            <span>{error}</span>
            <button onClick={() => setError(null)}>Dismiss</button>
          </div>
        )}

        {selectedWorkspace && (
          <StatsBar 
            appsStats={stats.apps}
            endpointsStats={stats.endpoints}
            vectorSearchStats={stats.vectorSearch}
            lakehousePostgresStats={stats.lakehousePostgres}
            workspaceName={selectedWorkspace.workspace_name}
          />
        )}

        {loading && !refreshing ? (
          <div className="loading-container">
            <Activity className="spinning" size={48} />
            <p>Loading apps...</p>
          </div>
        ) : (
          <AppList 
            apps={apps}
            onApprove={handleApprove}
            onRevoke={handleRevoke}
            onReload={() => selectedWorkspace && loadApps(selectedWorkspace.workspace_id)}
          />
        )}
      </main>

      {showApprovalModal && selectedApp && (
        <ApprovalModal
          app={selectedApp}
          workspace={selectedWorkspace}
          onSuccess={handleApprovalSuccess}
          onCancel={handleApprovalCancel}
        />
      )}

      {showRevokeModal && selectedApp && (
        <RevokeModal
          app={selectedApp}
          onSuccess={handleRevokeSuccess}
          onCancel={handleRevokeCancel}
        />
      )}
    </div>
  )
}

export default App


