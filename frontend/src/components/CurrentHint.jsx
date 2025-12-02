function CurrentHint({ hint }) {
  if (!hint) return null

  // Check if lab is completed
  if (hint.message) {
    return (
      <div className="bg-white rounded-lg shadow-md p-4">
        <h3 className="font-semibold text-lg text-gray-800 mb-4">🎉 完成！</h3>
        <div className="text-center py-4">
          <div className="text-4xl mb-2">🏆</div>
          <p className="text-cisco-light font-medium">{hint.message}</p>
          <p className="text-gray-500 text-sm mt-2">{hint.description}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <h3 className="font-semibold text-lg text-gray-800 mb-4">💡 當前步驟提示</h3>
      
      {/* Step Info */}
      <div className="bg-cisco-blue bg-opacity-10 rounded-lg p-3 mb-4">
        <div className="flex items-center space-x-2">
          <span className="bg-cisco-blue text-white px-2 py-1 rounded text-sm">
            步驟 {hint.step_id}
          </span>
          {hint.progress && (
            <span className="text-xs text-gray-500">
              ({hint.progress.current} / {hint.progress.total})
            </span>
          )}
        </div>
        <p className="mt-2 text-cisco-dark font-medium">{hint.description}</p>
      </div>

      {/* Checklist */}
      {hint.checklist && hint.checklist.length > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">✅ 確認清單：</h4>
          <ul className="space-y-1">
            {hint.checklist.map((item, idx) => (
              <li key={idx} className="flex items-center space-x-2 text-sm text-gray-600">
                <span className="w-4 h-4 border rounded flex items-center justify-center text-xs">
                  ☐
                </span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

export default CurrentHint
