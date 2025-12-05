import React, { useEffect, useState } from 'react';

const AdminDashboard: React.FC = () => {
  const [logs, setLogs] = useState<string[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    const source = new EventSource('http://localhost:8000/api/admin/logs/stream', {
      withCredentials: true,
    });

    source.onmessage = (event) => {
      setLogs((prev) => [...prev, event.data].slice(-200));
    };

    source.onerror = () => {
      setError('Failed to connect to log stream');
      source.close();
    };

    return () => {
      source.close();
    };
  }, []);

  return (
    <div style={{ padding: '1rem' }}>
      <h1>Admin Dashboard</h1>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <div
        style={{
          height: '70vh',
          overflowY: 'scroll',
          background: '#1e1e1e',
          color: '#d4d4d4',
          padding: '1rem',
          fontFamily: 'monospace',
        }}
      >
        {logs.map((line, idx) => (
          <div key={idx}>{line}</div>
        ))}
      </div>
    </div>
  );
};

export default AdminDashboard;
