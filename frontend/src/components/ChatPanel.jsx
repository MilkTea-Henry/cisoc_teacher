import { useState, useRef, useEffect } from 'react'

function ChatPanel({ labId, stepId, apiBase }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Add welcome message when lab changes
  useEffect(() => {
    if (labId) {
      setMessages([{
        role: 'assistant',
        content: `歡迎來到練功房！我是您的 Cisco 助教。\n\n您目前正在練習 Lab ${labId}。有任何問題都可以問我，例如：\n• 這個步驟該怎麼做？\n• 這個指令是什麼意思？\n• 為什麼設定沒有生效？`
      }])
    }
  }, [labId])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setLoading(true)

    try {
      const response = await fetch(`${apiBase}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: userMessage,
          lab_id: labId,
          step_id: stepId
        })
      })
      const data = await response.json()
      
      let assistantMessage = data.response
      if (data.suggested_commands && data.suggested_commands.length > 0) {
        assistantMessage += '\n\n💡 建議的指令：\n' + data.suggested_commands.map(cmd => `  • ${cmd}`).join('\n')
      }
      if (data.current_step_hint) {
        assistantMessage += `\n\n📝 當前步驟提示：${data.current_step_hint}`
      }

      setMessages(prev => [...prev, { role: 'assistant', content: assistantMessage }])
    } catch (error) {
      console.error('Chat error:', error)
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: '抱歉，發生錯誤。請稍後再試。' 
      }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-md h-[600px] flex flex-col">
      {/* Header */}
      <div className="bg-cisco-blue text-white px-4 py-3 rounded-t-lg">
        <h2 className="font-semibold text-lg">💬 練功房對話</h2>
        <p className="text-sm opacity-80">練習指令、問答、即時協助</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 chat-scroll">
        {messages.map((msg, idx) => (
          <div 
            key={idx}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div 
              className={`max-w-[80%] rounded-lg px-4 py-2 ${
                msg.role === 'user' 
                  ? 'bg-cisco-blue text-white' 
                  : 'bg-gray-100 text-gray-800'
              }`}
            >
              <pre className="whitespace-pre-wrap font-sans text-sm">{msg.content}</pre>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg px-4 py-2">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t">
        <div className="flex space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="輸入問題或指令..."
            className="flex-1 border rounded-lg px-4 py-2 focus:outline-none focus:border-cisco-blue"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="bg-cisco-blue text-white px-6 py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            發送
          </button>
        </div>
      </form>
    </div>
  )
}

export default ChatPanel
