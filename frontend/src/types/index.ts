export interface User {
  id: string;
  email: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface Job {
  id: string;
  title: string;
  description: string;
  requirements_json?: {
    required_skills?: string[];
    preferred_skills?: string[];
    required_experience_years?: number;
    preferred_experience_years?: number;
    required_degree?: string;
    preferred_institutions?: string[];
    institution_tiers?: Record<string, string[]>;
    mandatory_requirements?: {
      skills?: string[];
      min_experience_years?: number;
      required_degree?: string;
    };
  };
  status: 'draft' | 'active' | 'closed' | 'archived';
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface JobCreate {
  title: string;
  description: string;
  requirements_json?: Job['requirements_json'];
  status?: Job['status'];
}

export interface JobUpdate {
  title?: string;
  description?: string;
  requirements_json?: Job['requirements_json'];
  status?: Job['status'];
}

export interface Resume {
  id: string;
  file_path: string;
  file_name: string;
  file_size?: string;
  file_type: string;
  parsed_data_json?: any;
  status: 'uploaded' | 'parsing' | 'parsed' | 'processing' | 'processed' | 'error';
  uploaded_by: string;
  created_at: string;
  updated_at: string;
}

export interface ResumeUploadResponse {
  id: string;
  file_name: string;
  status: Resume['status'];
  message: string;
}

export interface Candidate {
  id: string;
  anonymized_id: string;
  resume_id: string;
  masked_data_json?: any;
  created_at: string;
  updated_at: string;
}

export interface MatchResult {
  id: string;
  job_id?: string;
  candidate_id: string;
  anonymized_id?: string;
  resume_id?: string;
  resume_file_name?: string;
  candidate_name?: string;
  scores_json: {
    skills?: number;
    experience?: number;
    education?: number;
    semantic_similarity?: number;
  };
  rank?: string;
  explanation?: any;
  overall_score: number;
  matched_skills?: string[];
  missing_skills?: string[];
  experience_summary?: string;
  created_at?: string;
  updated_at?: string;
  // Interview-related fields
  shortlisted?: boolean;
  interview_enabled?: boolean;
  online_interview_enabled?: boolean;
}

export interface MatchResponse {
  job_id: string;
  job_title: string;
  candidates_matched: number;
  ranked_results: Array<{
    candidate_id: string;
    anonymized_id: string;
    rank: number;
    overall_score: number;
    component_scores: {
      skills: number;
      experience: number;
      education: number;
    };
    explanation: string;
    ranking_explanation: string;
    resume_data?: any;
  }>;
  bias_detection?: {
    overall_bias_score: number;
    gender_bias: any;
    age_bias: any;
    institution_bias: any;
    recommendations: string[];
  };
  processing_time_seconds: number;
  strategy_used: string;
  diversity_enabled: boolean;
}
