import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import api from '../../services/api';
import { Job, JobCreate, JobUpdate } from '../../types';

interface JobsState {
  jobs: Job[];
  currentJob: Job | null;
  isLoading: boolean;
  error: string | null;
  total: number;
  filters: {
    status?: string;
    page: number;
    pageSize: number;
  };
}

const initialState: JobsState = {
  jobs: [],
  currentJob: null,
  isLoading: false,
  error: null,
  total: 0,
  filters: {
    page: 1,
    pageSize: 10,
  },
};

export const fetchJobs = createAsyncThunk(
  'jobs/fetchJobs',
  async (params: { page?: number; pageSize?: number; status?: string }) => {
    const response = await api.get('/jobs', { params });
    return response.data;
  }
);

export const fetchJob = createAsyncThunk('jobs/fetchJob', async (id: string) => {
  const response = await api.get(`/jobs/${id}`);
  return response.data;
});

export const createJob = createAsyncThunk('jobs/createJob', async (jobData: JobCreate) => {
  const response = await api.post<Job>('/jobs', jobData);
  return response.data;
});

export const updateJob = createAsyncThunk(
  'jobs/updateJob',
  async ({ id, data }: { id: string; data: JobUpdate }) => {
    const response = await api.put<Job>(`/jobs/${id}`, data);
    return response.data;
  }
);

export const deleteJob = createAsyncThunk('jobs/deleteJob', async (id: string) => {
  await api.delete(`/jobs/${id}`);
  return id;
});

const jobsSlice = createSlice({
  name: 'jobs',
  initialState,
  reducers: {
    setFilters: (state, action: PayloadAction<Partial<JobsState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearCurrentJob: (state) => {
      state.currentJob = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchJobs.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchJobs.fulfilled, (state, action) => {
        state.isLoading = false;
        state.jobs = action.payload.items;
        state.total = action.payload.total;
      })
      .addCase(fetchJobs.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch jobs';
      })
      .addCase(fetchJob.fulfilled, (state, action) => {
        state.currentJob = action.payload;
      })
      .addCase(createJob.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(createJob.fulfilled, (state, action) => {
        state.isLoading = false;
        state.jobs.unshift(action.payload);
        state.total += 1;
      })
      .addCase(createJob.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to create job';
      })
      .addCase(updateJob.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(updateJob.fulfilled, (state, action) => {
        state.isLoading = false;
        const index = state.jobs.findIndex((j) => j.id === action.payload.id);
        if (index !== -1) {
          state.jobs[index] = action.payload;
        }
        if (state.currentJob?.id === action.payload.id) {
          state.currentJob = action.payload;
        }
      })
      .addCase(updateJob.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to update job';
      })
      .addCase(deleteJob.fulfilled, (state, action) => {
        state.jobs = state.jobs.filter((j) => j.id !== action.payload);
        state.total -= 1;
      });
  },
});

export const { setFilters, clearCurrentJob } = jobsSlice.actions;
export default jobsSlice.reducer;

