import { configureStore } from '@reduxjs/toolkit';
import authReducer from './slices/authSlice';
import jobsReducer from './slices/jobsSlice';
import resumesReducer from './slices/resumesSlice';
import candidatesReducer from './slices/candidatesSlice';
import interviewsReducer from './slices/interviewsSlice';
import uiReducer from './slices/uiSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    jobs: jobsReducer,
    resumes: resumesReducer,
    candidates: candidatesReducer,
    interviews: interviewsReducer,
    ui: uiReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

