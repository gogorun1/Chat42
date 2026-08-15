import { Route, Routes } from 'react-router-dom'
import { AdminRoute } from './components/AdminRoute'
import { Layout } from './components/Layout'
import { ProtectedRoute } from './components/ProtectedRoute'
import { AdminPage } from './pages/AdminPage'
import { HomePage } from './pages/HomePage'
import { LoginPage } from './pages/LoginPage'
import { PrivacyPolicyPage } from './pages/PrivacyPolicyPage'
import { ProfilePage } from './pages/ProfilePage'
import { SignupPage } from './pages/SignupPage'
import { TermsOfServicePage } from './pages/TermsOfServicePage'
import { UploadPage } from './pages/UploadPage'
import { AnalyticsPage } from './pages/AnalyticsPage'
import { SearchPage } from './pages/SearchPage'


function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        {/* Protected routes - any authenticated user */}
        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/profile/:id" element={<ProfilePage />} />
          <Route element={<AdminRoute />}>
             <Route path="/admin" element={<AdminPage />} />
             </Route>
        </Route>

        {/* Protected routes - admin only */}
        <Route element={<ProtectedRoute requiredRole="admin" />}>
          <Route path="/analytics" element={<AnalyticsPage />} />
        </Route>

        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/privacy-policy" element={<PrivacyPolicyPage />} />
        <Route path="/terms-of-service" element={<TermsOfServicePage />} />
      </Route>
    </Routes>
  )
}

export default App
