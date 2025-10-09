import { useState } from 'react'
import { Settings as SettingsIcon, X, Palette } from 'lucide-react'
import { useTheme } from '../contexts/ThemeContext'
import '../styles/Settings.css'

function Settings() {
  const [isOpen, setIsOpen] = useState(false)
  const { theme, setTheme, themes } = useTheme()

  const handleThemeChange = (newTheme) => {
    setTheme(newTheme)
  }

  return (
    <>
      {/* Settings Button */}
      <button 
        className="settings-button"
        onClick={() => setIsOpen(true)}
        title="Settings"
      >
        <SettingsIcon size={20} />
      </button>

      {/* Settings Modal */}
      {isOpen && (
        <div className="settings-overlay" onClick={() => setIsOpen(false)}>
          <div className="settings-modal" onClick={(e) => e.stopPropagation()}>
            {/* Header */}
            <div className="settings-header">
              <h2>
                <SettingsIcon size={24} />
                Settings
              </h2>
              <button 
                className="settings-close"
                onClick={() => setIsOpen(false)}
                title="Close"
              >
                <X size={20} />
              </button>
            </div>

            {/* Content */}
            <div className="settings-content">
              {/* Theme Section */}
              <div className="settings-section">
                <div className="settings-section-header">
                  <Palette size={20} />
                  <h3>Theme</h3>
                </div>
                <p className="settings-section-description">
                  Choose your preferred color theme
                </p>

                <div className="theme-options">
                  {themes.map((themeOption) => (
                    <button
                      key={themeOption.id}
                      className={`theme-option ${theme === themeOption.id ? 'active' : ''}`}
                      onClick={() => handleThemeChange(themeOption.id)}
                    >
                      <div className="theme-option-header">
                        <div className={`theme-preview theme-preview-${themeOption.id}`}>
                          <div className="theme-preview-color primary"></div>
                          <div className="theme-preview-color secondary"></div>
                          <div className="theme-preview-color tertiary"></div>
                        </div>
                        <div className="theme-option-info">
                          <span className="theme-option-name">{themeOption.name}</span>
                          <span className="theme-option-description">{themeOption.description}</span>
                        </div>
                      </div>
                      {theme === themeOption.id && (
                        <span className="theme-option-check">✓</span>
                      )}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="settings-footer">
              <button 
                className="settings-done-button"
                onClick={() => setIsOpen(false)}
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export default Settings


