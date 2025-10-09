import React from 'react'
import { Package, Server, CheckCircle, AlertCircle, Activity, TrendingUp, Network, Database } from 'lucide-react'
import '../styles/StatsBar.css'

function StatsBar({ appsStats, endpointsStats, vectorSearchStats, lakehousePostgresStats, workspaceName }) {
  const totalAll = appsStats.total + endpointsStats.total + vectorSearchStats.total + lakehousePostgresStats.total
  const approvedAll = appsStats.approved + endpointsStats.approved + vectorSearchStats.approved + lakehousePostgresStats.approved
  const overallRate = totalAll > 0 ? ((approvedAll / totalAll) * 100).toFixed(1) : 0

  return (
    <div className="stats-bar">
      {/* Overall Stats - Moved to Front */}
      <div className="stats-section stats-overall">
        <div className="stats-section-header">
          <TrendingUp size={16} />
          <span>Overall Resources</span>
        </div>
        <div className="stats-section-content">
          <div className="stat-item">
            <div className="stat-value">{totalAll}</div>
            <div className="stat-label">Total</div>
          </div>
          <div className="stat-item stat-approved">
            <div className="stat-value">{approvedAll}</div>
            <div className="stat-label">Approved</div>
          </div>
          <div className="stat-item">
            <div className="stat-value">{overallRate}%</div>
            <div className="stat-label">Rate</div>
          </div>
        </div>
      </div>

      {/* Databricks Apps Section */}
      <div className="stats-section">
        <div className="stats-section-header">
          <Package size={16} />
          <span>Databricks Apps</span>
        </div>
        <div className="stats-section-content">
          <div className="stat-item">
            <Activity size={16} className="stat-icon" />
            <div className="stat-value">{appsStats.total}</div>
            <div className="stat-label">Total</div>
          </div>
          <div className="stat-item stat-approved">
            <CheckCircle size={16} className="stat-icon" />
            <div className="stat-value">{appsStats.approved}</div>
            <div className="stat-label">Approved</div>
          </div>
          <div className="stat-item stat-unapproved">
            <AlertCircle size={16} className="stat-icon" />
            <div className="stat-value">{appsStats.total - appsStats.approved}</div>
            <div className="stat-label">Unapproved</div>
          </div>
        </div>
      </div>

      {/* Serving Endpoints Section */}
      <div className="stats-section">
        <div className="stats-section-header">
          <Server size={16} />
          <span>Model Serving</span>
        </div>
        <div className="stats-section-content">
          <div className="stat-item">
            <Activity size={16} className="stat-icon" />
            <div className="stat-value">{endpointsStats.total}</div>
            <div className="stat-label">Total</div>
          </div>
          <div className="stat-item stat-approved">
            <CheckCircle size={16} className="stat-icon" />
            <div className="stat-value">{endpointsStats.approved}</div>
            <div className="stat-label">Approved</div>
          </div>
          <div className="stat-item stat-unapproved">
            <AlertCircle size={16} className="stat-icon" />
            <div className="stat-value">{endpointsStats.total - endpointsStats.approved}</div>
            <div className="stat-label">Unapproved</div>
          </div>
        </div>
      </div>

      {/* Vector Search Section */}
      <div className="stats-section">
        <div className="stats-section-header">
          <Network size={16} />
          <span>Vector Search</span>
        </div>
        <div className="stats-section-content">
          <div className="stat-item">
            <Activity size={16} className="stat-icon" />
            <div className="stat-value">{vectorSearchStats.total}</div>
            <div className="stat-label">Total</div>
          </div>
          <div className="stat-item stat-approved">
            <CheckCircle size={16} className="stat-icon" />
            <div className="stat-value">{vectorSearchStats.approved}</div>
            <div className="stat-label">Approved</div>
          </div>
          <div className="stat-item stat-unapproved">
            <AlertCircle size={16} className="stat-icon" />
            <div className="stat-value">{vectorSearchStats.total - vectorSearchStats.approved}</div>
            <div className="stat-label">Unapproved</div>
          </div>
        </div>
      </div>

      {/* Lakehouse Postgres Section */}
      <div className="stats-section">
        <div className="stats-section-header">
          <Database size={16} />
          <span>Lakehouse Postgres</span>
        </div>
        <div className="stats-section-content">
          <div className="stat-item">
            <Activity size={16} className="stat-icon" />
            <div className="stat-value">{lakehousePostgresStats.total}</div>
            <div className="stat-label">Total</div>
          </div>
          <div className="stat-item stat-approved">
            <CheckCircle size={16} className="stat-icon" />
            <div className="stat-value">{lakehousePostgresStats.approved}</div>
            <div className="stat-label">Approved</div>
          </div>
          <div className="stat-item stat-unapproved">
            <AlertCircle size={16} className="stat-icon" />
            <div className="stat-value">{lakehousePostgresStats.total - lakehousePostgresStats.approved}</div>
            <div className="stat-label">Unapproved</div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default StatsBar


