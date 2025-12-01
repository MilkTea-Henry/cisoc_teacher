import { useState } from 'react'

function CommandSuggestions({ commands, onSendCommand }) {
  const [sendingIdx, setSendingIdx] = useState(null)
  const [copied, setCopied] = useState(null)

  const handleSendCommand = async (cmd, idx) => {
    setSendingIdx(idx)
    const success = await onSendCommand(cmd)
    setSendingIdx(null)
    
    if (!success) {
      alert('無法發送指令到 Packet Tracer。請確認程式是否已開啟。')
    }
  }

  const handleCopyCommand = async (cmd, idx) => {
    try {
      await navigator.clipboard.writeText(cmd)
      setCopied(idx)
      setTimeout(() => setCopied(null), 2000)
    } catch (err) {
      console.error('Copy failed:', err)
    }
  }

  if (!commands || commands.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-4">
        <h3 className="font-semibold text-lg text-gray-800 mb-4">⌨️ 指令建議</h3>
        <p className="text-gray-500 text-sm text-center py-4">
          此步驟無建議指令
        </p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <h3 className="font-semibold text-lg text-gray-800 mb-4">⌨️ 指令建議</h3>
      
      <div className="space-y-2">
        {commands.map((cmd, idx) => (
          <div 
            key={idx}
            className="bg-gray-900 rounded-lg p-3 group"
          >
            <code className="text-green-400 cli-font text-sm block mb-2">
              {cmd}
            </code>
            <div className="flex space-x-2">
              <button
                onClick={() => handleCopyCommand(cmd, idx)}
                className="flex-1 text-xs bg-gray-700 text-white py-1 px-3 rounded hover:bg-gray-600 transition-colors"
              >
                {copied === idx ? '✓ 已複製' : '📋 複製'}
              </button>
              <button
                onClick={() => handleSendCommand(cmd, idx)}
                disabled={sendingIdx !== null}
                className="flex-1 text-xs bg-cisco-blue text-white py-1 px-3 rounded hover:bg-blue-600 disabled:opacity-50 transition-colors"
              >
                {sendingIdx === idx ? '發送中...' : '🚀 一鍵輸入'}
              </button>
            </div>
          </div>
        ))}
      </div>

      <p className="text-xs text-gray-400 mt-3 text-center">
        💡 「一鍵輸入」會將指令自動輸入到 Packet Tracer CLI
      </p>
    </div>
  )
}

export default CommandSuggestions
