/**
 * Interviews Redux Slice
 * Manages interview state and actions
 */
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import * as interviewService from '../../services/interviewService';
import { Interview, InterviewStatus, InterviewToggleRequest } from '../../services/interviewService';

interface InterviewsState {
  interviewStatuses: Record<string, InterviewStatus>; // key: `${candidateId}-${jobId}`
  interviews: Interview[];
  isLoading: boolean;
  error: string | null;
  updatingCandidates: string[]; // Track which candidates are being updated
}

const initialState: InterviewsState = {
  interviewStatuses: {},
  interviews: [],
  isLoading: false,
  error: null,
  updatingCandidates: [],
};

/**
 * Fetch interview status for a candidate
 */
export const fetchInterviewStatus = createAsyncThunk(
  'interviews/fetchStatus',
  async ({ candidateId, jobId }: { candidateId: string; jobId: string }) => {
    const status = await interviewService.getInterviewStatus(candidateId, jobId);
    return { candidateId, jobId, status };
  }
);

/**
 * Shortlist a candidate
 */
export const shortlistCandidate = createAsyncThunk(
  'interviews/shortlist',
  async (
    { candidateId, jobId, shortlisted }: { candidateId: string; jobId: string; shortlisted: boolean },
    { rejectWithValue }
  ) => {
    try {
      await interviewService.shortlistCandidate(candidateId, jobId, shortlisted);
      // Fetch updated status
      const status = await interviewService.getInterviewStatus(candidateId, jobId);
      return { candidateId, jobId, status };
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to shortlist candidate');
    }
  }
);

/**
 * Toggle interview enabled
 */
export const toggleInterviewEnabled = createAsyncThunk(
  'interviews/toggle',
  async (
    {
      candidateId,
      jobId,
      data,
    }: { candidateId: string; jobId: string; data: InterviewToggleRequest },
    { rejectWithValue }
  ) => {
    try {
      const status = await interviewService.toggleInterview(candidateId, jobId, data);
      return { candidateId, jobId, status };
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to toggle interview');
    }
  }
);

/**
 * Fetch interviews for a job
 */
export const fetchInterviews = createAsyncThunk(
  'interviews/fetch',
  async (params: { job_id?: string; candidate_id?: string; status?: string; page?: number; pageSize?: number }) => {
    const response = await interviewService.getInterviews(params);
    return response;
  }
);

/**
 * Schedule an interview
 */
export const scheduleInterview = createAsyncThunk(
  'interviews/schedule',
  async (data: Parameters<typeof interviewService.scheduleInterview>[0], { rejectWithValue }) => {
    try {
      const interview = await interviewService.scheduleInterview(data);
      return interview;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to schedule interview');
    }
  }
);

const interviewsSlice = createSlice({
  name: 'interviews',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    setUpdating: (state, action: PayloadAction<{ candidateId: string; updating: boolean }>) => {
      if (action.payload.updating) {
        if (!state.updatingCandidates.includes(action.payload.candidateId)) {
          state.updatingCandidates.push(action.payload.candidateId);
        }
      } else {
        state.updatingCandidates = state.updatingCandidates.filter(
          (id) => id !== action.payload.candidateId
        );
      }
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch interview status
      .addCase(fetchInterviewStatus.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchInterviewStatus.fulfilled, (state, action) => {
        state.isLoading = false;
        const key = `${action.payload.candidateId}-${action.payload.jobId}`;
        state.interviewStatuses[key] = action.payload.status;
      })
      .addCase(fetchInterviewStatus.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch interview status';
      })
      // Shortlist candidate
      .addCase(shortlistCandidate.pending, (state, action) => {
        if (!state.updatingCandidates.includes(action.meta.arg.candidateId)) {
          state.updatingCandidates.push(action.meta.arg.candidateId);
        }
        state.error = null;
      })
      .addCase(shortlistCandidate.fulfilled, (state, action) => {
        const key = `${action.payload.candidateId}-${action.payload.jobId}`;
        state.interviewStatuses[key] = action.payload.status;
        state.updatingCandidates = state.updatingCandidates.filter(
          (id) => id !== action.meta.arg.candidateId
        );
      })
      .addCase(shortlistCandidate.rejected, (state, action) => {
        state.error = action.payload as string;
        state.updatingCandidates = state.updatingCandidates.filter(
          (id) => id !== action.meta.arg.candidateId
        );
      })
      // Toggle interview
      .addCase(toggleInterviewEnabled.pending, (state, action) => {
        if (!state.updatingCandidates.includes(action.meta.arg.candidateId)) {
          state.updatingCandidates.push(action.meta.arg.candidateId);
        }
        state.error = null;
      })
      .addCase(toggleInterviewEnabled.fulfilled, (state, action) => {
        const key = `${action.payload.candidateId}-${action.payload.jobId}`;
        state.interviewStatuses[key] = action.payload.status;
        state.updatingCandidates = state.updatingCandidates.filter(
          (id) => id !== action.meta.arg.candidateId
        );
      })
      .addCase(toggleInterviewEnabled.rejected, (state, action) => {
        state.error = action.payload as string;
        state.updatingCandidates = state.updatingCandidates.filter(
          (id) => id !== action.meta.arg.candidateId
        );
      })
      // Fetch interviews
      .addCase(fetchInterviews.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchInterviews.fulfilled, (state, action) => {
        state.isLoading = false;
        state.interviews = action.payload.items;
      })
      .addCase(fetchInterviews.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch interviews';
      })
      // Schedule interview
      .addCase(scheduleInterview.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(scheduleInterview.fulfilled, (state, action) => {
        state.isLoading = false;
        state.interviews.push(action.payload);
      })
      .addCase(scheduleInterview.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });
  },
});

export const { clearError, setUpdating } = interviewsSlice.actions;
export default interviewsSlice.reducer;

