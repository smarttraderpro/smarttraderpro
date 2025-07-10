// frontend_web/src/components/Profile.js
import React, { useState, useEffect } from 'react';
import { fetchUserProfile, updateUserProfile, updateUserBrokerCredentials } from '../api';

function Profile() {
  const [userData, setUserData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  // Form states for profile update
  const [email, setEmail] = useState('');
  const [mobileNumber, setMobileNumber] = useState('');
  const [brokerPreference, setBrokerPreference] = useState('');

  // Form states for AngelOne credentials
  const [angelClientId, setAngelClientId] = useState('');
  const [angelApiKey, setAngelApiKey] = useState('');
  const [angelApiSecret, setAngelApiSecret] = useState('');

  useEffect(() => {
    const loadProfile = async () => {
      try {
        setLoading(true);
        const response = await fetchUserProfile();
        setUserData(response.data);
        setEmail(response.data.email || '');
        setMobileNumber(response.data.mobile_number || '');
        setBrokerPreference(response.data.broker_preference || 'NONE');

        // Note: We don't fetch and display existing API keys/secrets for security.
        // User re-enters them if they want to update.
        // We could fetch and display the broker_user_id (Client ID) if it's set.
        // For simplicity, current UserPublic schema doesn't expose encrypted keys.
        // We would need a way to know if keys are *set* without showing them.

      } catch (err) {
        setError('Failed to load user profile.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    loadProfile();
  }, []);

  const handleProfileUpdate = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMessage('');
    try {
      const profileUpdateData = {
        ...(email !== userData.email && { email }),
        ...(mobileNumber !== userData.mobile_number && { mobile_number: mobileNumber }),
        ...(brokerPreference !== userData.broker_preference && { broker_preference: brokerPreference }),
      };
      if (Object.keys(profileUpdateData).length > 0) {
        const response = await updateUserProfile(profileUpdateData);
        setUserData(response.data); // Update local state with new profile data
        setSuccessMessage('Profile updated successfully!');
      } else {
        setSuccessMessage('No changes to update in general profile.');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update profile.');
      console.error(err);
    }
  };

  const handleAngelCredentialsUpdate = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMessage('');
    if (!angelClientId || !angelApiKey || !angelApiSecret) {
        setError('Please fill in all AngelOne credential fields to update.');
        return;
    }
    try {
      const credentialsData = {
        broker_user_id: angelClientId,
        api_key: angelApiKey,
        api_secret: angelApiSecret,
      };
      await updateUserBrokerCredentials(credentialsData);
      setSuccessMessage('AngelOne credentials updated successfully! (Stored securely)');
      // Clear fields after successful update for security
      setAngelClientId('');
      setAngelApiKey('');
      setAngelApiSecret('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update AngelOne credentials.');
      console.error(err);
    }
  };

  if (loading) return <p>Loading profile...</p>;
  if (error && !userData) return <p style={{ color: 'red' }}>{error}</p>; // Show general error if profile completely failed

  return (
    <div className="profile-container">
      <h2>My Profile & Settings</h2>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {successMessage && <p style={{ color: 'green' }}>{successMessage}</p>}

      {userData && (
        <form onSubmit={handleProfileUpdate}>
          <h3>General Information</h3>
          <div>
            <label htmlFor="email">Email:</label>
            <input type="email" id="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div>
            <label htmlFor="mobileNumber">Mobile Number:</label>
            <input type="tel" id="mobileNumber" value={mobileNumber} onChange={(e) => setMobileNumber(e.target.value)} />
          </div>
          <div>
            <label htmlFor="brokerPreference">Preferred Broker:</label>
            <select id="brokerPreference" value={brokerPreference} onChange={(e) => setBrokerPreference(e.target.value)}>
              <option value="NONE">None</option>
              <option value="ANGELONE">Angel One</option>
              <option value="ZERODHA">Zerodha (Not Implemented)</option>
              <option value="UPSTOX">Upstox (Not Implemented)</option>
            </select>
          </div>
          <button type="submit">Update Profile</button>
        </form>
      )}

      <hr />

      <h3>Broker API Credentials</h3>
      <p>Select your preferred broker above first. Then, enter credentials for the selected broker.</p>

      {brokerPreference === 'ANGELONE' && (
        <form onSubmit={handleAngelCredentialsUpdate}>
          <h4>Angel One Credentials</h4>
          <p>Your API Key and Secret are stored encrypted. Enter them here to set or update.</p>
          <div>
            <label htmlFor="angelClientId">Client ID (Username):</label>
            <input type="text" id="angelClientId" value={angelClientId} onChange={(e) => setAngelClientId(e.target.value)} placeholder="Your AngelOne Client ID" />
          </div>
          <div>
            <label htmlFor="angelApiKey">API Key:</label>
            <input type="text" id="angelApiKey" value={angelApiKey} onChange={(e) => setAngelApiKey(e.target.value)} placeholder="Your AngelOne API Key" />
          </div>
          <div>
            <label htmlFor="angelApiSecret">API Secret / Key:</label>
            <input type="password" id="angelApiSecret" value={angelApiSecret} onChange={(e) => setAngelApiSecret(e.target.value)} placeholder="Your AngelOne API Secret" />
          </div>
          <button type="submit">Save AngelOne Credentials</button>
        </form>
      )}

      {/* Add similar conditional forms for Zerodha, Upstox when implemented */}
      {brokerPreference === 'ZERODHA' && <p>Zerodha integration not yet implemented.</p>}
      {brokerPreference === 'UPSTOX' && <p>Upstox integration not yet implemented.</p>}

    </div>
  );
}

export default Profile;
