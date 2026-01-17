import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { AxiosError } from 'axios';
import api from '../../services/api';
import { User, Token } from '../../types';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

const initialState: AuthState = {
  user: null,
  token: localStorage.getItem('token'),
  isAuthenticated: !!localStorage.getItem('token'),
  isLoading: false,
  error: null,
};

// Helper function to extract error message from axios error
const getErrorMessage = (error: unknown): string => {
  if (error instanceof AxiosError) {
    // Network error (backend not reachable)
    if (!error.response) {
      if (error.code === 'ECONNREFUSED' || error.message.includes('Network Error')) {
        return 'Unable to connect to server. Please ensure the backend server is running.';
      }
      if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
        return 'Request timed out. Please check your connection and try again.';
      }
      return 'Network error. Please check your connection and try again.';
    }
    // HTTP error with response
    const status = error.response.status;
    const detail = error.response.data?.detail || error.response.data?.message;
    
    if (status === 401) {
      return detail || 'Incorrect email or password';
    }
    if (status === 403) {
      return detail || 'Account is inactive. Please contact support.';
    }
    if (status === 404) {
      return 'Endpoint not found. Please check the API configuration.';
    }
    if (status >= 500) {
      return detail || 'Server error. Please try again later.';
    }
    return detail || error.message || 'An error occurred';
  }
  
  if (error instanceof Error) {
    return error.message;
  }
  
  return 'An unexpected error occurred';
};

export const login = createAsyncThunk(
  'auth/login',
  async (credentials: { email: string; password: string }, { rejectWithValue }) => {
    try {
      const response = await api.post<Token>('/auth/login/json', credentials);
      return response.data;
    } catch (error) {
      return rejectWithValue(getErrorMessage(error));
    }
  }
);

export const register = createAsyncThunk(
  'auth/register',
  async (userData: { email: string; password: string; is_superuser?: boolean }, { rejectWithValue }) => {
    try {
      const response = await api.post<User>('/auth/register', userData);
      return response.data;
    } catch (error) {
      return rejectWithValue(getErrorMessage(error));
    }
  }
);

export const getCurrentUser = createAsyncThunk('auth/me', async () => {
  const response = await api.get<User>('/auth/me');
  return response.data;
});

export const logout = createAsyncThunk('auth/logout', async () => {
  localStorage.removeItem('token');
  return null;
});

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Login
      .addCase(login.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(login.fulfilled, (state, action) => {
        state.isLoading = false;
        state.token = action.payload.access_token;
        state.isAuthenticated = true;
        localStorage.setItem('token', action.payload.access_token);
      })
      .addCase(login.rejected, (state, action) => {
        state.isLoading = false;
        // Use the error message from rejectWithValue if available, otherwise fallback
        state.error = (action.payload as string) || action.error.message || 'Login failed';
      })
      // Register
      .addCase(register.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(register.fulfilled, (state) => {
        state.isLoading = false;
      })
      .addCase(register.rejected, (state, action) => {
        state.isLoading = false;
        state.error = (action.payload as string) || action.error.message || 'Registration failed';
      })
      // Get current user
      .addCase(getCurrentUser.fulfilled, (state, action) => {
        state.user = action.payload;
        state.isAuthenticated = true;
      })
      .addCase(getCurrentUser.rejected, (state) => {
        state.user = null;
        state.isAuthenticated = false;
        state.token = null;
        localStorage.removeItem('token');
      })
      // Logout
      .addCase(logout.fulfilled, (state) => {
        state.user = null;
        state.token = null;
        state.isAuthenticated = false;
      });
  },
});

export const { clearError } = authSlice.actions;
export default authSlice.reducer;

