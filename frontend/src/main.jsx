import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import { ThemeProvider } from './contexts/ThemeContext'
import './styles/theme.css'
import './styles/index.css'

console.log('🚀 [Main] Starting Workspace Guardian...')
console.log('🌐 [Main] Current URL:', window.location.href)
console.log('📍 [Main] Origin:', window.location.origin)

try {
  const rootElement = document.getElementById('root')
  if (!rootElement) {
    console.error('❌ [Main] Root element not found!')
    throw new Error('Root element not found')
  }
  console.log('✅ [Main] Root element found')
  
  const root = ReactDOM.createRoot(rootElement)
  console.log('✅ [Main] React root created')
  
  root.render(
    <React.StrictMode>
      <ThemeProvider>
        <App />
      </ThemeProvider>
    </React.StrictMode>,
  )
  console.log('✅ [Main] App rendered successfully')
} catch (error) {
  console.error('❌ [Main] Fatal error during initialization:', error)
  document.body.innerHTML = `
    <div style="padding: 20px; font-family: system-ui; max-width: 600px; margin: 50px auto;">
      <h1 style="color: #dc2626;">⚠️ Application Error</h1>
      <p>Failed to initialize Workspace Guardian</p>
      <pre style="background: #f3f4f6; padding: 10px; border-radius: 4px; overflow: auto;">${error.message}\n\n${error.stack}</pre>
      <p style="margin-top: 20px;">Please check the browser console for more details.</p>
    </div>
  `
}
