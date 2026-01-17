import React, { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  List,
  Typography,
  Divider,
  IconButton,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Avatar,
  Menu,
  MenuItem,
  Breadcrumbs,
  Link,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  Work as WorkIcon,
  Description as DescriptionIcon,
  People as PeopleIcon,
  Settings as SettingsIcon,
  Brightness4,
  Brightness7,
  AccountCircle,
  Logout,
} from '@mui/icons-material';
import { useAppDispatch, useAppSelector } from '../../store/hooks';
import { toggleTheme, toggleSidebar } from '../../store/slices/uiSlice';
import { logout, getCurrentUser } from '../../store/slices/authSlice';
import { useEffect } from 'react';

const drawerWidth = 240;

const DashboardLayout: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useAppDispatch();
  const { theme: appTheme, sidebarOpen } = useAppSelector((state) => state.ui);
  const { user } = useAppSelector((state) => state.auth);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  useEffect(() => {
    dispatch(getCurrentUser());
  }, [dispatch]);

  const menuItems = [
    { text: 'Dashboard', icon: <DashboardIcon />, path: '/dashboard' },
    { text: 'Jobs', icon: <WorkIcon />, path: '/dashboard/jobs' },
    { text: 'Resumes', icon: <DescriptionIcon />, path: '/dashboard/resumes' },
    { text: 'Candidates', icon: <PeopleIcon />, path: '/dashboard/candidates' },
    { text: 'Settings', icon: <SettingsIcon />, path: '/dashboard/settings' },
  ];

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    dispatch(logout());
    navigate('/login');
    handleMenuClose();
  };

  const getBreadcrumbs = () => {
    const paths = location.pathname.split('/').filter((x) => x);
    const breadcrumbs = [{ label: 'Home', path: '/dashboard' }];

    paths.forEach((path, index) => {
      if (path !== 'dashboard') {
        breadcrumbs.push({
          label: path.charAt(0).toUpperCase() + path.slice(1),
          path: '/' + paths.slice(0, index + 1).join('/'),
        });
      }
    });

    return breadcrumbs;
  };

  const drawer = (
    <Box>
      <Toolbar>
        <Typography variant="h6" noWrap component="div">
          Resume Screening
        </Typography>
      </Toolbar>
      <Divider />
      <List>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => navigate(item.path)}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar
        position="fixed"
        sx={{
          zIndex: (theme) => theme.zIndex.drawer + 1,
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            edge="start"
            onClick={() => dispatch(toggleSidebar())}
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            Resume Screening System
          </Typography>
          <IconButton color="inherit" onClick={() => dispatch(toggleTheme())}>
            {appTheme === 'dark' ? <Brightness7 /> : <Brightness4 />}
          </IconButton>
          <IconButton color="inherit" onClick={handleMenuOpen}>
            <Avatar sx={{ width: 32, height: 32 }}>
              {user?.email.charAt(0).toUpperCase()}
            </Avatar>
          </IconButton>
          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleMenuClose}
          >
            <MenuItem disabled>
              <AccountCircle sx={{ mr: 1 }} />
              {user?.email}
            </MenuItem>
            <Divider />
            <MenuItem onClick={handleLogout}>
              <Logout sx={{ mr: 1 }} />
              Logout
            </MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>
      <Drawer
        variant={isMobile ? 'temporary' : 'persistent'}
        open={sidebarOpen}
        onClose={() => dispatch(toggleSidebar())}
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
          },
        }}
      >
        {drawer}
      </Drawer>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { sm: `calc(100% - ${drawerWidth}px)` },
        }}
      >
        <Toolbar />
        <Breadcrumbs sx={{ mb: 2 }}>
          {getBreadcrumbs().map((crumb, index) => (
            <Link
              key={index}
              color="inherit"
              href={crumb.path}
              onClick={(e) => {
                e.preventDefault();
                navigate(crumb.path);
              }}
            >
              {crumb.label}
            </Link>
          ))}
        </Breadcrumbs>
        <Outlet />
      </Box>
    </Box>
  );
};

export default DashboardLayout;

