function StepsProgress({ lab, progress, onAdvance, onReset }) {
  if (!lab || !progress) return null

  const progressPercent = (progress.completed_steps.length / progress.total_steps) * 100

  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <h3 className="font-semibold text-lg text-gray-800 mb-4">📊 步驟進度</h3>
      
      {/* Lab Title */}
      <div className="mb-4">
        <span className="text-sm text-gray-500">目前實驗：</span>
        <h4 className="font-medium text-cisco-dark">{lab.title}</h4>
        {lab.chapter && (
          <span className="text-xs text-gray-400">章節 {lab.chapter}</span>
        )}
      </div>

      {/* Progress Bar */}
      <div className="mb-4">
        <div className="flex justify-between text-sm text-gray-600 mb-1">
          <span>進度</span>
          <span>{progress.completed_steps.length} / {progress.total_steps} 步驟</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div 
            className="bg-cisco-light h-3 rounded-full transition-all duration-300"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      {/* Steps List */}
      <div className="space-y-2 max-h-60 overflow-y-auto">
        {lab.steps.map((step, index) => {
          const isCompleted = progress.completed_steps.includes(step.id)
          const isCurrent = index === progress.current_step

          return (
            <div 
              key={step.id}
              className={`flex items-center space-x-2 p-2 rounded ${
                isCurrent ? 'bg-cisco-blue bg-opacity-10 border-l-4 border-cisco-blue' :
                isCompleted ? 'bg-green-50' : 'bg-gray-50'
              }`}
            >
              <span className={`w-6 h-6 flex items-center justify-center rounded-full text-xs ${
                isCompleted ? 'bg-cisco-light text-white' :
                isCurrent ? 'bg-cisco-blue text-white' :
                'bg-gray-300 text-gray-600'
              }`}>
                {isCompleted ? '✓' : step.id}
              </span>
              <span className={`text-sm ${
                isCurrent ? 'font-medium text-cisco-dark' :
                isCompleted ? 'text-green-700' : 'text-gray-600'
              }`}>
                {step.desc}
              </span>
            </div>
          )
        })}
      </div>

      {/* Action Buttons */}
      <div className="flex space-x-2 mt-4">
        <button
          onClick={onAdvance}
          disabled={progress.current_step >= progress.total_steps}
          className="flex-1 bg-cisco-blue text-white py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          完成此步驟 ✓
        </button>
        <button
          onClick={onReset}
          className="px-4 py-2 border border-gray-300 rounded-lg text-gray-600 hover:bg-gray-50 transition-colors"
        >
          重置
        </button>
      </div>
    </div>
  )
}

export default StepsProgress
