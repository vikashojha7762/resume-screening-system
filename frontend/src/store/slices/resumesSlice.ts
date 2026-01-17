import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../../services/api';
import { Resume } from '../../types';

interface ResumesState {
  resumes: Resume[];
  isLoading: boolean;
  error: string | null;
  total: number;
  uploadProgress: Record<string, number>;
}

const initialState: ResumesState = {
  resumes: [],
  isLoading: false,
  error: null,
  total: 0,
  uploadProgress: {},
};

export const fetchResumes = createAsyncThunk(
  'resumes/fetchResumes',
  async (params?: { page?: number; pageSize?: number; status?: string }) => {
    const response = await api.get('/resumes', { params });
    return response.data;
  }
);

export const uploadResume = createAsyncThunk(
  'resumes/uploadResume',
  async (file: File, { dispatch }) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/resumes/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        const progress = progressEvent.total
          ? Math.round((progressEvent.loaded * 100) / progressEvent.total)
          : 0;
        dispatch(setUploadProgress({ fileId: file.name, progress }));
      },
    });
    
    dispatch(removeUploadProgress(file.name));
    return response.data;
  }
);

export const deleteResume = createAsyncThunk('resumes/deleteResume', async (id: string) => {
  await api.delete(`/resumes/${id}`);
  return id;
});

const resumesSlice = createSlice({
  name: 'resumes',
  initialState,
  reducers: {
    setUploadProgress: (state, action) => {
      const { fileId, progress } = action.payload;
      state.uploadProgress[fileId] = progress;
    },
    removeUploadProgress: (state, action) => {
      delete state.uploadProgress[action.payload];
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchResumes.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchResumes.fulfilled, (state, action) => {
        state.isLoading = false;
        // Handle both list response format and direct array
        if (action.payload.items) {
          state.resumes = action.payload.items;
          state.total = action.payload.total || action.payload.items.length;
        } else if (Array.isArray(action.payload)) {
          state.resumes = action.payload;
          state.total = action.payload.length;
        } else {
          // Fallback: empty array if structure is unexpected
          console.warn('Unexpected fetchResumes response format:', action.payload);
          state.resumes = [];
          state.total = 0;
        }
      })
      .addCase(fetchResumes.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch resumes';
      })
      .addCase(uploadResume.pending, (state) => {
        state.error = null;
      })
      .addCase(uploadResume.fulfilled, (state, action) => {
        // Add the uploaded resume to the list immediately
        if (action.payload) {
          // Ensure ID is a string (handle UUID objects)
          const resumeId = typeof action.payload.id === 'string' 
            ? action.payload.id 
            : String(action.payload.id);
          
          // Check if resume already exists (avoid duplicates)
          const exists = state.resumes.some((r) => {
            const rId = typeof r.id === 'string' ? r.id : String(r.id);
            return rId === resumeId;
          });
          
          if (!exists) {
            // Normalize the resume data to ensure all fields are properly formatted
            const normalizedResume: Resume = {
              id: resumeId,
              file_path: action.payload.file_path || '',
              file_name: action.payload.file_name || '',
              file_size: action.payload.file_size,
              file_type: action.payload.file_type || '',
              parsed_data_json: action.payload.parsed_data_json,
              status: typeof action.payload.status === 'string' 
                ? action.payload.status 
                : action.payload.status?.value || 'uploaded',
              uploaded_by: typeof action.payload.uploaded_by === 'string'
                ? action.payload.uploaded_by
                : String(action.payload.uploaded_by),
              created_at: action.payload.created_at 
                ? (typeof action.payload.created_at === 'string' 
                    ? action.payload.created_at 
                    : new Date(action.payload.created_at).toISOString())
                : new Date().toISOString(),
              updated_at: action.payload.updated_at
                ? (typeof action.payload.updated_at === 'string'
                    ? action.payload.updated_at
                    : new Date(action.payload.updated_at).toISOString())
                : new Date().toISOString(),
            };
            state.resumes.unshift(normalizedResume);
            state.total += 1;
          }
        }
      })
      .addCase(uploadResume.rejected, (state, action) => {
        state.error = action.error.message || 'Failed to upload resume';
      })
      .addCase(deleteResume.fulfilled, (state, action) => {
        state.resumes = state.resumes.filter((r) => r.id !== action.payload);
        state.total -= 1;
      });
  },
});

export const { setUploadProgress, removeUploadProgress } = resumesSlice.actions;
export default resumesSlice.reducer;

