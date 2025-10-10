import React, { useState } from 'react'
import { X, CheckCircle, Calendar, FileText } from 'lucide-react'
import { approveApp } from '../services/api'
import '../styles/ApprovalModal.css'

function ApprovalModal({ app, workspace, onSuccess, onCancel }) {
  const [formData, setFormData] = useState({
    justification: '',
    expirationDate: '',
    approvedBy: 'current-user' // TODO: Get from auth context
  })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!formData.justification.trim()) {
      setError('Justification is required')
      return
    }

    try {
      setSubmitting(true)
      setError(null)

      // Convert expiration date to UTC at 00:00:00
      let expirationDateUTC = null
      if (formData.expirationDate) {
        // Parse the date string (YYYY-MM-DD format)
        const [year, month, day] = formData.expirationDate.split('-').map(Number)
        // Create UTC date at midnight
        expirationDateUTC = new Date(Date.UTC(year, month - 1, day, 0, 0, 0, 0)).toISOString()
      }

      const approvalData = {
        resource_name: app.name,
        resource_id: app.resource_id,
        workspace_id: workspace.id,
        workspace_name: workspace.name,
        resource_creator: app.creator,
        approved_by: formData.approvedBy,
        justification: formData.justification,
        expiration_date: expirationDateUTC
      }

      await approveApp(approvalData)
      onSuccess()
    } catch (err) {
      setError('Failed to approve resource: ' + err.message)
      console.error('Error approving app:', err)
    } finally {
      setSubmitting(false)
    }
  }

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    setError(null)
  }

  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>
            <CheckCircle size={24} />
            Approve Resource
          </h2>
          <button className="close-button" onClick={onCancel}>
            <X size={24} />
          </button>
        </div>

        <div className="modal-body">
          <div className="app-summary">
            <h3>{app.name}</h3>
            <p>Workspace: {workspace.name}</p>
            <p>Creator: {app.creator}</p>
          </div>

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="justification">
                <FileText size={18} />
                Justification *
              </label>
              <textarea
                id="justification"
                value={formData.justification}
                onChange={(e) => handleChange('justification', e.target.value)}
                placeholder="Provide a reason for approving this app..."
                rows={4}
                required
                disabled={submitting}
              />
              <span className="field-hint">
                Explain why this app should be approved
              </span>
            </div>

            <div className="form-group">
              <label htmlFor="expirationDate">
                <Calendar size={18} />
                Expiration Date (Optional)
              </label>
              <input
                type="date"
                id="expirationDate"
                value={formData.expirationDate}
                onChange={(e) => handleChange('expirationDate', e.target.value)}
                disabled={submitting}
                min={new Date().toISOString().split('T')[0]}
              />
              <span className="field-hint">
                Expires at 00:00:00 UTC. Leave empty for no expiration.
              </span>
            </div>

            {error && (
              <div className="error-message">
                {error}
              </div>
            )}

            <div className="modal-actions">
              <button 
                type="button" 
                className="cancel-button"
                onClick={onCancel}
                disabled={submitting}
              >
                Cancel
              </button>
              <button 
                type="submit" 
                className="submit-button"
                disabled={submitting}
              >
                <CheckCircle size={18} />
                {submitting ? 'Approving...' : 'Approve'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

export default ApprovalModal


