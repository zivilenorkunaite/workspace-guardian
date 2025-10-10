import React from 'react'
import { 
  Package, CheckCircle, XCircle, Clock, 
  User, Calendar, Shield, ShieldOff, AlertTriangle, Server, Network, Database, FileText 
} from 'lucide-react'
import { format, isPast, isValid, parseISO } from 'date-fns'
import '../styles/AppCard.css'

function AppCard({ app, onApprove, onRevoke }) {
  
  // Helper to safely format dates
  const safeFormatDate = (dateValue, formatString = 'MMM dd, yyyy') => {
    if (!dateValue) return null
    try {
      // Try to parse the date - handle both ISO strings and Date objects
      const date = typeof dateValue === 'string' ? parseISO(dateValue) : new Date(dateValue)
      if (isValid(date)) {
        return format(date, formatString)
      }
      return null
    } catch (error) {
      console.warn('Invalid date value:', dateValue, error)
      return null
    }
  }

  // Helper to safely check if date is past
  const safeIsPast = (dateValue) => {
    if (!dateValue) return false
    try {
      const date = typeof dateValue === 'string' ? parseISO(dateValue) : new Date(dateValue)
      return isValid(date) ? isPast(date) : false
    } catch (error) {
      return false
    }
  }

  const getStateClass = () => {
    const state = app.state?.toUpperCase()
    if (state === 'RUNNING' || state === 'READY' || state === 'ACTIVE' || state === 'ONLINE') return 'state-running'
    if (state === 'STOPPED' || state === 'READ_ONLY') return 'state-stopped'
    return 'state-unknown'
  }

  const getIcon = () => {
    switch (app.type) {
      case 'serving_endpoint':
        return <Server size={24} />
      case 'vector_search':
        return <Network size={24} />
      case 'lakehouse_postgres':
        return <Database size={24} />
      default:
        return <Package size={24} />
    }
  }

  const getTypeLabel = () => {
    switch (app.type) {
      case 'serving_endpoint':
        return 'Model Serving Endpoint'
      case 'vector_search':
        return 'Vector Search Endpoint'
      case 'lakehouse_postgres':
        return 'Lakehouse Postgres'
      default:
        return 'Databricks App'
    }
  }

  const isExpired = app.expiration_date && 
                    safeIsPast(app.expiration_date)

  const showApprovalWarning = isExpired || 
                               (app.expiration_date && 
                                !isExpired && 
                                (() => {
                                  try {
                                    const expDate = typeof app.expiration_date === 'string' 
                                      ? parseISO(app.expiration_date) 
                                      : new Date(app.expiration_date)
                                    return isValid(expDate) && (expDate - new Date() < 7 * 24 * 60 * 60 * 1000)
                                  } catch {
                                    return false
                                  }
                                })())

  return (
    <div className={`app-card ${app.is_approved ? 'approved' : 'unapproved'}`}>
      <div className="app-card-header">
        <div className="app-title">
          {getIcon()}
          <h3>{app.name}</h3>
          <span className="app-type-badge">
            {getTypeLabel()}
          </span>
        </div>
        <div className={`app-state ${getStateClass()}`}>
          {app.state}
        </div>
      </div>

      <div className="app-card-body">
        <div className="app-info">
          <div className="info-item">
            <User size={16} />
            <span>Creator: {app.creator}</span>
          </div>
          {app.created_at && safeFormatDate(app.created_at) && (
            <div className="info-item">
              <Calendar size={16} />
              <span>Created: {safeFormatDate(app.created_at)}</span>
            </div>
          )}
          {app.description && (
            <div className="info-item description-item">
              <FileText size={16} />
              <span>{app.description}</span>
            </div>
          )}
        </div>

        {app.is_approved ? (
          <div className="approval-details">
            <div className="approval-header">
              <Shield size={18} className="approval-icon" />
              <span className="approval-label">Approved</span>
            </div>
            
            <div className="approval-info">
              {app.approved_by && (
                <div className="info-item">
                  <User size={14} />
                  <span>By: {app.approved_by}</span>
                </div>
              )}
              {safeFormatDate(app.approval_date) && (
                <div className="info-item">
                  <Calendar size={14} />
                  <span>On: {safeFormatDate(app.approval_date)}</span>
                </div>
              )}
              {app.expiration_date && safeFormatDate(app.expiration_date, 'MMM dd, yyyy HH:mm') && (
                <div className={`info-item ${isExpired ? 'expired' : ''}`}>
                  <Clock size={14} />
                  <span>
                    Expires: {safeFormatDate(app.expiration_date, 'MMM dd, yyyy HH:mm')} (Local)
                    {isExpired && ' (EXPIRED)'}
                  </span>
                </div>
              )}
            </div>

            {showApprovalWarning && (
              <div className="approval-warning">
                <AlertTriangle size={16} />
                <span>
                  {isExpired 
                    ? 'This approval has expired' 
                    : 'This approval expires soon'}
                </span>
              </div>
            )}

            {app.justification && (
              <div className="approval-justification">
                <strong>Justification:</strong>
                <p>{app.justification}</p>
              </div>
            )}

            <button 
              className="revoke-button"
              onClick={() => onRevoke(app)}
            >
              <ShieldOff size={16} />
              Revoke Approval
            </button>
          </div>
        ) : (
          <div className="unapproved-section">
            <div className="unapproved-header">
              <XCircle size={18} className="unapproved-icon" />
              <span>Not Approved</span>
            </div>
            <button 
              className="approve-button"
              onClick={() => onApprove(app)}
            >
              <CheckCircle size={16} />
              Approve
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default AppCard


