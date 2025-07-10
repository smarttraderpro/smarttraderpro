import React, { useEffect, useState } from 'react';
import { fetchUserProfile, fetchLiveIndices } from '../api'; // Added fetchLiveIndices
import './Dashboard.css'; // For styling the dashboard

function Dashboard() {
  const [userData, setUserData] = useState(null);
  const [indicesData, setIndicesData] = useState([]);
  const [loadingProfile, setLoadingProfile] = useState(true);
  const [loadingIndices, setLoadingIndices] = useState(true);
  const [error, setError] = useState('');

  // Fetch user profile data
  useEffect(() => {
    const getUserProfile = async () => {
      try {
        setLoadingProfile(true);
        const response = await fetchUserProfile();
        setUserData(response.data);
        setError('');
      } catch (err) {
        console.error("Fetch user profile error:", err);
        setError('Failed to fetch user profile. Please try logging in again.');
        // Handle token expiry or invalid token, e.g., redirect to login
        // navigate('/login'); // if using useNavigate
      } finally {
        setLoadingProfile(false);
      }
    };
    getUserProfile();
  }, []);

  // Fetch live indices data and set up polling
  useEffect(() => {
    const getIndicesData = async () => {
      try {
        setLoadingIndices(true);
        const response = await fetchLiveIndices();
        if (response.data && response.data.data) {
          setIndicesData(response.data.data);
        } else {
          setIndicesData([]); // Handle case where data might be missing
        }
        setError(''); // Clear previous errors if successful
      } catch (err) {
        console.error("Fetch live indices error:", err);
        setError('Failed to fetch live market data. It might be temporarily unavailable.');
        setIndicesData([]); // Clear data on error
      } finally {
        setLoadingIndices(false);
      }
    };

    getIndicesData(); // Initial fetch
    const intervalId = setInterval(getIndicesData, 15000); // Poll every 15 seconds

    return () => clearInterval(intervalId); // Cleanup interval on component unmount
  }, []);


  if (loadingProfile) {
    return <p>Loading profile...</p>;
  }

  if (error && !userData) { // Show general error if profile failed and no user data
    return <p style={{ color: 'red' }}>{error}</p>;
  }

  return (
    <div className="dashboard-container">
      <h2>User Dashboard</h2>
      {userData ? (
        <p>Welcome, {userData.email}!</p>
      ) : (
        <p style={{ color: 'orange' }}>User profile not loaded.</p>
      )}

      <hr />
      <h3>Live Market Indices</h3>
      {loadingIndices && <p>Loading market data...</p>}
      {error && indicesData.length === 0 && <p style={{ color: 'red' }}>{error}</p>}

      {!loadingIndices && indicesData.length === 0 && !error && (
        <p>No market data available at the moment.</p>
      )}

      {indicesData.length > 0 && (
        <div className="indices-grid">
          {indicesData.map((index) => (
            <div key={index.symbol} className="index-card">
              <h4>{index.symbol}</h4>
              <p className={`ltp ${index.change > 0 ? 'positive' : index.change < 0 ? 'negative' : 'neutral'}`}>
                {index.ltp.toFixed(2)}
              </p>
              <p className={`change ${index.change > 0 ? 'positive' : index.change < 0 ? 'negative' : 'neutral'}`}>
                {index.change.toFixed(2)} ({index.percent_change.toFixed(2)}%)
              </p>
            </div>
          ))}
        </div>
      )}
      {/* More dashboard content will go here */}
    </div>
  );
}

export default Dashboard;
