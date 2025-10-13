import React, { useState, useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';
import {
  Box,
  AppBar,
  Toolbar,
  Typography,
  Container,
  Alert,
  Snackbar,
} from '@mui/material';
import ChatInterface from './components/ChatInterface';
import Dashboard from './components/Dashboard';
import AlertsPanel from './components/AlertsPanel';
import Sidebar from './components/Sidebar';
import { api } from './services/api';

interface HealthStatus {
  status: string;
  services: Record<string, string>;
}

function App() {
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const checkHealth = async () => {
    try {
      const health = await api.getHealth();
      setHealthStatus(health);
      if (error) setError(null); // Clear error if health check succeeds
    } catch (err) {
      console.error('Health check failed:', err);
      setError('Unable to connect to monitoring backend');
    }
  };

  const handleCloseError = () => {
    setError(null);
  };

  const isHealthy = healthStatus?.status === 'healthy';

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      {/* Sidebar */}
      <Sidebar 
        open={sidebarOpen} 
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        isHealthy={isHealthy}
      />

      {/* Main content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          display: 'flex',
          flexDirection: 'column',
          transition: 'margin-left 0.3s',
          marginLeft: sidebarOpen ? '280px' : '72px',
        }}
      >
        {/* Header */}
        <AppBar 
          position="sticky" 
          sx={{ 
            backgroundColor: 'background.paper',
            borderBottom: '1px solid rgba(255, 255, 255, 0.12)',
          }}
        >
          <Toolbar>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1, color: 'text.primary' }}>
              AI Monitoring Agent
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography variant="body2" color="text.secondary">
                Status:
              </Typography>
              <Box
                sx={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  backgroundColor: isHealthy ? 'success.main' : 'error.main',
                }}
              />
              <Typography variant="body2" color={isHealthy ? 'success.main' : 'error.main'}>
                {healthStatus?.status || 'Unknown'}
              </Typography>
            </Box>
          </Toolbar>
        </AppBar>

        {/* Content area */}
        <Container 
          maxWidth="xl" 
          sx={{ 
            flexGrow: 1, 
            py: 3,
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          <Routes>
            <Route path="/" element={<ChatInterface />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/alerts" element={<AlertsPanel />} />
          </Routes>
        </Container>
      </Box>

      {/* Error snackbar */}
      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={handleCloseError}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseError} severity="error" sx={{ width: '100%' }}>
          {error}
        </Alert>
      </Snackbar>
    </Box>
  );
}

export default App;