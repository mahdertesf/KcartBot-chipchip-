import { useState } from 'react';
import { useAuth } from '../context/AuthContext';

const AuthModal = ({ isOpen, onClose }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    email: '',
    role: 'customer',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { login, signup } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      let result;
      if (isLogin) {
        result = await login(formData.username, formData.password);
      } else {
        result = await signup(
          formData.username,
          formData.password,
          formData.email,
          formData.role
        );
      }

      if (result.success) {
        onClose();
        setFormData({ username: '', password: '', email: '', role: 'customer' });
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError('An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  if (!isOpen) return null;

  return (
    <div className="modal modal-open">
      <div className="modal-box">
        <div className="flex items-center justify-center mb-4">
          <img src="/chipchiplogo.png" alt="ChipChip Logo" className="h-16 w-auto" />
        </div>
        <h3 className="font-bold text-lg mb-4 text-center">
          {isLogin ? 'Login to KcartBot' : 'Create Account'}
        </h3>
        
        {error && (
          <div className="alert alert-error mb-4">
            <svg xmlns="http://www.w3.org/2000/svg" className="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-control">
            <label className="label">
              <span className="label-text">Username</span>
            </label>
            <input
              type="text"
              name="username"
              value={formData.username}
              onChange={handleChange}
              className="input input-bordered"
              required
            />
          </div>

          {!isLogin && (
            <div className="form-control mt-4">
              <label className="label">
                <span className="label-text">Email</span>
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className="input input-bordered"
                required
              />
            </div>
          )}

          <div className="form-control mt-4">
            <label className="label">
              <span className="label-text">Password</span>
            </label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              className="input input-bordered"
              required
            />
          </div>

          {!isLogin && (
            <div className="form-control mt-4">
              <label className="label">
                <span className="label-text">I am a...</span>
              </label>
              <select
                name="role"
                value={formData.role}
                onChange={handleChange}
                className="select select-bordered"
              >
                <option value="customer">Customer</option>
                <option value="supplier">Supplier</option>
              </select>
            </div>
          )}

          <div className="modal-action">
            <button
              type="button"
              className="btn btn-ghost"
              onClick={onClose}
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn bg-red-600 hover:bg-red-700 text-white border-red-600"
              disabled={loading}
            >
              {loading ? (
                <span className="loading loading-spinner"></span>
              ) : (
                isLogin ? 'Login' : 'Sign Up'
              )}
            </button>
          </div>
        </form>

        <div className="divider">OR</div>

        <button
          type="button"
          className="btn btn-link btn-sm w-full text-red-600 hover:text-red-700"
          onClick={() => {
            setIsLogin(!isLogin);
            setError('');
          }}
        >
          {isLogin
            ? "Don't have an account? Sign up"
            : 'Already have an account? Login'}
        </button>
      </div>
    </div>
  );
};

export default AuthModal;

