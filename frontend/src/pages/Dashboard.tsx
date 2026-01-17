import React, { useEffect } from 'react';
import { Grid, Card, CardContent, Typography, Box, CircularProgress } from '@mui/material';
import {
  Work as WorkIcon,
  Description as DescriptionIcon,
  People as PeopleIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';
import { useAppSelector, useAppDispatch } from '../store/hooks';
import { fetchJobs } from '../store/slices/jobsSlice';
import { fetchResumes } from '../store/slices/resumesSlice';

const Dashboard: React.FC = () => {
  const dispatch = useAppDispatch();
  const { jobs, isLoading: jobsLoading } = useAppSelector((state) => state.jobs);
  const { resumes, isLoading: resumesLoading } = useAppSelector((state) => state.resumes);
  const { matchResults } = useAppSelector((state) => state.candidates);
  const { isAuthenticated } = useAppSelector((state) => state.auth);

  // Fetch data when component mounts or when authentication state changes
  // This ensures data is loaded immediately after login
  useEffect(() => {
    if (isAuthenticated) {
      // Fetch data immediately after login or when component mounts
      // This handles the case where user logs out and logs back in
      dispatch(fetchJobs({ page: 1, pageSize: 100 }));
      dispatch(fetchResumes({ page: 1, pageSize: 100 }));
    }
  }, [dispatch, isAuthenticated]); // Trigger when authentication state changes (e.g., after login)

  const stats = [
    {
      title: 'Active Jobs',
      value: jobs.filter((j) => j.status === 'active').length,
      icon: <WorkIcon />,
      color: '#1976d2',
    },
    {
      title: 'Total Resumes',
      value: resumes.length,
      icon: <DescriptionIcon />,
      color: '#2e7d32',
    },
    {
      title: 'Candidates Matched',
      value: matchResults.length,
      icon: <PeopleIcon />,
      color: '#ed6c02',
    },
    {
      title: 'Avg Match Score',
      value:
        matchResults.length > 0
          ? (
              matchResults.reduce((sum, r) => sum + Number(r.overall_score), 0) /
              matchResults.length
            ).toFixed(1)
          : '0.0',
      icon: <TrendingUpIcon />,
      color: '#9c27b0',
    },
  ];

  // Show loading state while data is being fetched
  const isLoading = jobsLoading || resumesLoading;

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      {isLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '200px' }}>
          <CircularProgress />
        </Box>
      ) : (
        <Grid container spacing={3}>
          {stats.map((stat, index) => (
            <Grid item xs={12} sm={6} md={3} key={index}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Box
                      sx={{
                        backgroundColor: `${stat.color}20`,
                        borderRadius: '50%',
                        p: 1,
                        mr: 2,
                      }}
                    >
                      <Box sx={{ color: stat.color }}>{stat.icon}</Box>
                    </Box>
                    <Box>
                      <Typography variant="h4">{stat.value}</Typography>
                      <Typography variant="body2" color="text.secondary">
                        {stat.title}
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  );
};

export default Dashboard;

