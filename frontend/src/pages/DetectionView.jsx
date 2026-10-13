import { useState } from 'react'
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

function DetectionView() {
  const [selectedFile, setSelectedFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState(null)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isDragging, setIsDragging] = useState(false)
  const [imageSize, setImageSize] = useState(null)

  function selectFile(file) {
    if (!file) return
    if (!file.type.startsWith('image/')) {
      setError('Please choose an image file (JPEG or PNG).')
      return
    }
    setSelectedFile(file)
    setPreviewUrl(URL.createObjectURL(file))
    setResult(null)
    setError(null)
    setImageSize(null)
  }

  function handleDrop(event) {
    event.preventDefault()
    setIsDragging(false)
    selectFile(event.dataTransfer.files[0])
  }

  function handleImageLoad(event) {
    setImageSize({
      width: event.target.naturalWidth,
      height: event.target.naturalHeight,
    })
  }

  async function handleDetectClick() {
    if (!selectedFile) return

    setIsLoading(true)
    setError(null)
    setResult(null)

    const formData = new FormData()
    formData.append('file', selectedFile)

    try {
      const response = await axios.post(`${API_BASE_URL}/detect`, formData)
      setResult(response.data)
    } catch (err) {
      setError(err.response?.data?.detail ?? err.message)
    } finally {
      setIsLoading(false)
    }
  }

  const averageConfidence =
    result && result.detections.length > 0
      ? result.detections.reduce((sum, d) => sum + d.confidence, 0) / result.detections.length
      : null

  return (
    <section>
      <div className="page-header">
        <h2>Person detection</h2>
        <p>Upload an image to detect and count the people in it.</p>
      </div>

      <label
        className={`dropzone${isDragging ? ' dragging' : ''}`}
        onDragOver={(e) => {
          e.preventDefault()
          setIsDragging(true)
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
      >
        <strong>Drop an image here or click to browse</strong>
        <span>JPEG or PNG</span>
        <input type="file" accept="image/*" onChange={(e) => selectFile(e.target.files[0])} />
      </label>

      {error && <div className="error">{error}</div>}

      {previewUrl && (
        <div className="workspace">
          <div className="card">
            <div className="preview">
              <img src={previewUrl} alt="Selected preview" onLoad={handleImageLoad} />

              {result && imageSize && (
                <svg viewBox={`0 0 ${imageSize.width} ${imageSize.height}`}>
                  {result.detections.map((detection, index) => {
                    const { x1, y1, x2, y2 } = detection.box
                    const labelFontSize = Math.max(imageSize.width, imageSize.height) / 35
                    const labelPadding = labelFontSize / 4

                    return (
                      <g key={index}>
                        <rect
                          x={x1}
                          y={y1}
                          width={x2 - x1}
                          height={y2 - y1}
                          fill="none"
                          stroke="#34d399"
                          strokeWidth={Math.max(imageSize.width, imageSize.height) / 200}
                        />
                        <text
                          x={x1 + labelPadding}
                          y={y1 + labelFontSize + labelPadding}
                          fill="#34d399"
                          fontSize={labelFontSize}
                          fontWeight="bold"
                          stroke="#111"
                          strokeWidth={labelFontSize / 5}
                          paintOrder="stroke"
                          strokeLinejoin="round"
                        >
                          P {index + 1} — {(detection.confidence * 100).toFixed(1)}%
                        </text>
                      </g>
                    )
                  })}
                </svg>
              )}
            </div>

            <div className="actions">
              <button className="btn btn-primary" onClick={handleDetectClick} disabled={isLoading}>
                {isLoading ? 'Detecting…' : 'Detect people'}
              </button>
              <span className="filename">{selectedFile.name}</span>
            </div>
          </div>

          <div className="card">
            {result ? (
              <>
                <div className="stats">
                  <div className="stat">
                    <span className="stat-value">{result.person_count}</span>
                    <span className="stat-label">People</span>
                  </div>
                  <div className="stat">
                    <span className="stat-value">
                      {averageConfidence === null ? '—' : `${(averageConfidence * 100).toFixed(0)}%`}
                    </span>
                    <span className="stat-label">Avg conf.</span>
                  </div>
                  <div className="stat">
                    <span className="stat-value">{result.inference_time_ms.toFixed(0)}</span>
                    <span className="stat-label">ms</span>
                  </div>
                </div>

                {result.detections.length > 0 && (
                  <ul className="detection-list">
                    {result.detections.map((detection, index) => (
                      <li key={index}>
                        <span>Person {index + 1}</span>
                        <span>{(detection.confidence * 100).toFixed(1)}%</span>
                      </li>
                    ))}
                  </ul>
                )}
              </>
            ) : (
              <p className="empty">Results will appear here after detection.</p>
            )}
          </div>
        </div>
      )}
    </section>
  )
}

export default DetectionView
