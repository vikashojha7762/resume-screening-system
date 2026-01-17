import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  Grid,
  CircularProgress,
  Tabs,
  Tab,
} from '@mui/material';
import { ArrowBack, Edit as EditIcon } from '@mui/icons-material';
import { useAppDispatch, useAppSelector } from '../store/hooks';
import { fetchJob } from '../store/slices/jobsSlice';
import { matchJobToCandidates } from '../store/slices/candidatesSlice';

const JobDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { currentJob, isLoading } = useAppSelector((state) => state.jobs);
  const [tabValue, setTabValue] = useState(0);

  useEffect(() => {
    if (id) {
      dispatch(fetchJob(id));
    }
  }, [dispatch, id]);

  const handleMatch = async () => {
    if (id) {
      await dispatch(matchJobToCandidates({ jobId: id, strategy: 'standard' })).unwrap();
      setTabValue(1);
    }
  };

  if (isLoading || !currentJob) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <Button startIcon={<ArrowBack />} onClick={() => navigate('/dashboard/jobs')}>
          Back
        </Button>
        <Typography variant="h4" sx={{ flexGrow: 1, ml: 2 }}>
          {currentJob.title}
        </Typography>
        <Chip label={currentJob.status} color={currentJob.status === 'active' ? 'success' : 'default'} />
        <Button
          startIcon={<EditIcon />}
          variant="outlined"
          sx={{ ml: 2 }}
          onClick={() => navigate(`/dashboard/jobs/${id}/edit`)}
        >
          Edit
        </Button>
      </Box>

      <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)} sx={{ mb: 3 }}>
        <Tab label="Details" />
        <Tab label="Candidates" />
        <Tab label="Analytics" />
      </Tabs>

      {tabValue === 0 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Description
                </Typography>
                <Typography variant="body1" paragraph>
                  {currentJob.description}
                </Typography>
              </CardContent>
            </Card>

            {currentJob.requirements_json && (
              <Card sx={{ mt: 3 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Requirements
                  </Typography>
                  {currentJob.requirements_json.required_skills && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        Required Skills:
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                        {currentJob.requirements_json.required_skills.map((skill, idx) => (
                          <Chip key={idx} label={skill} size="small" />
                        ))}
                      </Box>
                    </Box>
                  )}
                </CardContent>
              </Card>
            )}
          </Grid>
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Job Information
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Created: {new Date(currentJob.created_at).toLocaleDateString()}
                </Typography>
                <Button
                  variant="contained"
                  fullWidth
                  sx={{ mt: 3 }}
                  onClick={handleMatch}
                >
                  Match Candidates
                </Button>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {tabValue === 1 && (
        <Box>
          <Typography variant="h6" gutterBottom>
            Matched Candidates
          </Typography>
          {/* Candidate list will be rendered here */}
        </Box>
      )}

      {tabValue === 2 && (
        <Box>
          <Typography variant="h6" gutterBottom>
            Analytics
          </Typography>
          {/* Analytics charts will be rendered here */}
        </Box>
      )}
    </Box>
  );
};

export default JobDetail;

