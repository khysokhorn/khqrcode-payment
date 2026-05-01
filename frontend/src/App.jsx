import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [status, setStatus] = useState('Checking backend...');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(() => {
    fetch('/api/v1/')
      .then(res => res.json())
      .then(data => setStatus('Backend Connected'))
      .catch(err => setStatus('Backend Disconnected'));
  }, []);

  const createTestPayment = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/aba/create-deeplink', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tran_id: `TEST-${Date.now()}`,
          amount: 1.00,
          currency: 'USD',
          firstname: 'Test',
          lastname: 'User',
          email: 'test@example.com',
          items: [{ name: 'Test Product', quantity: 1, price: 1.00 }]
        })
      });
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Error:', error);
      alert('Failed to create payment');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <nav className="navbar">
        <div className="logo">
          <span className="logo-icon">💎</span>
          <span className="logo-text">PayGate</span>
        </div>
        <div className="status-badge">
          <span className={`status-dot ${status === 'Backend Connected' ? 'online' : 'offline'}`}></span>
          {status}
        </div>
      </nav>

      <main>
        <section className="hero">
          <h1 className="gradient-text">Modern Payment Infrastructure</h1>
          <p className="subtitle">Seamlessly integrate ABA PayWay and KHQR into your applications with our robust microservice.</p>
        </section>

        <div className="glass-card main-card">
          {!result ? (
            <div className="empty-state">
              <h3>Test Integration</h3>
              <p>Click the button below to generate a test ABA Deep Link payment.</p>
              <button onClick={createTestPayment} disabled={loading}>
                {loading ? 'Creating...' : 'Generate Test Payment'}
              </button>
            </div>
          ) : (
            <div className="result-container">
              <div className="success-header">
                <h3>Payment Link Generated</h3>
                <button className="secondary" onClick={() => setResult(null)}>New Test</button>
              </div>
              
              <div className="payment-details">
                <div className="detail-item">
                  <label>Transaction ID</label>
                  <span>{result.tran_id || 'N/A'}</span>
                </div>
                <div className="detail-item">
                  <label>Status</label>
                  <span className="badge-success">Ready</span>
                </div>
              </div>

              {result.abapay_deeplink && (
                <div className="deeplink-section">
                  <p>Open in ABA Mobile:</p>
                  <a href={result.abapay_deeplink} className="deeplink-button">
                    Open ABA Mobile
                  </a>
                </div>
              )}

              {result.app_deeplink && (
                <div className="qr-section">
                   <p>Payment URL:</p>
                   <code className="url-box">{result.app_deeplink}</code>
                </div>
              )}
            </div>
          )}
        </div>

        <section className="features">
          <div className="feature-card">
            <h4>ABA PayWay</h4>
            <p>Direct deep linking for the best mobile user experience.</p>
          </div>
          <div className="feature-card">
            <h4>KHQR Ready</h4>
            <p>Universal QR codes compliant with Bakong standards.</p>
          </div>
          <div className="feature-card">
            <h4>PostgreSQL</h4>
            <p>Reliable transaction tracking with persistent storage.</p>
          </div>
        </section>
      </main>

      <footer>
        <p>&copy; 2024 PayGate Microservice. All rights reserved.</p>
      </footer>
    </div>
  );
}

export default App;
