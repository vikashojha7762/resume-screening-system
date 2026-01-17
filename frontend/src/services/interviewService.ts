/**
 * Interview Service
 * API functions for interview management
 */
import api from './api';

export interface InterviewStatus {
  shortlisted: boolean;
  interview_enabled: boolean;
  online_interview_enabled: boolean;
}

export interface InterviewToggleRequest {
  interview_enabled: boolean;
  online_interview_enabled?: boolean;
}

export interface Interview {
  id: string;
  job_id: string;
  candidate_id: string;
  interview_date: string;
  interview_time: string;
  interview_timezone: string;
  interview_duration: number;
  interviewer_name?: string;
  interview_type: 'online' | 'offline';
  interview_status: 'scheduled' | 'completed' | 'cancelled' | 'no_show' | 'in_progress';
  online_interview_enabled: boolean;
  meeting_link?: string;
  meeting_room_id?: string;
  candidate_joined_at?: string;
  interviewer_joined_at?: string;
  scheduled_by: string;
  cancellation_reason?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

/**
 * Shortlist or unshortlist a candidate
 */
export const shortlistCandidate = async (
  candidateId: string,
  jobId: string,
  shortlisted: boolean
): Promise<{ message: string; shortlisted: boolean }> => {
  const response = await api.post(
    `/candidates/${candidateId}/shortlist?job_id=${jobId}&shortlisted=${shortlisted}`
  );
  return response.data;
};

/**
 * Toggle interview enabled status
 */
export const toggleInterview = async (
  candidateId: string,
  jobId: string,
  data: InterviewToggleRequest
): Promise<InterviewStatus> => {
  const response = await api.post(
    `/candidates/${candidateId}/toggle-interview?job_id=${jobId}`,
    data
  );
  return response.data;
};

/**
 * Get interview status for a candidate
 */
export const getInterviewStatus = async (
  candidateId: string,
  jobId: string
): Promise<InterviewStatus> => {
  const response = await api.get(
    `/candidates/${candidateId}/interview-status?job_id=${jobId}`
  );
  return response.data;
};

/**
 * Schedule an interview
 */
export const scheduleInterview = async (data: {
  job_id: string;
  candidate_id: string;
  interview_date: string;
  interview_time: string;
  interview_timezone?: string;
  interview_duration?: number;
  interviewer_name?: string;
  interview_type?: 'online' | 'offline';
  online_interview_enabled?: boolean;
  notes?: string;
}): Promise<Interview> => {
  const response = await api.post('/interviews', {
    ...data,
    interview_timezone: data.interview_timezone || 'UTC',
    interview_duration: data.interview_duration || 60,
    interview_type: data.interview_type || 'offline',
    online_interview_enabled: data.online_interview_enabled || false,
  });
  return response.data;
};

/**
 * Get interviews for a job
 */
export const getInterviews = async (params: {
  job_id?: string;
  candidate_id?: string;
  status?: string;
  page?: number;
  pageSize?: number;
}): Promise<{ items: Interview[]; total: number; page: number; page_size: number }> => {
  const response = await api.get('/interviews', { params });
  return response.data;
};

/**
 * Get a specific interview
 */
export const getInterview = async (interviewId: string): Promise<Interview> => {
  const response = await api.get(`/interviews/${interviewId}`);
  return response.data;
};

/**
 * Update an interview
 */
export const updateInterview = async (
  interviewId: string,
  data: Partial<Interview>
): Promise<Interview> => {
  const response = await api.put(`/interviews/${interviewId}`, data);
  return response.data;
};

/**
 * Cancel an interview
 */
export const cancelInterview = async (
  interviewId: string,
  cancellationReason?: string
): Promise<Interview> => {
  const response = await api.post(`/interviews/${interviewId}/cancel`, null, {
    params: { cancellation_reason: cancellationReason },
  });
  return response.data;
};

