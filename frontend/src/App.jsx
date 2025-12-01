import { useState, useEffect } from 'react'
import ChatPanel from './components/ChatPanel'
import StepsProgress from './components/StepsProgress'
import CurrentHint from './components/CurrentHint'
import CommandSuggestions from './components/CommandSuggestions'
import LabSelector from './components/LabSelector'

const API_BASE = '/api'

function App() {
  const [labs, setLabs] = useState([])
  const [currentLab, setCurrentLab] = useState(null)
  const [progress, setProgress] = useState(null)
  const [currentHint, setCurrentHint] = useState(null)
  const [loading, setLoading] = useState(true)

  // Fetch labs on mount
  useEffect(() => {
    fetchLabs()
  }, [])

  // Fetch progress and hint when lab changes
  useEffect(() => {
    if (currentLab) {
      fetchProgress()
      fetchCurrentHint()
    }
  }, [currentLab])

  const fetchLabs = async () => {
    try {
      const response = await fetch(`${API_BASE}/labs`)
      const data = await response.json()
      setLabs(data)
      if (data.length > 0) {
        setCurrentLab(data[0])
      }
    } catch (error) {
      console.error('Error fetching labs:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchProgress = async () => {
    if (!currentLab) return
    try {
      const response = await fetch(`${API_BASE}/labs/${currentLab.lab_id}/progress`)
      const data = await response.json()
      setProgress(data)
    } catch (error) {
      console.error('Error fetching progress:', error)
    }
  }

  const fetchCurrentHint = async () => {
    if (!currentLab) return
    try {
      const response = await fetch(`${API_BASE}/labs/${currentLab.lab_id}/current-hint`)
      const data = await response.json()
      setCurrentHint(data)
    } catch (error) {
      console.error('Error fetching current hint:', error)
    }
  }

  const handleAdvanceStep = async () => {
    if (!currentLab) return
    try {
      const response = await fetch(`${API_BASE}/labs/${currentLab.lab_id}/progress/next`, {
        method: 'POST'
      })
      const data = await response.json()
      setProgress(data)
      fetchCurrentHint()
    } catch (error) {
      console.error('Error advancing step:', error)
    }
  }

  const handleResetProgress = async () => {
    if (!currentLab) return
    try {
      const response = await fetch(`${API_BASE}/labs/${currentLab.lab_id}/progress/reset`, {
        method: 'POST'
      })
      const data = await response.json()
      setProgress(data)
      fetchCurrentHint()
    } catch (error) {
      console.error('Error resetting progress:', error)
    }
  }

  const handleSendCommand = async (command) => {
    try {
      const response = await fetch(`${API_BASE}/cli/send?command=${encodeURIComponent(command)}&press_enter=true`, {
        method: 'POST'
      })
      const data = await response.json()
      return data.success
    } catch (error) {
      console.error('Error sending command:', error)
      return false
    }
  }

  const handleLoadLab = async (labData) => {
    try {
      const response = await fetch(`${API_BASE}/labs/json`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(labData)
      })
      const data = await response.json()
      setLabs(prev => [...prev.filter(l => l.lab_id !== data.lab_id), data])
      setCurrentLab(data)
    } catch (error) {
      console.error('Error loading lab:', error)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-xl text-gray-600">載入中...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-cisco-dark text-white py-4 px-6 shadow-lg">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h1 className="text-2xl font-bold">🎓 Cisco Lab Teacher</h1>
            <span className="text-cisco-blue">練功房</span>
          </div>
          <LabSelector 
            labs={labs} 
            currentLab={currentLab} 
            onSelectLab={setCurrentLab}
            onLoadLab={handleLoadLab}
          />
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 px-4">
        {!currentLab ? (
          <div className="text-center py-20">
            <h2 className="text-2xl font-semibold text-gray-700 mb-4">
              歡迎使用 Cisco Lab Teacher!
            </h2>
            <p className="text-gray-500 mb-6">
              請先載入一個 Lab 檔案開始練習
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Column - Progress & Hints */}
            <div className="lg:col-span-1 space-y-6">
              {/* Steps Progress */}
              <StepsProgress 
                lab={currentLab}
                progress={progress}
                onAdvance={handleAdvanceStep}
                onReset={handleResetProgress}
              />

              {/* Current Hint */}
              <CurrentHint hint={currentHint} />

              {/* Command Suggestions */}
              <CommandSuggestions 
                commands={currentHint?.commands || []}
                onSendCommand={handleSendCommand}
              />
            </div>

            {/* Right Column - Chat */}
            <div className="lg:col-span-2">
              <ChatPanel 
                labId={currentLab?.lab_id}
                stepId={currentHint?.step_id}
                apiBase={API_BASE}
              />
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-gray-200 py-4 text-center text-gray-600 text-sm">
        <p>Cisco Lab Teacher © 2024 - 協助您精通 Cisco 網路設定</p>
      </footer>
    </div>
  )
}

export default App
