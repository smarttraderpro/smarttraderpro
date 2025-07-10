import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom'; // Added Link
import { signupUser } from '../api';

function Signup() {
  const [email, setEmail] = useState('');
  const [mobile, setMobile] = useState(''); // Optional
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

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

    try {
      const userData = {
        email,
        password,
        // Only include mobile_number if it's provided
        ...(mobile && { mobile_number: mobile })
      };

      const response = await signupUser(userData); // Calls backend /auth/signup

      // Backend now returns a message like:
      // {"message": "Signup successful. An OTP has been sent to your email for verification.", ...}
      setMessage(response.data.message || "Signup successful. Please check your email to verify your account.");

      // Optionally, clear form or redirect
      // navigate('/verify-account'); // Or provide a link/button
      setEmail('');
      setMobile('');
      setPassword('');
      setConfirmPassword('');

    } catch (err) {
      if (err.response && err.response.data && err.response.data.detail) {
        setError(err.response.data.detail);
      } else {
        setError('Signup failed. Please try again.');
      }
      console.error('Signup error:', err);
    }
  };

  return (
    <div>
      <h2>Signup</h2>
      <form onSubmit={handleSignup}>
        <div>
          <label htmlFor="email">Email:</label>
          <input
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>

        <div>
          <label htmlFor="mobile">Mobile Number (Optional):</label>
          <input
            type="tel"
            id="mobile"
            value={mobile}
            onChange={(e) => setMobile(e.target.value)}
            placeholder="e.g., 1234567890"
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
            minLength="8"
          />
        </div>
        <div>
          <label htmlFor="confirmPassword">Confirm Password:</label>
          <input
            type="password"
            id="confirmPassword"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            minLength="8"
          />
        </div>

        {error && <p style={{ color: 'red' }}>{error}</p>}
        {message && (
          <div>
            <p style={{ color: 'green' }}>{message}</p>
            {/* Add a link to the verification page if signup was successful and requires verification */}
            {message.toLowerCase().includes("otp has been sent") && (
              <p>
                <Link to="/verify-account">Click here to Verify Account</Link>
              </p>
            )}
          </div>
        )}
        <button type="submit">Signup</button>
      </form>
      <p>
        Already have an account? <Link to="/login">Login here</Link>
      </p>
    </div>
  );
}

export default Signup;
