import React, { useEffect, useState } from 'react';
// import api from '../api'; // Example: if you have an api utility

function Dashboard() {
  const [userData, setUserData] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        // Example: Fetch user data from /users/me
        // const response = await api.get('/api/v1/users/me');
        // setUserData(response.data);

        // Placeholder data for now
        setUserData({ email: "user@example.com", message: "Welcome to your dashboard!" });

      } catch (err) {
        setError('Failed to fetch user data. Please try logging in again.');
        console.error("Dashboard fetch error:", err);
        // Handle token expiry or invalid token, e.g., redirect to login
      }
    };

    fetchUserData();
  }, []);

  if (error) {
    return <p style={{ color: 'red' }}>{error}</p>;
  }

  if (!userData) {
    return <p>Loading dashboard...</p>;
  }

  return (
    <div>
      <h2>User Dashboard</h2>
      <p>Email: {userData.email}</p>
      <p>{userData.message}</p>
      {/* More dashboard content will go here */}
    </div>
  );
}

export default Dashboard;
