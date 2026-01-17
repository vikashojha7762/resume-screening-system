import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Switch,
  FormControlLabel,
  Divider,
  Grid,
  Button,
  TextField,
  Alert,
} from '@mui/material';
import { Save as SaveIcon } from '@mui/icons-material';
import { useAppDispatch, useAppSelector } from '../store/hooks';
import { toggleTheme, setTheme } from '../store/slices/uiSlice';
import { toast } from 'react-toastify';

const Settings: React.FC = () => {
  const dispatch = useAppDispatch();
  const { theme, sidebarOpen } = useAppSelector((state) => state.ui);
  const { user } = useAppSelector((state) => state.auth);
  const [notifications, setNotifications] = useState(true);
  const [emailNotifications, setEmailNotifications] = useState(true);

  const handleThemeToggle = () => {
    dispatch(toggleTheme());
    toast.success(`Theme changed to ${theme === 'light' ? 'dark' : 'light'} mode`);
  };

  const handleSave = () => {
    // Save settings logic here
    toast.success('Settings saved successfully');
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>

      <Grid container spacing={3} sx={{ mt: 2 }}>
        {/* Appearance Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Appearance
              </Typography>
              <Divider sx={{ my: 2 }} />
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={theme === 'dark'}
                      onChange={handleThemeToggle}
                      color="primary"
                    />
                  }
                  label="Dark Mode"
                />
                <Typography variant="body2" color="text.secondary">
                  Toggle between light and dark theme
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Notification Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Notifications
              </Typography>
              <Divider sx={{ my: 2 }} />
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={notifications}
                      onChange={(e) => setNotifications(e.target.checked)}
                      color="primary"
                    />
                  }
                  label="Enable Notifications"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={emailNotifications}
                      onChange={(e) => setEmailNotifications(e.target.checked)}
                      color="primary"
                      disabled={!notifications}
                    />
                  }
                  label="Email Notifications"
                />
                <Typography variant="body2" color="text.secondary">
                  Receive notifications about job matches and updates
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Account Information */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Account Information
              </Typography>
              <Divider sx={{ my: 2 }} />
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Email"
                    value={user?.email || ''}
                    disabled
                    variant="outlined"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="User ID"
                    value={user?.id || ''}
                    disabled
                    variant="outlined"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Account Status"
                    value={user?.is_active ? 'Active' : 'Inactive'}
                    disabled
                    variant="outlined"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Role"
                    value={user?.is_superuser ? 'Superuser' : 'User'}
                    disabled
                    variant="outlined"
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* System Information */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Information
              </Typography>
              <Divider sx={{ my: 2 }} />
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Typography variant="body2">
                  <strong>Application Version:</strong> 1.0.0
                </Typography>
                <Typography variant="body2">
                  <strong>Environment:</strong> Development
                </Typography>
                <Typography variant="body2">
                  <strong>API URL:</strong> {import.meta.env.VITE_API_URL || 'http://localhost:8000'}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Save Button */}
        <Grid item xs={12}>
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
            <Button
              variant="contained"
              startIcon={<SaveIcon />}
              onClick={handleSave}
            >
              Save Settings
            </Button>
          </Box>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Settings;

