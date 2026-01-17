import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Box,
  Card,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress,
  Chip,
  IconButton,
  Button,
  CircularProgress,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Switch,
  Tooltip,
} from '@mui/material';
import {
  Visibility as VisibilityIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Event as EventIcon,
} from '@mui/icons-material';
import { useAppDispatch, useAppSelector } from '../store/hooks';
import { matchJobToCandidates } from '../store/slices/candidatesSlice';
import { fetchJobs } from '../store/slices/jobsSlice';
import {
  shortlistCandidate,
  toggleInterviewEnabled,
  fetchInterviewStatus,
} from '../store/slices/interviewsSlice';

const Candidates: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const jobId = searchParams.get('jobId');
  const dispatch = useAppDispatch();
  const { matchResults, isLoading, error } = useAppSelector((state) => state.candidates);
  const { jobs } = useAppSelector((state) => state.jobs);
  const { interviewStatuses, updatingCandidates } = useAppSelector((state) => state.interviews);
  const [selectedJobId, setSelectedJobId] = useState<string>(jobId || '');

  // Fetch jobs on mount
  useEffect(() => {
    dispatch(fetchJobs({ page: 1, pageSize: 100 }));
  }, [dispatch]);

  // Sync selectedJobId with URL parameter
  useEffect(() => {
    if (jobId && jobId !== selectedJobId) {
      setSelectedJobId(jobId);
    } else if (!jobId) {
      setSelectedJobId('');
    }
  }, [jobId]);

  // Note: We don't auto-fetch ranked results on job selection
  // Results are only shown after clicking "Match Candidates"
  // This prevents overwriting matched results

  const handleJobChange = (event: any) => {
    const newJobId = event.target.value;
    setSelectedJobId(newJobId);
    if (newJobId) {
      setSearchParams({ jobId: newJobId });
    } else {
      setSearchParams({});
    }
  };

  const handleMatch = async () => {
    if (jobId) {
      try {
        const result = await dispatch(matchJobToCandidates({ jobId, strategy: 'standard' })).unwrap();
        // Results are automatically stored in state by the slice
        if (result.message) {
          console.log('Matching info:', result.message);
        }
        // Fetch interview statuses for all matched candidates
        if (result.ranked_candidates && jobId) {
          result.ranked_candidates.forEach((candidate: any) => {
            dispatch(fetchInterviewStatus({ candidateId: candidate.candidate_id, jobId }));
          });
        }
      } catch (error: any) {
        console.error('Failed to match candidates:', error);
        // Error is already handled by the slice and displayed in the UI
      }
    }
  };

  const handleShortlistToggle = async (candidateId: string, currentShortlisted: boolean) => {
    if (!jobId) return;
    try {
      await dispatch(
        shortlistCandidate({
          candidateId,
          jobId,
          shortlisted: !currentShortlisted,
        })
      ).unwrap();
    } catch (error: any) {
      console.error('Failed to toggle shortlist:', error);
    }
  };

  const handleInterviewToggle = async (
    candidateId: string,
    currentInterviewEnabled: boolean,
    currentOnlineEnabled: boolean
  ) => {
    if (!jobId) return;
    try {
      await dispatch(
        toggleInterviewEnabled({
          candidateId,
          jobId,
          data: {
            interview_enabled: !currentInterviewEnabled,
            online_interview_enabled: currentOnlineEnabled,
          },
        })
      ).unwrap();
    } catch (error: any) {
      console.error('Failed to toggle interview:', error);
    }
  };

  const getInterviewStatus = (candidateId: string) => {
    if (!jobId) return null;
    const key = `${candidateId}-${jobId}`;
    return interviewStatuses[key] || null;
  };

  const isUpdating = (candidateId: string) => {
    return updatingCandidates.includes(candidateId);
  };

  if (!jobId) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Candidates
        </Typography>
        <Box sx={{ mt: 3 }}>
          <FormControl fullWidth sx={{ maxWidth: 400 }}>
            <InputLabel>Select a Job</InputLabel>
            <Select
              value={selectedJobId}
              label="Select a Job"
              onChange={handleJobChange}
            >
              {jobs.length === 0 ? (
                <MenuItem value="" disabled>
                  No jobs available
                </MenuItem>
              ) : (
                jobs.map((job) => (
                  <MenuItem key={job.id} value={job.id}>
                    {job.title}
                  </MenuItem>
                ))
              )}
            </Select>
          </FormControl>
          {jobs.length === 0 && (
            <Alert severity="info" sx={{ mt: 2, maxWidth: 400 }}>
              No jobs found. Please create a job first to view candidates.
            </Alert>
          )}
        </Box>
      </Box>
    );
  }

  const selectedJob = jobs.find((j) => j.id === jobId);

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3, flexWrap: 'wrap', gap: 2 }}>
        <Typography variant="h4">Candidates</Typography>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <FormControl sx={{ minWidth: 250 }}>
            <InputLabel>Select Job</InputLabel>
            <Select
              value={selectedJobId}
              label="Select Job"
              onChange={handleJobChange}
            >
              {jobs.map((job) => (
                <MenuItem key={job.id} value={job.id}>
                  {job.title}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <Button variant="contained" onClick={handleMatch} disabled={isLoading}>
            {isLoading ? <CircularProgress size={24} /> : 'Match Candidates'}
          </Button>
        </Box>
      </Box>

      {selectedJob && (
        <Alert severity="info" sx={{ mb: 3 }}>
          Showing candidates for: <strong>{selectedJob.title}</strong>
        </Alert>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {isLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <TableContainer component={Card}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Rank</TableCell>
                    <TableCell>Candidate ID</TableCell>
                    <TableCell>Score</TableCell>
                    <TableCell>Skills</TableCell>
                    <TableCell>Experience</TableCell>
                    <TableCell>Education</TableCell>
                    <TableCell>Shortlisted</TableCell>
                    <TableCell>Interview</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {matchResults.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={9} align="center" sx={{ py: 4 }}>
                        <Typography variant="body2" color="text.secondary">
                          No candidates found. Click "Match Candidates" to find matching candidates for this job.
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ) : (
                    matchResults.map((result) => {
                      const interviewStatus = getInterviewStatus(result.candidate_id);
                      const shortlisted = interviewStatus?.shortlisted || result.shortlisted || false;
                      const interviewEnabled = interviewStatus?.interview_enabled || result.interview_enabled || false;
                      const onlineEnabled = interviewStatus?.online_interview_enabled || result.online_interview_enabled || false;
                      const updating = isUpdating(result.candidate_id);

                      return (
                        <TableRow key={result.id} hover>
                          <TableCell>
                            <Chip label={`#${result.rank || 'N/A'}`} color="primary" size="small" />
                          </TableCell>
                          <TableCell>
                            <Box>
                              <Typography variant="body2" fontWeight="medium">
                                {result.candidate_name || result.anonymized_id || result.candidate_id}
                              </Typography>
                              {result.resume_file_name && (
                                <Typography variant="caption" color="text.secondary">
                                  {result.resume_file_name}
                                </Typography>
                              )}
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <LinearProgress
                                variant="determinate"
                                value={Number(result.overall_score)}
                                sx={{ width: 100, height: 8, borderRadius: 4 }}
                              />
                              <Typography variant="body2">
                                {Number(result.overall_score).toFixed(1)}%
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell>
                            {result.scores_json?.skills !== undefined
                              ? `${result.scores_json.skills.toFixed(0)}%`
                              : 'N/A'}
                          </TableCell>
                          <TableCell>
                            {result.scores_json?.experience !== undefined
                              ? `${result.scores_json.experience.toFixed(0)}%`
                              : 'N/A'}
                          </TableCell>
                          <TableCell>
                            {result.scores_json?.semantic_similarity !== undefined
                              ? `${result.scores_json.semantic_similarity.toFixed(0)}%`
                              : result.scores_json?.education !== undefined
                              ? `${(result.scores_json.education * 100).toFixed(0)}%`
                              : 'N/A'}
                          </TableCell>
                          <TableCell>
                            <Tooltip title={shortlisted ? 'Shortlisted' : 'Not Shortlisted'}>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                <Switch
                                  size="small"
                                  checked={shortlisted}
                                  disabled={updating}
                                  onChange={() => handleShortlistToggle(result.candidate_id, shortlisted)}
                                  color="primary"
                                />
                                {shortlisted ? (
                                  <CheckCircleIcon color="success" fontSize="small" />
                                ) : (
                                  <CancelIcon color="disabled" fontSize="small" />
                                )}
                              </Box>
                            </Tooltip>
                          </TableCell>
                          <TableCell>
                            {shortlisted ? (
                              <Tooltip
                                title={
                                  interviewEnabled
                                    ? onlineEnabled
                                      ? 'Online Interview Enabled'
                                      : 'Interview Enabled (Offline)'
                                    : 'Interview Disabled'
                                }
                              >
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                  <Switch
                                    size="small"
                                    checked={interviewEnabled}
                                    disabled={updating}
                                    onChange={() => handleInterviewToggle(result.candidate_id, interviewEnabled, onlineEnabled)}
                                    color="primary"
                                  />
                                  {interviewEnabled && (
                                    <EventIcon
                                      color={onlineEnabled ? 'primary' : 'action'}
                                      fontSize="small"
                                    />
                                  )}
                                </Box>
                              </Tooltip>
                            ) : (
                              <Typography variant="caption" color="text.secondary">
                                Shortlist first
                              </Typography>
                            )}
                          </TableCell>
                          <TableCell align="right">
                            <IconButton
                              size="small"
                              onClick={() => navigate(`/dashboard/candidates/${result.candidate_id}?jobId=${jobId}`)}
                            >
                              <VisibilityIcon />
                            </IconButton>
                          </TableCell>
                        </TableRow>
                      );
                    })
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </Grid>
          <Grid item xs={12} md={4}>
            {/* Score breakdown card will be added here when candidate selection is implemented */}
          </Grid>
        </Grid>
      )}
    </Box>
  );
};

export default Candidates;

