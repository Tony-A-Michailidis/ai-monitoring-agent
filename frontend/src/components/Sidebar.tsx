import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  Box,
  Typography,
  IconButton,
  Tooltip,
  Chip,
} from '@mui/material';
import {
  Chat as ChatIcon,
  Dashboard as DashboardIcon,
  Warning as AlertIcon,
  Menu as MenuIcon,
  HealthAndSafety as HealthIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';

interface SidebarProps {
  open: boolean;
  onToggle: () => void;
  isHealthy: boolean;
}

const Sidebar: React.FC<SidebarProps> = ({ open, onToggle, isHealthy }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    {
      text: 'Chat Assistant',
      icon: <ChatIcon />,
      path: '/',
      description: 'Conversational monitoring interface',
    },
    {
      text: 'Dashboard',
      icon: <DashboardIcon />,
      path: '/dashboard',
      description: 'System metrics overview',
    },
    {
      text: 'Alerts',
      icon: <AlertIcon />,
      path: '/alerts',
      description: 'Active alerts and notifications',
    },
  ];

  const drawerWidth = open ? 280 : 72;

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
          transition: 'width 0.3s ease',
          backgroundColor: 'background.paper',
          borderRight: '1px solid rgba(255, 255, 255, 0.12)',
        },
      }}
    >
      {/* Header */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          p: 2,
          minHeight: 64,
        }}
      >
        <IconButton onClick={onToggle} sx={{ mr: open ? 2 : 0 }}>
          <MenuIcon />
        </IconButton>
        {open && (
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            AI Monitor
          </Typography>
        )}
      </Box>

      <Divider />

      {/* Status indicator */}
      <Box sx={{ p: open ? 2 : 1 }}>
        {open ? (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <HealthIcon color={isHealthy ? 'success' : 'error'} />
            <Typography variant="body2" color="text.secondary">
              System Status
            </Typography>
            <Chip
              label={isHealthy ? 'Healthy' : 'Issues'}
              color={isHealthy ? 'success' : 'error'}
              size="small"
            />
          </Box>
        ) : (
          <Tooltip title={`System Status: ${isHealthy ? 'Healthy' : 'Issues'}`} placement="right">
            <Box sx={{ display: 'flex', justifyContent: 'center' }}>
              <HealthIcon color={isHealthy ? 'success' : 'error'} />
            </Box>
          </Tooltip>
        )}
      </Box>

      <Divider />

      {/* Navigation menu */}
      <List sx={{ flexGrow: 1, pt: 1 }}>
        {menuItems.map((item) => {
          const isActive = location.pathname === item.path;
          
          return (
            <ListItem key={item.text} disablePadding>
              <ListItemButton
                selected={isActive}
                onClick={() => navigate(item.path)}
                sx={{
                  mx: 1,
                  mb: 0.5,
                  borderRadius: 1,
                  '&.Mui-selected': {
                    backgroundColor: 'primary.main',
                    color: 'primary.contrastText',
                    '& .MuiListItemIcon-root': {
                      color: 'primary.contrastText',
                    },
                  },
                  '&:hover': {
                    backgroundColor: isActive ? 'primary.main' : 'action.hover',
                  },
                }}
              >
                <ListItemIcon
                  sx={{
                    minWidth: open ? 56 : 'auto',
                    justifyContent: 'center',
                  }}
                >
                  {open ? (
                    item.icon
                  ) : (
                    <Tooltip title={item.text} placement="right">
                      {item.icon}
                    </Tooltip>
                  )}
                </ListItemIcon>
                {open && (
                  <ListItemText
                    primary={item.text}
                    secondary={item.description}
                    primaryTypographyProps={{
                      variant: 'body2',
                      fontWeight: isActive ? 600 : 400,
                    }}
                    secondaryTypographyProps={{
                      variant: 'caption',
                      color: isActive ? 'primary.contrastText' : 'text.secondary',
                      sx: { opacity: isActive ? 0.8 : 0.7 },
                    }}
                  />
                )}
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>

      {/* Footer */}
      <Box sx={{ p: open ? 2 : 1 }}>
        <Divider sx={{ mb: 2 }} />
        {open ? (
          <Box>
            <Typography variant="caption" color="text.secondary" display="block">
              AI Monitoring Agent v1.0.0
            </Typography>
            <Typography variant="caption" color="text.secondary" display="block">
              Powered by OpenAI & FastAPI
            </Typography>
          </Box>
        ) : (
          <Tooltip title="Settings" placement="right">
            <IconButton size="small" sx={{ width: '100%' }}>
              <SettingsIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        )}
      </Box>
    </Drawer>
  );
};

export default Sidebar;