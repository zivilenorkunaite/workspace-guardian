import React from 'react'
import { Database } from 'lucide-react'
import '../styles/WorkspaceSelector.css'

function WorkspaceSelector({ workspaces, selectedWorkspace, onSelect, disabled }) {
  return (
    <div className="workspace-selector">
      <label htmlFor="workspace-select">
        <Database size={18} />
        <span>Workspace:</span>
      </label>
      <select
        id="workspace-select"
        value={selectedWorkspace?.workspace_id || ''}
        onChange={(e) => {
          const workspace = workspaces.find(w => w.workspace_id === e.target.value)
          onSelect(workspace)
        }}
        disabled={disabled || workspaces.length === 0}
      >
        {workspaces.length === 0 ? (
          <option value="">No workspaces available</option>
        ) : (
          workspaces.map(workspace => (
            <option key={workspace.workspace_id} value={workspace.workspace_id}>
              {workspace.workspace_name}
            </option>
          ))
        )}
      </select>
    </div>
  )
}

export default WorkspaceSelector




