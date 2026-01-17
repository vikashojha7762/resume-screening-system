import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Box,
  Button,
  Card,
  CardContent,
  TextField,
  Typography,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Grid,
  CircularProgress,
} from '@mui/material';
import { ArrowBack, Save as SaveIcon } from '@mui/icons-material';
import { useAppDispatch, useAppSelector } from '../store/hooks';
import { createJob, updateJob, fetchJob } from '../store/slices/jobsSlice';
import { JobCreate, JobUpdate } from '../types';
import { toast } from 'react-toastify';

const JobForm: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { currentJob, isLoading } = useAppSelector((state) => state.jobs);
  const { user } = useAppSelector((state) => state.auth);
  const isEdit = Boolean(id);

  // Check if user is authenticated
  useEffect(() => {
    if (!user) {
      toast.error('Please login to create a job');
      navigate('/login');
    }
  }, [user, navigate]);

  const [formData, setFormData] = useState<JobCreate>({
    title: '',
    description: '',
    status: 'draft',
    requirements_json: {
      required_skills: [],
      preferred_skills: [],
      required_experience_years: 0,
      preferred_experience_years: 0,
    },
  });

  const [skillsInput, setSkillsInput] = useState('');
  const [preferredSkillsInput, setPreferredSkillsInput] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (isEdit && id) {
      dispatch(fetchJob(id));
    }
  }, [dispatch, id, isEdit]);

  useEffect(() => {
    if (isEdit && currentJob) {
      setFormData({
        title: currentJob.title,
        description: currentJob.description,
        status: currentJob.status,
        requirements_json: currentJob.requirements_json || {
          required_skills: [],
          preferred_skills: [],
          required_experience_years: 0,
          preferred_experience_years: 0,
        },
      });
      if (currentJob.requirements_json?.required_skills) {
        setSkillsInput(currentJob.requirements_json.required_skills.join(', '));
      }
      if (currentJob.requirements_json?.preferred_skills) {
        setPreferredSkillsInput(currentJob.requirements_json.preferred_skills.join(', '));
      }
    }
  }, [currentJob, isEdit]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.title.trim() || !formData.description.trim()) {
      toast.error('Please fill in all required fields');
      return;
    }

    setIsSubmitting(true);

    try {
      // Parse skills from comma-separated string
      const requiredSkills = skillsInput
        .split(',')
        .map((s) => s.trim())
        .filter((s) => s.length > 0);
      const preferredSkills = preferredSkillsInput
        .split(',')
        .map((s) => s.trim())
        .filter((s) => s.length > 0);

      // Build requirements_json - only include fields that have values
      const requirementsJson: any = {};
      if (requiredSkills.length > 0) {
        requirementsJson.required_skills = requiredSkills;
      }
      if (preferredSkills.length > 0) {
        requirementsJson.preferred_skills = preferredSkills;
      }
      if (formData.requirements_json?.required_experience_years) {
        requirementsJson.required_experience_years = formData.requirements_json.required_experience_years;
      }
      if (formData.requirements_json?.preferred_experience_years) {
        requirementsJson.preferred_experience_years = formData.requirements_json.preferred_experience_years;
      }

      const jobData: JobCreate | JobUpdate = {
        title: formData.title.trim(),
        description: formData.description.trim(),
        status: formData.status,
        requirements_json: Object.keys(requirementsJson).length > 0 ? requirementsJson : undefined,
      };

      if (isEdit && id) {
        await dispatch(updateJob({ id, data: jobData as JobUpdate })).unwrap();
        toast.success('Job updated successfully');
      } else {
        await dispatch(createJob(jobData as JobCreate)).unwrap();
        toast.success('Job created successfully');
      }
      navigate('/dashboard/jobs');
    } catch (error: any) {
      console.error('Error saving job:', error);
      let errorMessage = 'Failed to save job';
      
      if (error?.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error?.message) {
        errorMessage = error.message;
      } else if (typeof error === 'string') {
        errorMessage = error;
      }
      
      toast.error(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (field: keyof JobCreate, value: any) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  if (isEdit && isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <Button
          startIcon={<ArrowBack />}
          onClick={() => navigate('/dashboard/jobs')}
          sx={{ mr: 2 }}
        >
          Back
        </Button>
        <Typography variant="h4">{isEdit ? 'Edit Job' : 'Create Job'}</Typography>
      </Box>

      <Card>
        <CardContent>
          <form onSubmit={handleSubmit}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Job Title"
                  value={formData.title}
                  onChange={(e) => handleChange('title', e.target.value)}
                  required
                />
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Description"
                  value={formData.description}
                  onChange={(e) => handleChange('description', e.target.value)}
                  multiline
                  rows={6}
                  required
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Status</InputLabel>
                  <Select
                    value={formData.status}
                    label="Status"
                    onChange={(e) => handleChange('status', e.target.value)}
                  >
                    <MenuItem value="draft">Draft</MenuItem>
                    <MenuItem value="active">Active</MenuItem>
                    <MenuItem value="closed">Closed</MenuItem>
                    <MenuItem value="archived">Archived</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12}>
                <Typography variant="h6" sx={{ mb: 2 }}>
                  Requirements
                </Typography>
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Required Skills (comma-separated)"
                  value={skillsInput}
                  onChange={(e) => setSkillsInput(e.target.value)}
                  placeholder="e.g., Python, FastAPI, PostgreSQL"
                  helperText="Enter skills separated by commas"
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Preferred Skills (comma-separated)"
                  value={preferredSkillsInput}
                  onChange={(e) => setPreferredSkillsInput(e.target.value)}
                  placeholder="e.g., Docker, Kubernetes, AWS"
                  helperText="Enter skills separated by commas"
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  type="number"
                  label="Required Experience (years)"
                  value={formData.requirements_json?.required_experience_years || 0}
                  onChange={(e) =>
                    handleChange('requirements_json', {
                      ...formData.requirements_json,
                      required_experience_years: parseInt(e.target.value) || 0,
                    })
                  }
                  inputProps={{ min: 0 }}
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  type="number"
                  label="Preferred Experience (years)"
                  value={formData.requirements_json?.preferred_experience_years || 0}
                  onChange={(e) =>
                    handleChange('requirements_json', {
                      ...formData.requirements_json,
                      preferred_experience_years: parseInt(e.target.value) || 0,
                    })
                  }
                  inputProps={{ min: 0 }}
                />
              </Grid>

              <Grid item xs={12}>
                <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end', mt: 2 }}>
                  <Button
                    variant="outlined"
                    onClick={() => navigate('/dashboard/jobs')}
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    variant="contained"
                    startIcon={isSubmitting ? <CircularProgress size={20} /> : <SaveIcon />}
                    disabled={!formData.title.trim() || !formData.description.trim() || isSubmitting}
                  >
                    {isSubmitting ? 'Saving...' : isEdit ? 'Update Job' : 'Create Job'}
                  </Button>
                </Box>
              </Grid>
            </Grid>
          </form>
        </CardContent>
      </Card>
    </Box>
  );
};

export default JobForm;

