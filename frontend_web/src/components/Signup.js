import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { signupUser, sendOtp, verifyOtp as verifyOtpApi } from '../api'; // Renamed verifyOtp to avoid conflict

function Signup() {
  const [email, setEmail] = useState('');
  const [mobile, setMobile] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const [otp, setOtp] = useState('');
  const [otpSentTo, setOtpSentTo] = useState(''); // 'email' or 'mobile'
  const [otpVerifiedFor, setOtpVerifiedFor] = useState(''); // 'email' or 'mobile' after successful verification

  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSignup = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    if (!otpVerifiedFor) { // Check if primary identifier (e.g. email) is OTP verified
        setError("Please verify your email or mobile with OTP before signing up.");
        return;
    }

    try {
      const userData = { email, password };
      if (mobile) {
        userData.mobile_number = mobile;
      }

      const response = await signupUser(userData);
      setMessage(`Signup successful for ${response.data.email}! You can now login.`);
      // navigate('/login'); // Or auto-login and redirect to dashboard
    } catch (err) {
      if (err.response && err.response.data && err.response.data.detail) {
        setError(err.response.data.detail);
      } else {
        setError('Signup failed. Please try again.');
      }
      console.error('Signup error:', err);
    }
  };

  const handleSendOtp = async (identifierType) => {
    setError('');
    setMessage('');
    const identifierValue = identifierType === 'email' ? email : mobile;
    if (!identifierValue) {
        setError(`Please enter your ${identifierType} first.`);
        return;
    }
    try {
        await sendOtp(identifierValue);
        setOtpSentTo(identifierType);
        setMessage(`OTP sent to your ${identifierType}. Please check and enter below.`);
    } catch (err) {
        if (err.response && err.response.data && err.response.data.detail) {
            setError(err.response.data.detail);
          } else {
            setError(`Failed to send OTP to ${identifierType}.`);
          }
        console.error('Send OTP error:', err);
    }
  };

  const handleVerifyOtp = async () => {
    setError('');
    setMessage('');
    if (!otpSentTo || !otp) {
        setError("Please request and enter OTP first.");
        return;
    }
    const identifierValue = otpSentTo === 'email' ? email : mobile;
    try {
        await verifyOtpApi(identifierValue, otp); // Using verifyOtpApi
        setOtpVerifiedFor(otpSentTo);
        setMessage(`${otpSentTo.charAt(0).toUpperCase() + otpSentTo.slice(1)} verified successfully! You can now complete signup.`);
        setOtp(''); // Clear OTP field
        setOtpSentTo(''); // Reset otpSentTo
    } catch (err) {
        if (err.response && err.response.data && err.response.data.detail) {
            setError(err.response.data.detail);
          } else {
            setError("OTP verification failed.");
          }
        console.error('Verify OTP error:', err);
    }
  }

  return (
    <div>
      <h2>Signup</h2>
      <form onSubmit={handleSignup}>
        <div>
          <label htmlFor="email">Email:</label>
          <input type="email" id="email" value={email} onChange={(e) => setEmail(e.target.value)} required disabled={otpVerifiedFor === 'email'}/>
          {otpSentTo !== 'email' && otpVerifiedFor !== 'email' && <button type="button" onClick={() => handleSendOtp('email')}>Send OTP to Email</button>}
          {otpVerifiedFor === 'email' && <span> (Verified)</span>}
        </div>

        {otpSentTo === 'email' && otpVerifiedFor !== 'email' && (
            <div>
                <label htmlFor="otpEmail">Email OTP:</label>
                <input type="text" id="otpEmail" value={otp} onChange={(e) => setOtp(e.target.value)} />
                <button type="button" onClick={handleVerifyOtp}>Verify Email OTP</button>
            </div>
        )}

        <div>
          <label htmlFor="mobile">Mobile Number (Optional):</label>
          <input type="tel" id="mobile" value={mobile} onChange={(e) => setMobile(e.target.value)} disabled={otpVerifiedFor === 'mobile'}/>
          {/* Basic OTP for mobile if provided and not yet verified */}
          {/* More complex logic needed if mobile is also a primary verification method */}
        </div>

        <div>
          <label htmlFor="password">Password:</label>
          <input type="password" id="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </div>
        <div>
          <label htmlFor="confirmPassword">Confirm Password:</label>
          <input type="password" id="confirmPassword" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required />
        </div>

        {error && <p style={{ color: 'red' }}>{error}</p>}
        {message && <p style={{ color: 'green' }}>{message}</p>}
        <button type="submit" disabled={!otpVerifiedFor}>Signup</button>
      </form>
    </div>
  );
}

export default Signup;
