import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom'; // Corrected import
import { loginUser } from '../api';

function Login({ setToken }) {
  const [username, setUsername] = useState(''); // Can be email or mobile
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const response = await loginUser({ username, password });
      if (response.data.access_token) {
        setToken(response.data.access_token); // Call prop function to set token in App.js
        // Optionally store refresh token: localStorage.setItem('refreshToken', response.data.refresh_token);
        navigate('/dashboard');
      } else {
        setError('Login failed: No token received.');
      }
    } catch (err) {
      if (err.response && err.response.data && err.response.data.detail) {
        setError(err.response.data.detail);
      } else {
        setError('Login failed. Please try again.');
      }
      console.error('Login error:', err);
    }
  };

  return (
    <div>
      <h2>Login</h2>
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="username">Email or Mobile:</label>
          <input
            type="text"
            id="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </div>
        <div>
          <label htmlFor="password">Password:</label>
          <input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        {error && <p style={{ color: 'red' }}>{error}</p>}
        <button type="submit">Login</button>
      </form>
    </div>
  );
}

export default Login;
