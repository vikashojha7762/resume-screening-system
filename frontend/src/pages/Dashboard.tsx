import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  CircularProgress,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Chip,
  Paper,
  Avatar,
  LinearProgress,
} from '@mui/material';
import {
  Work as WorkIcon,
  Description as DescriptionIcon,
  People as PeopleIcon,
  TrendingUp as TrendingUpIcon,
  Add as AddIcon,
  ArrowForward as ArrowForwardIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { useAppSelector, useAppDispatch } from '../store/hooks';
import { fetchJobs } from '../store/slices/jobsSlice';
import { fetchResumes } from '../store/slices/resumesSlice';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { jobs, isLoading: jobsLoading } = useAppSelector((state) => state.jobs);
  const { resumes, isLoading: resumesLoading } = useAppSelector((state) => state.resumes);
  const { matchResults } = useAppSelector((state) => state.candidates);
  const { isAuthenticated } = useAppSelector((state) => state.auth);

  useEffect(() => {
    if (isAuthenticated) {
      dispatch(fetchJobs({ page: 1, pageSize: 100 }));
      dispatch(fetchResumes({ page: 1, pageSize: 100 }));
    }
  }, [dispatch, isAuthenticated]);

  const stats = [
    {
      title: 'Active Jobs',
      value: jobs.filter((j) => j.status === 'active').length,
      icon: <WorkIcon />,
      color: '#1976d2',
      gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      bgColor: 'rgba(102, 126, 234, 0.1)',
    },
    {
      title: 'Total Resumes',
      value: resumes.length,
      icon: <DescriptionIcon />,
      color: '#2e7d32',
      gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
      bgColor: 'rgba(245, 87, 108, 0.1)',
    },
    {
      title: 'Candidates Matched',
      value: matchResults.length,
      icon: <PeopleIcon />,
      color: '#ed6c02',
      gradient: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
      bgColor: 'rgba(79, 172, 254, 0.1)',
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
      gradient: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
      bgColor: 'rgba(250, 112, 154, 0.1)',
      suffix: '%',
    },
  ];

  const isLoading = jobsLoading || resumesLoading;
  const recentJobs = jobs.slice(0, 5);
  const recentResumes = resumes.slice(0, 5);
  const shortlistedCandidates = matchResults.filter((r) => r.shortlisted).slice(0, 5);

  return (
    <Box sx={{ width: '100%', height: '100%' }}>
      {/* Welcome Section */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom sx={{ fontWeight: 700, color: 'text.primary' }}>
          Welcome Back! 👋
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          Here's what's happening with your recruitment process today.
        </Typography>
      </Box>

      {/* Quick Actions */}
      <Box sx={{ mb: 4, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => navigate('/dashboard/jobs/new')}
          sx={{
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            boxShadow: '0 4px 15px rgba(102, 126, 234, 0.4)',
            '&:hover': {
              background: 'linear-gradient(135deg, #764ba2 0%, #667eea 100%)',
              boxShadow: '0 6px 20px rgba(102, 126, 234, 0.6)',
            },
          }}
        >
          Create New Job
        </Button>
        <Button
          variant="outlined"
          startIcon={<DescriptionIcon />}
          onClick={() => navigate('/dashboard/resumes')}
          sx={{
            borderColor: '#667eea',
            color: '#667eea',
            '&:hover': {
              borderColor: '#764ba2',
              backgroundColor: 'rgba(102, 126, 234, 0.08)',
            },
          }}
        >
          Upload Resume
        </Button>
        <Button
          variant="outlined"
          startIcon={<PeopleIcon />}
          onClick={() => navigate('/dashboard/candidates')}
          sx={{
            borderColor: '#4facfe',
            color: '#4facfe',
            '&:hover': {
              borderColor: '#00f2fe',
              backgroundColor: 'rgba(79, 172, 254, 0.08)',
            },
          }}
        >
          View Candidates
        </Button>
      </Box>

      {isLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          {/* Stats Cards */}
          <Grid container spacing={3} sx={{ mb: 4 }}>
            {stats.map((stat, index) => (
              <Grid item xs={12} sm={6} md={3} key={index}>
                <Card
                  sx={{
                    height: '100%',
                    background: stat.gradient,
                    color: 'white',
                    position: 'relative',
                    overflow: 'hidden',
                    boxShadow: '0 8px 24px rgba(0, 0, 0, 0.12)',
                    transition: 'transform 0.3s ease, box-shadow 0.3s ease',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: '0 12px 32px rgba(0, 0, 0, 0.18)',
                    },
                  }}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Box
                        sx={{
                          backgroundColor: 'rgba(255, 255, 255, 0.2)',
                          borderRadius: '12px',
                          p: 1.5,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                        }}
                      >
                        {React.cloneElement(stat.icon, { sx: { fontSize: 28 } })}
                      </Box>
                    </Box>
                    <Typography variant="h3" sx={{ fontWeight: 700, mb: 0.5 }}>
                      {stat.value}
                      {stat.suffix || ''}
                    </Typography>
                    <Typography variant="body2" sx={{ opacity: 0.9, fontWeight: 500 }}>
                      {stat.title}
                    </Typography>
                  </CardContent>
                  <Box
                    sx={{
                      position: 'absolute',
                      bottom: 0,
                      left: 0,
                      right: 0,
                      height: '4px',
                      background: 'rgba(255, 255, 255, 0.3)',
                    }}
                  />
                </Card>
              </Grid>
            ))}
          </Grid>

          {/* Main Content Grid */}
          <Grid container spacing={3}>
            {/* Recent Jobs */}
            <Grid item xs={12} md={6}>
              <Card
                sx={{
                  height: '100%',
                  boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
                  borderRadius: '12px',
                }}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                    <Typography variant="h6" sx={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: 1 }}>
                      <WorkIcon color="primary" />
                      Recent Jobs
                    </Typography>
                    <Button
                      size="small"
                      endIcon={<ArrowForwardIcon />}
                      onClick={() => navigate('/dashboard/jobs')}
                    >
                      View All
                    </Button>
                  </Box>
                  {recentJobs.length === 0 ? (
                    <Box sx={{ textAlign: 'center', py: 4 }}>
                      <WorkIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                      <Typography variant="body2" color="text.secondary">
                        No jobs yet. Create your first job posting!
                      </Typography>
                    </Box>
                  ) : (
                    <List sx={{ p: 0 }}>
                      {recentJobs.map((job) => (
                        <ListItem
                          key={job.id}
                          sx={{
                            borderBottom: '1px solid',
                            borderColor: 'divider',
                            '&:last-child': { borderBottom: 'none' },
                            '&:hover': { backgroundColor: 'action.hover', cursor: 'pointer' },
                          }}
                          onClick={() => navigate(`/dashboard/jobs/${job.id}`)}
                        >
                          <ListItemText
                            primary={
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                                <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                                  {job.title}
                                </Typography>
                                <Chip
                                  label={job.status}
                                  size="small"
                                  color={job.status === 'active' ? 'success' : 'default'}
                                  sx={{ height: 20, fontSize: '0.7rem' }}
                                />
                              </Box>
                            }
                            secondary={
                              <Typography variant="caption" color="text.secondary">
                                Created {new Date(job.created_at).toLocaleDateString()}
                              </Typography>
                            }
                          />
                          <ListItemSecondaryAction>
                            <ArrowForwardIcon sx={{ color: 'text.secondary', fontSize: 20 }} />
                          </ListItemSecondaryAction>
                        </ListItem>
                      ))}
                    </List>
                  )}
                </CardContent>
              </Card>
            </Grid>

            {/* Recent Resumes */}
            <Grid item xs={12} md={6}>
              <Card
                sx={{
                  height: '100%',
                  boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
                  borderRadius: '12px',
                }}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                    <Typography variant="h6" sx={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: 1 }}>
                      <DescriptionIcon color="primary" />
                      Recent Resumes
                    </Typography>
                    <Button
                      size="small"
                      endIcon={<ArrowForwardIcon />}
                      onClick={() => navigate('/dashboard/resumes')}
                    >
                      View All
                    </Button>
                  </Box>
                  {recentResumes.length === 0 ? (
                    <Box sx={{ textAlign: 'center', py: 4 }}>
                      <DescriptionIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                      <Typography variant="body2" color="text.secondary">
                        No resumes uploaded yet. Upload your first resume!
                      </Typography>
                    </Box>
                  ) : (
                    <List sx={{ p: 0 }}>
                      {recentResumes.map((resume) => (
                        <ListItem
                          key={resume.id}
                          sx={{
                            borderBottom: '1px solid',
                            borderColor: 'divider',
                            '&:last-child': { borderBottom: 'none' },
                            '&:hover': { backgroundColor: 'action.hover', cursor: 'pointer' },
                          }}
                        >
                          <Avatar
                            sx={{
                              bgcolor: 'primary.main',
                              mr: 2,
                              width: 40,
                              height: 40,
                            }}
                          >
                            <DescriptionIcon />
                          </Avatar>
                          <ListItemText
                            primary={
                              <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                                {resume.file_name || 'Untitled Resume'}
                              </Typography>
                            }
                            secondary={
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                                <Chip
                                  label={resume.status || 'uploaded'}
                                  size="small"
                                  color={
                                    resume.status === 'processed'
                                      ? 'success'
                                      : resume.status === 'processing'
                                        ? 'warning'
                                        : 'default'
                                  }
                                  sx={{ height: 18, fontSize: '0.65rem' }}
                                />
                                <Typography variant="caption" color="text.secondary">
                                  {new Date(resume.created_at).toLocaleDateString()}
                                </Typography>
                              </Box>
                            }
                          />
                        </ListItem>
                      ))}
                    </List>
                  )}
                </CardContent>
              </Card>
            </Grid>

            {/* Shortlisted Candidates */}
            {shortlistedCandidates.length > 0 && (
              <Grid item xs={12}>
                <Card
                  sx={{
                    boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
                    borderRadius: '12px',
                  }}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                      <Typography variant="h6" sx={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: 1 }}>
                        <CheckCircleIcon color="success" />
                        Shortlisted Candidates
                      </Typography>
                      <Button
                        size="small"
                        endIcon={<ArrowForwardIcon />}
                        onClick={() => navigate('/dashboard/candidates')}
                      >
                        View All
                      </Button>
                    </Box>
                    <Grid container spacing={2}>
                      {shortlistedCandidates.map((candidate) => (
                        <Grid item xs={12} sm={6} md={4} key={candidate.id}>
                          <Paper
                            sx={{
                              p: 2,
                              border: '1px solid',
                              borderColor: 'divider',
                              borderRadius: '8px',
                              '&:hover': {
                                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
                                cursor: 'pointer',
                              },
                            }}
                            onClick={() => navigate(`/dashboard/candidates/${candidate.candidate_id}`)}
                          >
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                              <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                                {candidate.candidate_name || candidate.anonymized_id || 'Anonymous'}
                              </Typography>
                              <Chip
                                label={`#${candidate.rank || 'N/A'}`}
                                size="small"
                                color="primary"
                                sx={{ height: 20 }}
                              />
                            </Box>
                            <Box sx={{ mt: 2 }}>
                              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                <Typography variant="caption" color="text.secondary">
                                  Match Score
                                </Typography>
                                <Typography variant="caption" sx={{ fontWeight: 600 }}>
                                  {Number(candidate.overall_score).toFixed(1)}%
                                </Typography>
                              </Box>
                              <LinearProgress
                                variant="determinate"
                                value={Number(candidate.overall_score)}
                                sx={{
                                  height: 6,
                                  borderRadius: 3,
                                  backgroundColor: 'rgba(0, 0, 0, 0.1)',
                                  '& .MuiLinearProgress-bar': {
                                    borderRadius: 3,
                                    background: 'linear-gradient(90deg, #667eea 0%, #764ba2 100%)',
                                  },
                                }}
                              />
                            </Box>
                            {candidate.resume_file_name && (
                              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                                {candidate.resume_file_name}
                              </Typography>
                            )}
                          </Paper>
                        </Grid>
                      ))}
                    </Grid>
                  </CardContent>
                </Card>
              </Grid>
            )}

            {/* Performance Overview */}
            <Grid item xs={12}>
              <Card
                sx={{
                  boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
                  borderRadius: '12px',
                  background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%)',
                }}
              >
                <CardContent>
                  <Typography variant="h6" sx={{ fontWeight: 600, mb: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
                    <TrendingUpIcon color="primary" />
                    Performance Overview
                  </Typography>
                  <Grid container spacing={3}>
                    <Grid item xs={12} sm={6} md={3}>
                      <Box sx={{ textAlign: 'center' }}>
                        <Typography variant="h4" sx={{ fontWeight: 700, color: 'primary.main', mb: 0.5 }}>
                          {jobs.length}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Total Jobs
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Box sx={{ textAlign: 'center' }}>
                        <Typography variant="h4" sx={{ fontWeight: 700, color: 'success.main', mb: 0.5 }}>
                          {resumes.length}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Total Resumes
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Box sx={{ textAlign: 'center' }}>
                        <Typography variant="h4" sx={{ fontWeight: 700, color: 'warning.main', mb: 0.5 }}>
                          {matchResults.length}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Matched Candidates
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Box sx={{ textAlign: 'center' }}>
                        <Typography variant="h4" sx={{ fontWeight: 700, color: 'secondary.main', mb: 0.5 }}>
                          {shortlistedCandidates.length}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Shortlisted
                        </Typography>
                      </Box>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </>
      )}
    </Box>
  );
};

export default Dashboard;
