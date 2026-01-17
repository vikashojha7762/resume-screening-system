import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../../services/api';
import { MatchResult } from '../../types';

interface CandidatesState {
  matchResults: MatchResult[];
  currentCandidate: MatchResult | null;
  isLoading: boolean;
  error: string | null;
  total: number;
}

const initialState: CandidatesState = {
  matchResults: [],
  currentCandidate: null,
  isLoading: false,
  error: null,
  total: 0,
};

export const fetchMatchResults = createAsyncThunk(
  'candidates/fetchMatchResults',
  async (params: { jobId?: string; minScore?: number; maxScore?: number; page?: number; pageSize?: number }) => {
    const response = await api.get('/results', { params });
    return response.data;
  }
);

export const matchJobToCandidates = createAsyncThunk(
  'candidates/matchJobToCandidates',
  async (params: {
    jobId: string;
    strategy?: string;
    diversityWeight?: number;
    enableBiasDetection?: boolean;
  }) => {
    // Use the new simplified matching endpoint
    const response = await api.post(`/jobs/${params.jobId}/match-candidates`);
    return response.data;
  }
);

export const fetchRankedResults = createAsyncThunk(
  'candidates/fetchRankedResults',
  async (params: { jobId: string; limit?: number; minScore?: number }) => {
    const response = await api.get(`/results/job/${params.jobId}/ranked`, { params });
    return response.data;
  }
);

const candidatesSlice = createSlice({
  name: 'candidates',
  initialState,
  reducers: {
    clearCurrentCandidate: (state) => {
      state.currentCandidate = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchMatchResults.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchMatchResults.fulfilled, (state, action) => {
        state.isLoading = false;
        state.matchResults = action.payload.items;
        state.total = action.payload.total;
      })
      .addCase(fetchMatchResults.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch match results';
      })
      .addCase(matchJobToCandidates.fulfilled, (state, action) => {
        state.isLoading = false;
        // Handle new response format from /jobs/{job_id}/match-candidates
        const rankedCandidates = action.payload.ranked_candidates || [];
        // Convert to MatchResult format for compatibility
        state.matchResults = rankedCandidates.map((candidate: any, index: number) => ({
          id: candidate.candidate_id || candidate.resume_id || `candidate-${index}`,
          candidate_id: candidate.candidate_id || '',
          anonymized_id: candidate.anonymized_id || '',
          resume_id: candidate.resume_id || '',
          resume_file_name: candidate.resume_file_name || '',
          candidate_name: candidate.candidate_name || 'Anonymous',
          overall_score: candidate.final_score || 0.0,
          rank: candidate.rank?.toString() || (index + 1).toString(),
          scores_json: {
            skills: candidate.component_scores?.skills ?? 0.0,
            experience: candidate.component_scores?.experience ?? 0.0,
            semantic_similarity: candidate.component_scores?.semantic_similarity ?? 0.0,
          },
          matched_skills: candidate.matched_skills || [],
          missing_skills: candidate.missing_skills || [],
          experience_summary: candidate.experience_summary || '',
        }));
        state.total = action.payload.candidates_matched || rankedCandidates.length;
        state.error = null;
      })
      .addCase(fetchRankedResults.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchRankedResults.fulfilled, (state, action) => {
        state.isLoading = false;
        state.matchResults = action.payload.items || [];
        state.total = action.payload.total || 0;
      })
      .addCase(fetchRankedResults.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch ranked results';
      })
      .addCase(matchJobToCandidates.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(matchJobToCandidates.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to match candidates';
      });
  },
});

export const { clearCurrentCandidate } = candidatesSlice.actions;
export default candidatesSlice.reducer;

