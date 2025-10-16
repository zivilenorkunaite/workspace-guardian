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
  console.log('📱 [App] Component initializing...')
  
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
    console.log('🔄 [App] Mount effect triggered - loading workspaces...')
    loadWorkspaces()
  }, [])

  // Load apps when workspace changes
  useEffect(() => {
    if (selectedWorkspace) {
      loadApps(selectedWorkspace.id)
    }
  }, [selectedWorkspace])

  const loadWorkspaces = async () => {
    console.log('🔄 [App] loadWorkspaces() called')
    try {
      setLoading(true)
      setError(null)
      console.log('📡 [App] Fetching workspaces from API...')
      const data = await fetchWorkspaces()
      console.log('✅ [App] Workspaces loaded:', data)
      setWorkspaces(data)
      
      // Auto-select first workspace
      if (data.length > 0) {
        console.log('🎯 [App] Auto-selecting workspace:', data[0])
        setSelectedWorkspace(data[0])
      } else {
        console.warn('⚠️  [App] No workspaces available')
      }
    } catch (err) {
      const errorMsg = 'Failed to load workspaces: ' + err.message
      console.error('❌ [App] Error loading workspaces:', err)
      console.error('❌ [App] Error details:', { message: err.message, stack: err.stack })
      setError(errorMsg)
    } finally {
      setLoading(false)
      console.log('✅ [App] loadWorkspaces() complete')
    }
  }

  const loadApps = async (workspaceId) => {
    console.log('🔄 [App] loadApps() called with workspaceId:', workspaceId)
    try {
      setLoading(true)
      setError(null)
      console.log('📡 [App] Fetching apps from API...')
      const data = await fetchApps(workspaceId)
      console.log('✅ [App] API response:', data)
      
      // API returns 'resources' field, not 'apps'
      const resources = data.resources || []
      console.log(`📊 [App] Found ${resources.length} resources`)
      setApps(resources)
      
      // Split stats by type
      const databricksApps = resources.filter(app => app.type === 'app')
      const servingEndpoints = resources.filter(app => app.type === 'serving_endpoint')
      const vectorSearch = resources.filter(app => app.type === 'vector_search')
      const lakehousePostgres = resources.filter(app => app.type === 'postgres')
      
      console.log('📊 [App] Resource breakdown:', {
        apps: databricksApps.length,
        endpoints: servingEndpoints.length,
        vectorSearch: vectorSearch.length,
        postgres: lakehousePostgres.length
      })
      
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
      const errorMsg = 'Failed to load apps: ' + err.message
      console.error('❌ [App] Error loading apps:', err)
      console.error('❌ [App] Error details:', { message: err.message, stack: err.stack })
      setError(errorMsg)
    } finally {
      setLoading(false)
      console.log('✅ [App] loadApps() complete')
    }
  }

  const handleRefresh = async () => {
    if (!selectedWorkspace) return
    
    try {
      setRefreshing(true)
      setError(null)
      await refreshApps(selectedWorkspace.id)
      await loadApps(selectedWorkspace.id)
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
      loadApps(selectedWorkspace.id)
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
      loadApps(selectedWorkspace.id)
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
            workspaceName={selectedWorkspace.name}
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
            onReload={() => selectedWorkspace && loadApps(selectedWorkspace.id)}
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


