import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  Chip,
  Alert,
  CircularProgress,
  Grid,
  Card,
  CardContent,
  Button,
  IconButton,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { api, AlertData } from '../services/api';

const AlertsPanel: React.FC = () => {
  const [alerts, setAlerts] = useState<AlertData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  useEffect(() => {
    loadAlerts();
    const interval = setInterval(loadAlerts, 15000); // Refresh every 15 seconds
    return () => clearInterval(interval);
  }, []);

  const loadAlerts = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await api.getActiveAlerts();
      setAlerts(response.alerts);
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Failed to load alerts:', err);
      setError('Failed to load alerts. Please check your connection.');
    } finally {
      setLoading(false);
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return <ErrorIcon color="error" />;
      case 'warning':
        return <WarningIcon color="warning" />;
      default:
        return <InfoIcon color="info" />;
    }
  };

  const getSeverityColor = (severity: string): "error" | "warning" | "info" => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return 'error';
      case 'warning':
        return 'warning';
      default:
        return 'info';
    }
  };

  const groupedAlerts = alerts.reduce((acc, alert) => {
    if (!acc[alert.severity]) {
      acc[alert.severity] = [];
    }
    acc[alert.severity].push(alert);
    return acc;
  }, {} as Record<string, AlertData[]>);

  const totalCritical = groupedAlerts.critical?.length || 0;
  const totalWarning = groupedAlerts.warning?.length || 0;
  const totalInfo = groupedAlerts.info?.length || 0;

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Box sx={{ display: 'flex', justifyContent: 'between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          Active Alerts
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          {lastUpdated && (
            <Typography variant="body2" color="text.secondary">
              Last updated: {lastUpdated.toLocaleTimeString()}
            </Typography>
          )}
          <IconButton onClick={loadAlerts} disabled={loading}>
            <RefreshIcon />
          </IconButton>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Summary Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <ErrorIcon color="error" sx={{ mr: 1 }} />
                <Typography variant="h6">Critical</Typography>
              </Box>
              <Typography variant="h3" color="error">
                {totalCritical}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <WarningIcon color="warning" sx={{ mr: 1 }} />
                <Typography variant="h6">Warning</Typography>
              </Box>
              <Typography variant="h3" color="warning.main">
                {totalWarning}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <InfoIcon color="info" sx={{ mr: 1 }} />
                <Typography variant="h6">Info</Typography>
              </Box>
              <Typography variant="h3" color="info.main">
                {totalInfo}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Alerts List */}
      <Paper sx={{ p: 2 }}>
        {loading && alerts.length === 0 ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : alerts.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 6 }}>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              🎉 No Active Alerts
            </Typography>
            <Typography color="text.secondary">
              Your system is running smoothly with no active alerts.
            </Typography>
          </Box>
        ) : (
          <Box>
            <Typography variant="h6" gutterBottom>
              All Active Alerts ({alerts.length})
            </Typography>
            
            {/* Group alerts by severity */}
            {['critical', 'warning', 'info'].map((severity) => {
              const severityAlerts = groupedAlerts[severity];
              if (!severityAlerts || severityAlerts.length === 0) return null;

              return (
                <Box key={severity} sx={{ mb: 3 }}>
                  <Typography variant="subtitle1" sx={{ mb: 2, display: 'flex', alignItems: 'center' }}>
                    {getSeverityIcon(severity)}
                    <Box sx={{ ml: 1 }}>
                      {severity.charAt(0).toUpperCase() + severity.slice(1)} ({severityAlerts.length})
                    </Box>
                  </Typography>
                  
                  <List>
                    {severityAlerts.map((alert, index) => (
                      <ListItem
                        key={`${alert.name}-${index}`}
                        sx={{
                          border: '1px solid',
                          borderColor: 'divider',
                          borderRadius: 1,
                          mb: 1,
                          backgroundColor: 'background.paper',
                        }}
                      >
                        <ListItemText
                          primary={
                            <Box sx={{ display: 'flex', justifyContent: 'between', alignItems: 'center', mb: 1 }}>
                              <Typography variant="subtitle1" component="div">
                                {alert.name}
                              </Typography>
                              <Chip
                                size="small"
                                label={alert.severity}
                                color={getSeverityColor(alert.severity)}
                              />
                            </Box>
                          }
                          secondary={
                            <Box>
                              {alert.description && (
                                <Typography variant="body2" color="text.primary" sx={{ mb: 1 }}>
                                  {alert.description}
                                </Typography>
                              )}
                              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                                <Typography variant="caption" color="text.secondary">
                                  Service: {alert.service}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  Time: {new Date(alert.timestamp).toLocaleString()}
                                </Typography>
                              </Box>
                              {alert.labels && Object.keys(alert.labels).length > 0 && (
                                <Box sx={{ mt: 1, display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                  {Object.entries(alert.labels).slice(0, 5).map(([key, value]) => (
                                    <Chip
                                      key={key}
                                      label={`${key}: ${value}`}
                                      size="small"
                                      variant="outlined"
                                    />
                                  ))}
                                </Box>
                              )}
                            </Box>
                          }
                        />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              );
            })}
          </Box>
        )}
      </Paper>
    </Box>
  );
};

export default AlertsPanel;