import { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import AuthModal from './components/AuthModal';
import ChatInterface from './components/ChatInterface';
import './App.css';

function AppContent() {
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const { user, logout, isAuthenticated, loading } = useAuth();

  // Listen for auth modal open event from ChatInterface
  useEffect(() => {
    const handleOpenAuthModal = () => setAuthModalOpen(true);
    window.addEventListener('openAuthModal', handleOpenAuthModal);
    return () => window.removeEventListener('openAuthModal', handleOpenAuthModal);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <span className="loading loading-spinner loading-lg"></span>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col">
      {/* Main Chat Area */}
      <div className="flex-1 overflow-hidden">
        <ChatInterface />
      </div>

      {/* Auth Modal */}
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
      />

      {/* Footer */}
      <footer className="footer footer-center p-4 bg-red-600 text-white">
        <aside>
          <div className="flex items-center justify-center gap-2 mb-2">
            <img src="/chipchiplogo.png" alt="ChipChip Logo" className="h-6 w-auto" />
          </div>
          <p>
            KcartBot - Powered by AI | Built with ❤️ for Ethiopian Agriculture
          </p>
        </aside>
      </footer>
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
