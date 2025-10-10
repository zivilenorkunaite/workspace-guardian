import React, { useState } from 'react'
import AppCard from './AppCard'
import { Package, Server, Network, Database, ChevronDown, ChevronUp } from 'lucide-react'
import '../styles/AppList.css'

function AppList({ apps, onApprove, onRevoke, onReload }) {
  const [appsExpanded, setAppsExpanded] = useState(true)
  const [endpointsExpanded, setEndpointsExpanded] = useState(true)
  const [vectorSearchExpanded, setVectorSearchExpanded] = useState(true)
  const [lakehousePostgresExpanded, setLakehousePostgresExpanded] = useState(true)

  if (apps.length === 0) {
    return (
      <div className="empty-state">
        <Package size={64} />
        <h2>No Resources Found</h2>
        <p>There are no Databricks resources in this workspace.</p>
      </div>
    )
  }

  // Split apps by type
  const databricksApps = apps.filter(app => app.type === 'app')
  const servingEndpoints = apps.filter(app => app.type === 'serving_endpoint')
  const vectorSearch = apps.filter(app => app.type === 'vector_search')
  const lakehousePostgres = apps.filter(app => app.type === 'postgres')

  return (
    <div className="app-list-container">
      {/* Databricks Apps Section */}
      {databricksApps.length > 0 && (
        <div className="app-section">
          <div 
            className="section-header clickable"
            onClick={() => setAppsExpanded(!appsExpanded)}
            role="button"
            tabIndex={0}
            onKeyPress={(e) => e.key === 'Enter' && setAppsExpanded(!appsExpanded)}
          >
            <Package size={24} />
            <h2>Databricks Apps</h2>
            <span className="section-count">{databricksApps.length}</span>
            {appsExpanded ? <ChevronUp size={24} /> : <ChevronDown size={24} />}
          </div>
          <div className={`app-list-wrapper ${appsExpanded ? 'expanded' : 'collapsed'}`}>
            <div className="app-list">
              {databricksApps.map(app => (
                <AppCard 
                  key={`${app.resource_id}-${app.workspace_id}`}
                  app={app}
                  onApprove={onApprove}
                  onRevoke={onRevoke}
                />
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Serving Endpoints Section */}
      {servingEndpoints.length > 0 && (
        <div className="app-section">
          <div 
            className="section-header clickable"
            onClick={() => setEndpointsExpanded(!endpointsExpanded)}
            role="button"
            tabIndex={0}
            onKeyPress={(e) => e.key === 'Enter' && setEndpointsExpanded(!endpointsExpanded)}
          >
            <Server size={24} />
            <h2>Model Serving Endpoints</h2>
            <span className="section-count">{servingEndpoints.length}</span>
            {endpointsExpanded ? <ChevronUp size={24} /> : <ChevronDown size={24} />}
          </div>
          <div className={`app-list-wrapper ${endpointsExpanded ? 'expanded' : 'collapsed'}`}>
            <div className="app-list">
              {servingEndpoints.map(app => (
                <AppCard 
                  key={`${app.resource_id}-${app.workspace_id}`}
                  app={app}
                  onApprove={onApprove}
                  onRevoke={onRevoke}
                />
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Vector Search Section */}
      {vectorSearch.length > 0 && (
        <div className="app-section">
          <div 
            className="section-header clickable"
            onClick={() => setVectorSearchExpanded(!vectorSearchExpanded)}
            role="button"
            tabIndex={0}
            onKeyPress={(e) => e.key === 'Enter' && setVectorSearchExpanded(!vectorSearchExpanded)}
          >
            <Network size={24} />
            <h2>Vector Search Endpoints</h2>
            <span className="section-count">{vectorSearch.length}</span>
            {vectorSearchExpanded ? <ChevronUp size={24} /> : <ChevronDown size={24} />}
          </div>
          <div className={`app-list-wrapper ${vectorSearchExpanded ? 'expanded' : 'collapsed'}`}>
            <div className="app-list">
              {vectorSearch.map(app => (
                <AppCard 
                  key={`${app.resource_id}-${app.workspace_id}`}
                  app={app}
                  onApprove={onApprove}
                  onRevoke={onRevoke}
                />
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Lakehouse Postgres Section */}
      {lakehousePostgres.length > 0 && (
        <div className="app-section">
          <div 
            className="section-header clickable"
            onClick={() => setLakehousePostgresExpanded(!lakehousePostgresExpanded)}
            role="button"
            tabIndex={0}
            onKeyPress={(e) => e.key === 'Enter' && setLakehousePostgresExpanded(!lakehousePostgresExpanded)}
          >
            <Database size={24} />
            <h2>Lakehouse Postgres</h2>
            <span className="section-count">{lakehousePostgres.length}</span>
            {lakehousePostgresExpanded ? <ChevronUp size={24} /> : <ChevronDown size={24} />}
          </div>
          <div className={`app-list-wrapper ${lakehousePostgresExpanded ? 'expanded' : 'collapsed'}`}>
            <div className="app-list">
              {lakehousePostgres.map(app => (
                <AppCard 
                  key={`${app.resource_id}-${app.workspace_id}`}
                  app={app}
                  onApprove={onApprove}
                  onRevoke={onRevoke}
                />
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default AppList


