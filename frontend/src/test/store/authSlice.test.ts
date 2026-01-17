import { describe, it, expect } from 'vitest';
import { configureStore } from '@reduxjs/toolkit';
import authReducer, { login, register, logout } from '../../store/slices/authSlice';

describe('Auth Slice', () => {
  const createStore = () => {
    return configureStore({
      reducer: {
        auth: authReducer,
      },
    });
  };

  it('should handle initial state', () => {
    const store = createStore();
    const state = store.getState().auth;
    
    expect(state.isAuthenticated).toBe(false);
    expect(state.user).toBeNull();
    expect(state.token).toBeNull();
  });

  it('should handle login pending', () => {
    const store = createStore();
    store.dispatch(login.pending('', { email: 'test@example.com', password: 'password' }));
    const state = store.getState().auth;
    
    expect(state.isLoading).toBe(true);
    expect(state.error).toBeNull();
  });

  it('should handle login fulfilled', () => {
    const store = createStore();
    const token = { access_token: 'test-token', token_type: 'bearer' };
    store.dispatch(login.fulfilled(token, '', { email: 'test@example.com', password: 'password' }));
    const state = store.getState().auth;
    
    expect(state.isAuthenticated).toBe(true);
    expect(state.token).toBe('test-token');
    expect(state.isLoading).toBe(false);
  });

  it('should handle login rejected', () => {
    const store = createStore();
    store.dispatch(login.rejected(new Error('Invalid credentials'), '', { email: 'test@example.com', password: 'password' }));
    const state = store.getState().auth;
    
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeTruthy();
  });

  it('should handle logout', () => {
    const store = createStore();
    // First login
    store.dispatch(login.fulfilled({ access_token: 'test-token', token_type: 'bearer' }, '', { email: 'test@example.com', password: 'password' }));
    // Then logout
    store.dispatch(logout.fulfilled(null, ''));
    const state = store.getState().auth;
    
    expect(state.isAuthenticated).toBe(false);
    expect(state.token).toBeNull();
    expect(state.user).toBeNull();
  });
});

