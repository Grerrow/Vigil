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
  const [uploadFileSize, setUploadFileSize] = useState(null)
  const [currentTimeMs, setCurrentTimeMs] = useState(0)

  const isVideo = selectedFile?.type.startsWith('video/') ?? false

  function selectFile(file) {
    if (!file) return
    if (!file.type.startsWith('image/' ) && !file.type.startsWith('video/')) {
      setError('Please choose an image file (JPEG or PNG) or a video file (MP4).')
      return
    }
    if (previewUrl) URL.revokeObjectURL(previewUrl)
    setSelectedFile(file)
    setPreviewUrl(URL.createObjectURL(file))
    setResult(null)
    setError(null)
    setUploadFileSize(null)
    setCurrentTimeMs(0)
  }

  function handleDrop(event) {
    event.preventDefault()
    setIsDragging(false)
    selectFile(event.dataTransfer.files[0])
  }

  function fileLoad(event) {
    setUploadFileSize({
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
      const endpoint = isVideo ? '/detect/video' : '/detect'
      const response = await axios.post(`${API_BASE_URL}${endpoint}`, formData)
      setResult(response.data)
    } catch (err) {
      setError(err.response?.data?.detail ?? err.message)
    } finally {
      setIsLoading(false)
    }
  }

  // For video, show the detections of the latest sampled frame at or before the playhead.
  let overlayDetections = []
  if (result) {
    if (isVideo) {
      const frame = result.frames.findLast((f) => f.timestamp_ms <= currentTimeMs)
      overlayDetections = frame ? frame.detections : []
    } else {
      overlayDetections = result.detections
    }
  }

  const overlaySize = isVideo && result
    ? { width: result.frame_width, height: result.frame_height }
    : uploadFileSize

  const averageConfidence = !result
    ? null
    : isVideo
      ? result.frames_analyzed > 0 && result.average_confidence > 0
        ? result.average_confidence
        : null
      : result.detections.length > 0
        ? result.detections.reduce((sum, d) => sum + d.confidence, 0) / result.detections.length
        : null
  const peopleCount = result ? (isVideo ? result.peak_person_count : result.person_count) : 0

  return (
    <section>
      <div className="page-header">
        <h2>Person detection</h2>
        <p>Upload an image or video to detect and count the people in it.</p>
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
        <strong>Drop an image/video here or click to browse</strong>
        <span>JPEG, PNG, or MP4</span>
        {/* File input for selecting an image, reminder to add video support later */}
        <input type="file" accept="image/*,video/*" onChange={(e) => selectFile(e.target.files[0])} />
      </label>

      {error && <div className="error">{error}</div>}

      {previewUrl && (
        <div className="workspace">
          <div className="card">
            <div className="preview">
              {isVideo ? (
                <video
                  src={previewUrl}
                  controls
                  onTimeUpdate={(e) => setCurrentTimeMs(e.target.currentTime * 1000)}
                  onSeeked={(e) => setCurrentTimeMs(e.target.currentTime * 1000)}
                />
              ) : (
                <img src={previewUrl} alt="Selected preview" onLoad={fileLoad} />
              )}

              {result && overlaySize && (
                <svg viewBox={`0 0 ${overlaySize.width} ${overlaySize.height}`}>
                  {overlayDetections.map((detection, index) => {
                    const { x1, y1, x2, y2 } = detection.box
                    const labelFontSize = Math.max(overlaySize.width, overlaySize.height) / 35
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
                          strokeWidth={Math.max(overlaySize.width, overlaySize.height) / 200}
                        />
                        <text
                          x={x1 + labelPadding}
                          y={y1 + labelFontSize + labelPadding}
                          fill="#34d399"
                          fontSize={labelFontSize}
                          fontWeight="normal"
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
                    <span className="stat-value">{peopleCount}</span>
                    <span className="stat-label">{isVideo ? 'Peak people' : 'People'}</span>
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

                {isVideo && (
                  <p className="filename">
                    {result.frames_analyzed} frames analyzed · avg{' '}
                    {result.average_person_count.toFixed(1)} people per frame
                  </p>
                )}

                {overlayDetections.length > 0 && (
                  <ul className="detection-list">
                    {overlayDetections.map((detection, index) => (
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
