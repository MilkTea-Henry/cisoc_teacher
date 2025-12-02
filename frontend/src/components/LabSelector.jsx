import { useState } from 'react'

function LabSelector({ labs, currentLab, onSelectLab, onLoadLab }) {
  const [showModal, setShowModal] = useState(false)
  const [jsonInput, setJsonInput] = useState('')
  const [error, setError] = useState('')

  const handleLoadJson = () => {
    setError('')
    try {
      const labData = JSON.parse(jsonInput)
      if (!labData.lab_id || !labData.title) {
        setError('JSON 必須包含 lab_id 和 title 欄位')
        return
      }
      onLoadLab(labData)
      setShowModal(false)
      setJsonInput('')
    } catch (e) {
      setError('JSON 格式錯誤：' + e.message)
    }
  }

  const sampleLab = {
    lab_id: "2.1.3",
    title: "Basic Router Configuration",
    chapter: "2",
    objective: "Configure basic router settings",
    steps: [
      { id: "1", desc: "Enter privileged mode", cmds: ["enable"], checklist: ["Prompt shows #"] },
      { id: "2", desc: "Enter global config", cmds: ["configure terminal"], checklist: [] },
      { id: "3", desc: "Set hostname", cmds: ["hostname R1"], checklist: ["Prompt shows R1"] }
    ],
    qa: [
      { q: "What is enable?", a: "Enters privileged EXEC mode" }
    ]
  }

  return (
    <>
      <div className="flex items-center space-x-4">
        {/* Lab Dropdown */}
        <select
          value={currentLab?.lab_id || ''}
          onChange={(e) => {
            const lab = labs.find(l => l.lab_id === e.target.value)
            if (lab) onSelectLab(lab)
          }}
          className="bg-cisco-dark border border-gray-600 text-white px-3 py-2 rounded-lg focus:outline-none focus:border-cisco-blue"
        >
          <option value="" disabled>選擇實驗...</option>
          {labs.map(lab => (
            <option key={lab.lab_id} value={lab.lab_id}>
              Lab {lab.lab_id} - {lab.title}
            </option>
          ))}
        </select>

        {/* Load Lab Button */}
        <button
          onClick={() => setShowModal(true)}
          className="bg-cisco-light text-white px-4 py-2 rounded-lg hover:bg-green-600 transition-colors"
        >
          + 載入 Lab
        </button>
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl mx-4">
            <div className="p-6">
              <h2 className="text-xl font-semibold text-gray-800 mb-4">載入 Lab JSON</h2>
              
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  貼上 Lab JSON 資料：
                </label>
                <textarea
                  value={jsonInput}
                  onChange={(e) => setJsonInput(e.target.value)}
                  className="w-full h-64 border rounded-lg p-3 cli-font text-sm focus:outline-none focus:border-cisco-blue"
                  placeholder={JSON.stringify(sampleLab, null, 2)}
                />
              </div>

              {error && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
                  {error}
                </div>
              )}

              <div className="mb-4">
                <button
                  onClick={() => setJsonInput(JSON.stringify(sampleLab, null, 2))}
                  className="text-sm text-cisco-blue hover:underline"
                >
                  📝 載入範例 Lab
                </button>
              </div>

              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => {
                    setShowModal(false)
                    setJsonInput('')
                    setError('')
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-gray-600 hover:bg-gray-50 transition-colors"
                >
                  取消
                </button>
                <button
                  onClick={handleLoadJson}
                  className="px-4 py-2 bg-cisco-blue text-white rounded-lg hover:bg-blue-600 transition-colors"
                >
                  載入
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export default LabSelector
