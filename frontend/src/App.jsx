import { Route, Routes } from 'react-router-dom'
import NavBar from './components/NavBar'
import DetectionView from './pages/DetectionView'
import HistoryView from './pages/HistoryView'

function App() {
  return (
    <>
      <NavBar />
      <main>
        <Routes>
          <Route path="/" element={<DetectionView />} />
          <Route path="/history" element={<HistoryView />} />
        </Routes>
      </main>
    </>
  )
}

export default App
