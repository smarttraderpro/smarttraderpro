import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { verifyOtp } from '../api'; // Assuming verifyOtp is exported from api.js

function VerifyAccount() {
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');

    if (!email || !otp) {
      setError('Please enter both your email and the OTP.');
      return;
    }

    try {
      // The verifyOtp function in api.js expects (identifier, otp)
      const response = await verifyOtp(email, otp);

      // Backend response upon successful OTP verification and activation:
      // {"message": "Email an***@example.com verified and account activated successfully.", ...}
      setMessage(response.data.message || "Account verified and activated successfully! You can now log in.");

      // Redirect to login page after a short delay or provide a button
      setTimeout(() => {
        navigate('/login');
      }, 3000); // Redirect after 3 seconds

    } catch (err) {
      if (err.response && err.response.data && err.response.data.detail) {
        setError(err.response.data.detail);
      } else {
        setError('OTP verification failed. Please check your OTP or request a new one if needed.');
      }
      console.error('Verify OTP error:', err);
    }
  };

  return (
    <div>
      <h2>Verify Your Account</h2>
      <p>An OTP was sent to your email after signup. Please enter it below to activate your account.</p>
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="email">Email:</label>
          <input
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            placeholder="Enter the email you signed up with"
          />
        </div>
        <div>
          <label htmlFor="otp">OTP:</label>
          <input
            type="text"
            id="otp"
            value={otp}
            onChange={(e) => setOtp(e.target.value)}
            required
            minLength="6" // Assuming OTP is 6 digits
            maxLength="6"
          />
        </div>
        {error && <p style={{ color: 'red' }}>{error}</p>}
        {message && <p style={{ color: 'green' }}>{message}</p>}
        <button type="submit">Verify Account</button>
      </form>
      <p>
        Didn't receive an OTP or it expired? You might need to request it again via a "Resend OTP" feature (not yet implemented) or by trying to log in (which might prompt for verification if the account is inactive). For now, ensure you noted the OTP from the backend console during signup.
      </p>
      <p>
        <Link to="/login">Back to Login</Link>
      </p>
    </div>
  );
}

export default VerifyAccount;
