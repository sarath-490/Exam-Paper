import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { AuthProvider } from './context/AuthContext'
import Login from './pages/Login'
import AdminDashboard from './pages/AdminDashboard'
import TeacherDashboard from './pages/TeacherDashboard'
import UploadResource from './pages/UploadResource'
import GeneratePaper from './pages/GeneratePaper'
import VerifyPaper from './pages/VerifyPaper'
import History from './pages/History'
import ApprovedPapers from './pages/ApprovedPapers'
import EditPaper from './pages/EditPaper'
import PrivateRoute from './components/PrivateRoute'

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen">
          <Toaster position="top-right" />
          <Routes>
            <Route path="/login" element={<Login />} />
            
            {/* Admin Routes */}
            <Route
              path="/admin"
              element={
                <PrivateRoute role="admin">
                  <AdminDashboard />
                </PrivateRoute>
              }
            />
            
            {/* Teacher Routes */}
            <Route
              path="/teacher"
              element={
                <PrivateRoute role="teacher">
                  <TeacherDashboard />
                </PrivateRoute>
              }
            />
            <Route
              path="/upload"
              element={
                <PrivateRoute role="teacher">
                  <UploadResource />
                </PrivateRoute>
              }
            />
            <Route
              path="/generate"
              element={
                <PrivateRoute role="teacher">
                  <GeneratePaper />
                </PrivateRoute>
              }
            />
            <Route
              path="/teacher/verify/:paperId"
              element={
                <PrivateRoute role="teacher">
                  <VerifyPaper />
                </PrivateRoute>
              }
            />
            <Route
              path="/verify-paper/:paperId"
              element={
                <PrivateRoute role="teacher">
                  <VerifyPaper />
                </PrivateRoute>
              }
            />
            <Route
              path="/history"
              element={
                <PrivateRoute role="teacher">
                  <History />
                </PrivateRoute>
              }
            />
            <Route
              path="/approved-papers"
              element={
                <PrivateRoute role="teacher">
                  <ApprovedPapers />
                </PrivateRoute>
              }
            />
            <Route
              path="/edit-paper/:paperId"
              element={
                <PrivateRoute role="teacher">
                  <EditPaper />
                </PrivateRoute>
              }
            />
            
            <Route path="/" element={<Navigate to="/login" />} />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  )
}

export default App
