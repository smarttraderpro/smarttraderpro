import React, { useState, useEffect } from 'react';
import { Routes, Route, Link, useNavigate } from 'react-router-dom';
import Login from './components/Login';
import Signup from './components/Signup';
import Dashboard from './components/Dashboard'; // Placeholder for after login
import Home from './components/Home'; // Placeholder for landing page
import VerifyAccount from './components/VerifyAccount'; // Import the new component
import './App.css'; // Basic CSS, can be created later

function App() {
  const [token, setToken] = useState(localStorage.getItem('authToken'));
  const navigate = useNavigate();

  const handleSetToken = (newToken) => {
    localStorage.setItem('authToken', newToken);
    setToken(newToken);
  };

  const handleLogout = () => {
    localStorage.removeItem('authToken');
    setToken(null);
    navigate('/login');
  };

  useEffect(() => {
    // Optional: Could add token validation logic here if needed on app load
    // For now, just checks presence.
    const storedToken = localStorage.getItem('authToken');
    if (storedToken) {
      setToken(storedToken); // Corrected variable name
    }
  }, []);


  return (
    <div className="App">
      <nav>
        <ul>
          <li><Link to="/">Home</Link></li>
          {!token ? (
            <>
              <li><Link to="/login">Login</Link></li>
              <li><Link to="/signup">Signup</Link></li>
            </>
          ) : (
            <>
              <li><Link to="/dashboard">Dashboard</Link></li>
              <li><button onClick={handleLogout}>Logout</button></li>
            </>
          )}
        </ul>
      </nav>

      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login setToken={handleSetToken} />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/verify-account" element={<VerifyAccount />} />
        {token ? (
           <Route path="/dashboard" element={<Dashboard />} />
        ) : (
          // Redirect to login if trying to access dashboard without token
          // This is a simple way, protected routes are better for complex apps
          <Route path="/dashboard" element={<Login setToken={handleSetToken} />} />
        )}
      </Routes>
    </div>
  );
}

export default App;
