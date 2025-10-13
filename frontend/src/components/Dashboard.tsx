import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  Chip,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  Storage as StorageIcon,
  Cloud as CloudIcon,
  Timeline as TimelineIcon,
} from '@mui/icons-material';
import { api } from '../services/api';

const Dashboard: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<any>(null);
  const [alerts, setAlerts] = useState<any>(null);
  const [services, setServices] = useState<any>(null);

  useEffect(() => {
    loadDashboardData();
    const interval = setInterval(loadDashboardData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [summaryData, alertsData, servicesData] = await Promise.all([
        api.getMetricsSummary(),
        api.getActiveAlerts(),
        api.getServices(),
      ]);

      setSummary(summaryData);
      setAlerts(alertsData);
      setServices(servicesData);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
      setError('Failed to load dashboard data. Please check your connection.');
    } finally {
      setLoading(false);
    }
  };

  if (loading && !summary) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  const StatCard = ({ title, value, icon, color = 'primary' }: any) => (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Box
            sx={{
              p: 1,
              borderRadius: 1,
              backgroundColor: `${color}.main`,
              color: 'white',
              mr: 2,
            }}
          >
            {icon}
          </Box>
          <Typography variant="h6" component="div">
            {title}
          </Typography>
        </Box>
        <Typography variant="h4" component="div" color="text.primary">
          {value}
        </Typography>
      </CardContent>
    </Card>
  );

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Typography variant="h4" gutterBottom>
        System Dashboard
      </Typography>

      <Grid container spacing={3}>
        {/* Statistics Cards */}
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Metrics"
            value={summary?.metrics_count || 0}
            icon={<TimelineIcon />}
            color="primary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Active Services"
            value={services?.total_count || 0}
            icon={<CloudIcon />}
            color="success"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Data Sources"
            value={summary?.connectors?.length || 0}
            icon={<StorageIcon />}
            color="info"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Active Alerts"
            value={alerts?.count || 0}
            icon={<TrendingUpIcon />}
            color={alerts?.count > 0 ? 'error' : 'success'}
          />
        </Grid>

        {/* Services List */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: '400px' }}>
            <Typography variant="h6" gutterBottom>
              Connected Services
            </Typography>
            <Box sx={{ height: '340px', overflow: 'auto' }}>
              {services && Object.keys(services.services).length > 0 ? (
                Object.entries(services.services).map(([connector, servicesList]: [string, any]) => (
                  <Box key={connector} sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" color="primary" gutterBottom>
                      {connector.charAt(0).toUpperCase() + connector.slice(1)}
                    </Typography>
                    <List dense>
                      {servicesList.slice(0, 10).map((service: string, index: number) => (
                        <ListItem key={index} sx={{ py: 0 }}>
                          <ListItemText
                            primary={service}
                            primaryTypographyProps={{ variant: 'body2' }}
                          />
                          <Chip size="small" label="Active" color="success" />
                        </ListItem>
                      ))}
                      {servicesList.length > 10 && (
                        <ListItem>
                          <ListItemText
                            primary={`... and ${servicesList.length - 10} more`}
                            primaryTypographyProps={{ variant: 'caption', style: { fontStyle: 'italic' } }}
                          />
                        </ListItem>
                      )}
                    </List>
                  </Box>
                ))
              ) : (
                <Typography color="text.secondary">
                  No services found. Check your connector configuration.
                </Typography>
              )}
            </Box>
          </Paper>
        </Grid>

        {/* Alerts Panel */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: '400px' }}>
            <Typography variant="h6" gutterBottom>
              Recent Alerts
            </Typography>
            <Box sx={{ height: '340px', overflow: 'auto' }}>
              {alerts && alerts.alerts.length > 0 ? (
                <List>
                  {alerts.alerts.slice(0, 8).map((alert: any, index: number) => (
                    <ListItem key={index} sx={{ flexDirection: 'column', alignItems: 'flex-start' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', width: '100%', mb: 1 }}>
                        <Typography variant="body2" sx={{ flexGrow: 1 }}>
                          {alert.name}
                        </Typography>
                        <Chip
                          size="small"
                          label={alert.severity}
                          color={
                            alert.severity === 'critical' ? 'error' :
                            alert.severity === 'warning' ? 'warning' : 'info'
                          }
                        />
                      </Box>
                      <Typography variant="caption" color="text.secondary">
                        Service: {alert.service}
                      </Typography>
                      {alert.description && (
                        <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
                          {alert.description}
                        </Typography>
                      )}
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Typography color="text.secondary">
                    🎉 No active alerts! Your system is running smoothly.
                  </Typography>
                </Box>
              )}
            </Box>
          </Paper>
        </Grid>

        {/* Data Sources Status */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Data Source Status
            </Typography>
            <Grid container spacing={2}>
              {summary?.connector_summaries && Object.entries(summary.connector_summaries).map(([name, data]: [string, any]) => (
                <Grid item xs={12} sm={6} md={4} key={name}>
                  <Card>
                    <CardContent>
                      <Typography variant="subtitle1" gutterBottom>
                        {name.charAt(0).toUpperCase() + name.slice(1)}
                      </Typography>
                      {data.error ? (
                        <Chip label="Error" color="error" />
                      ) : (
                        <>
                          <Typography variant="body2" color="text.secondary">
                            Services: {data.service_count || 0}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Metrics: {data.metric_count || 0}
                          </Typography>
                          <Chip label="Connected" color="success" size="small" sx={{ mt: 1 }} />
                        </>
                      )}
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;