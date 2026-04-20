import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import NetworkManager from './pages/NetworkManager'
import NetworkCreator from './pages/NetworkCreator'
import TrainingLab from './pages/TrainingLab'
import LearningConfig from './pages/LearningConfig'
import CommandMode from './pages/CommandMode'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Navigate to="/networks" replace />} />
        <Route path="/networks" element={<NetworkManager />} />
        <Route path="/networks/new" element={<NetworkCreator />} />
        <Route path="/networks/:id/training" element={<TrainingLab />} />
        <Route path="/networks/:id/config" element={<LearningConfig />} />
        <Route path="/networks/:id/command" element={<CommandMode />} />
      </Route>
    </Routes>
  )
}
