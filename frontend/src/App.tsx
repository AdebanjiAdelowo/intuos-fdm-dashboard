import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import LoginPage from './pages/LoginPage'
import HomePage from './pages/HomePage'
import FleetOverviewPage from './pages/FleetOverviewPage'
import AircraftAnalysisPage from './pages/AircraftAnalysisPage'
import FlightAnalysisPage from './pages/FlightAnalysisPage'
import PilotAnalysisPage from './pages/PilotAnalysisPage'
import InstructorAnalysisPage from './pages/InstructorAnalysisPage'
import Layout from './components/Layout'

function isAuthenticated() {
  return Boolean(localStorage.getItem('token'))
}

function PrivateRoute({ children }: { children: React.ReactNode }) {
  return isAuthenticated() ? <>{children}</> : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/"
          element={
            <PrivateRoute>
              <Layout />
            </PrivateRoute>
          }
        >
          <Route index element={<HomePage />} />
          <Route path="fleet" element={<FleetOverviewPage />} />
          <Route path="aircraft" element={<AircraftAnalysisPage />} />
          <Route path="flights" element={<FlightAnalysisPage />} />
          <Route path="pilots" element={<PilotAnalysisPage />} />
          <Route path="instructors" element={<InstructorAnalysisPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
