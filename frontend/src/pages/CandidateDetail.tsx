import React, { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  CircularProgress,
  Paper,
} from '@mui/material';
import { ArrowBack } from '@mui/icons-material';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from 'recharts';
import { useAppSelector } from '../store/hooks';

const CandidateDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { matchResults } = useAppSelector((state) => state.candidates);
  
  const candidate = matchResults.find((r) => r.candidate_id === id);

  if (!candidate) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  const radarData = [
    { subject: 'Skills', value: (candidate.scores_json?.skills || 0) * 100, fullMark: 100 },
    { subject: 'Experience', value: (candidate.scores_json?.experience || 0) * 100, fullMark: 100 },
    { subject: 'Education', value: (candidate.scores_json?.education || 0) * 100, fullMark: 100 },
  ];

  const barData = [
    { name: 'Skills', score: (candidate.scores_json?.skills || 0) * 100 },
    { name: 'Experience', score: (candidate.scores_json?.experience || 0) * 100 },
    { name: 'Education', score: (candidate.scores_json?.education || 0) * 100 },
  ];

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <Button startIcon={<ArrowBack />} onClick={() => navigate('/dashboard/candidates')}>
          Back
        </Button>
        <Typography variant="h4" sx={{ flexGrow: 1, ml: 2 }}>
          Candidate Details
        </Typography>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Overall Score
              </Typography>
              <Typography variant="h3" color="primary">
                {Number(candidate.overall_score).toFixed(1)}%
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Rank: #{candidate.rank || 'N/A'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Score Breakdown
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={barData}>
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="score" fill="#1976d2" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Skills Radar
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <RadarChart data={radarData}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="subject" />
                  <PolarRadiusAxis angle={90} domain={[0, 100]} />
                  <Radar
                    name="Score"
                    dataKey="value"
                    stroke="#1976d2"
                    fill="#1976d2"
                    fillOpacity={0.6}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Explanation
              </Typography>
              <Typography variant="body1">
                {candidate.explanation?.text || 'No explanation available'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default CandidateDetail;

