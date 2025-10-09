import React, { useState } from 'react'
import { X, ShieldOff, FileText } from 'lucide-react'
import { revokeApproval } from '../services/api'
import '../styles/RevokeModal.css'

function RevokeModal({ app, onSuccess, onCancel }) {
  const [formData, setFormData] = useState({
    revokedReason: '',
    revokedBy: 'current-user' // TODO: Get from auth context
  })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!formData.revokedReason.trim()) {
      setError('Reason for revocation is required')
      return
    }

    try {
      setSubmitting(true)
      setError(null)

      const revokeData = {
        app_name: app.name,
        app_id: app.app_id,
        workspace_id: app.workspace_id,
        revoked_by: formData.revokedBy,
        revoked_reason: formData.revokedReason
      }

      await revokeApproval(revokeData)
      onSuccess()
    } catch (err) {
      setError('Failed to revoke approval: ' + err.message)
      console.error('Error revoking approval:', err)
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
      <div className="modal-content revoke-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header revoke-header">
          <h2>
            <ShieldOff size={24} />
            Revoke Approval
          </h2>
          <button className="close-button" onClick={onCancel}>
            <X size={24} />
          </button>
        </div>

        <div className="modal-body">
          <div className="app-summary revoke-warning">
            <h3>{app.name}</h3>
            <p className="warning-text">
              You are about to revoke approval for this {app.type === 'serving_endpoint' ? 'endpoint' : 'app'}. 
              This action will mark it as unapproved.
            </p>
          </div>

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="revokedReason">
                <FileText size={18} />
                Reason for Revocation *
              </label>
              <textarea
                id="revokedReason"
                value={formData.revokedReason}
                onChange={(e) => handleChange('revokedReason', e.target.value)}
                placeholder="Explain why this approval is being revoked..."
                rows={4}
                required
                disabled={submitting}
                autoFocus
              />
              <span className="field-hint">
                This reason will be stored in the approval history
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
                className="revoke-submit-button"
                disabled={submitting}
              >
                <ShieldOff size={16} />
                {submitting ? 'Revoking...' : 'Revoke Approval'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

export default RevokeModal



