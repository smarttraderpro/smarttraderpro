// frontend_web/src/components/Portfolio.js
import React, { useState, useEffect } from 'react';
import { fetchUserProfile, fetchAngelOneProfile, fetchAngelOneHoldings } from '../api';
import './Portfolio.css'; // For styling

function Portfolio() {
  const [currentUser, setCurrentUser] = useState(null);
  const [angelProfile, setAngelProfile] = useState(null);
  const [angelHoldings, setAngelHoldings] = useState([]);

  const [isLoadingProfile, setIsLoadingProfile] = useState(false);
  const [isLoadingHoldings, setIsLoadingHoldings] = useState(false);

  const [error, setError] = useState('');

  // State for PIN/TOTP modal/form
  const [showPinTotpModal, setShowPinTotpModal] = useState(false);
  const [pin, setPin] = useState('');
  const [totp, setTotp] = useState('');
  const [actionToRetry, setActionToRetry] = useState(null); // To store which function to retry ('profile' or 'holdings')

  useEffect(() => {
    const loadCurrentUser = async () => {
      try {
        const response = await fetchUserProfile();
        setCurrentUser(response.data);
      } catch (err) {
        console.error("Error fetching current user:", err);
        setError("Could not load your user profile.");
      }
    };
    loadCurrentUser();
  }, []);

  const handleFetchAngelData = async (action, currentPin = null, currentTotp = null) => {
    setError('');
    if (action === 'profile') setIsLoadingProfile(true);
    if (action === 'holdings') setIsLoadingHoldings(true);

    try {
      let response;
      if (action === 'profile') {
        response = await fetchAngelOneProfile(currentPin, currentTotp);
        setAngelProfile(response.data);
      } else if (action === 'holdings') {
        response = await fetchAngelOneHoldings(currentPin, currentTotp);
        setAngelHoldings(response.data.data || []); // API returns { "data": [...] }
      }
      setShowPinTotpModal(false); // Close modal on success
      setActionToRetry(null);
    } catch (err) {
      console.error(`Error fetching AngelOne ${action}:`, err);
      if (err.response && err.response.status === 401 && err.response.data?.detail?.toLowerCase().includes("session requires password/pin and totp")) {
        setError(`AngelOne session requires PIN & TOTP. Please enter them.`);
        setShowPinTotpModal(true);
        setActionToRetry(action); // Store which action to retry
      } else {
        setError(err.response?.data?.detail || `Failed to fetch AngelOne ${action}.`);
      }
    } finally {
      if (action === 'profile') setIsLoadingProfile(false);
      if (action === 'holdings') setIsLoadingHoldings(false);
    }
  };

  const handlePinTotpSubmit = (e) => {
    e.preventDefault();
    if (actionToRetry) {
      handleFetchAngelData(actionToRetry, pin, totp);
    }
    setPin(''); // Clear after submit
    setTotp(''); // Clear after submit
  };

  if (!currentUser) {
    return <p>Loading user data...</p>;
  }

  const isAngelOneSelected = currentUser.broker_preference === 'ANGELONE';

  return (
    <div className="portfolio-container">
      <h2>My Broker Portfolio</h2>
      {error && <p className="error-message">{error}</p>}

      {!isAngelOneSelected && (
        <p>Please select AngelOne as your preferred broker in Profile & Settings to view portfolio data here.</p>
      )}

      {isAngelOneSelected && (
        <div>
          <h3>Angel One Account</h3>
          <button onClick={() => handleFetchAngelData('profile')} disabled={isLoadingProfile}>
            {isLoadingProfile ? 'Loading Profile...' : 'Fetch AngelOne Profile/Funds'}
          </button>
          <button onClick={() => handleFetchAngelData('holdings')} disabled={isLoadingHoldings} style={{marginLeft: '10px'}}>
            {isLoadingHoldings ? 'Loading Holdings...' : 'Fetch AngelOne Holdings'}
          </button>

          {showPinTotpModal && (
            <div className="modal-overlay">
              <div className="modal-content">
                <h4>Enter AngelOne Credentials</h4>
                <p>A new session with AngelOne is required.</p>
                <form onSubmit={handlePinTotpSubmit}>
                  <div>
                    <label htmlFor="pin">PIN/Password:</label>
                    <input type="password" id="pin" value={pin} onChange={(e) => setPin(e.target.value)} required />
                  </div>
                  <div>
                    <label htmlFor="totp">TOTP:</label>
                    <input type="text" id="totp" value={totp} onChange={(e) => setTotp(e.target.value)} required minLength="6" maxLength="6" />
                  </div>
                  <button type="submit">Submit & Retry</button>
                  <button type="button" onClick={() => { setShowPinTotpModal(false); setActionToRetry(null); setError(''); }}>Cancel</button>
                </form>
              </div>
            </div>
          )}

          {angelProfile && (
            <div className="data-section">
              <h4>Profile & Funds</h4>
              <pre>{JSON.stringify(angelProfile, null, 2)}</pre>
            </div>
          )}

          {angelHoldings.length > 0 && (
            <div className="data-section">
              <h4>Holdings</h4>
              <table>
                <thead>
                  <tr>
                    <th>Symbol</th>
                    <th>Exchange</th>
                    <th>Qty</th>
                    <th>Avg. Price</th>
                    <th>LTP</th>
                    <th>P&L</th>
                    <th>Product</th>
                  </tr>
                </thead>
                <tbody>
                  {angelHoldings.map((holding, index) => (
                    <tr key={holding.isin || index}>
                      <td>{holding.tradingsymbol}</td>
                      <td>{holding.exchange}</td>
                      <td>{holding.quantity}</td>
                      <td>{holding.averageprice?.toFixed(2)}</td>
                      <td>{holding.ltp?.toFixed(2)}</td>
                      <td>{holding.pnl?.toFixed(2)}</td>
                      <td>{holding.producttype}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {isLoadingHoldings && angelHoldings.length === 0 && <p>Fetching holdings...</p>}
          {!isLoadingHoldings && angelHoldings.length === 0 && angelProfile && (
            <p>No holdings data found or yet to be fetched.</p>
          )}
        </div>
      )}
    </div>
  );
}

export default Portfolio;
