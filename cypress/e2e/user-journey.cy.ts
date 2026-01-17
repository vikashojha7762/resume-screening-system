/// <reference types="cypress" />

describe('Complete User Journey', () => {
  beforeEach(() => {
    // Visit the application
    cy.visit('http://localhost:3000');
  });

  it('should complete full user journey', () => {
    // 1. Login
    cy.get('[data-testid="email-input"]').type('test@example.com');
    cy.get('[data-testid="password-input"]').type('password123');
    cy.get('[data-testid="login-button"]').click();
    
    // Wait for redirect to dashboard
    cy.url().should('include', '/dashboard');
    
    // 2. Create a job
    cy.get('[data-testid="create-job-button"]').click();
    cy.get('[data-testid="job-title-input"]').type('Software Engineer');
    cy.get('[data-testid="job-description-input"]').type('We are looking for a skilled software engineer');
    cy.get('[data-testid="save-job-button"]').click();
    
    // 3. Upload resume
    cy.get('[data-testid="upload-resume-button"]').click();
    cy.get('[data-testid="file-input"]').attachFile('sample_resume.pdf');
    cy.get('[data-testid="upload-submit-button"]').click();
    
    // Wait for upload to complete
    cy.get('[data-testid="upload-success"]', { timeout: 10000 }).should('be.visible');
    
    // 4. Match candidates
    cy.get('[data-testid="match-candidates-button"]').click();
    cy.get('[data-testid="match-strategy-select"]').select('standard');
    cy.get('[data-testid="start-matching-button"]').click();
    
    // Wait for matching to complete
    cy.get('[data-testid="matching-complete"]', { timeout: 30000 }).should('be.visible');
    
    // 5. View results
    cy.get('[data-testid="view-results-button"]').click();
    cy.get('[data-testid="candidate-list"]').should('be.visible');
    cy.get('[data-testid="candidate-item"]').should('have.length.greaterThan', 0);
    
    // 6. View candidate details
    cy.get('[data-testid="candidate-item"]').first().click();
    cy.get('[data-testid="candidate-detail"]').should('be.visible');
    cy.get('[data-testid="candidate-score"]').should('be.visible');
  });
});

describe('Resume Upload Flow', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'password123');
    cy.visit('http://localhost:3000/dashboard/resumes');
  });

  it('should upload resume successfully', () => {
    cy.get('[data-testid="file-dropzone"]').attachFile('sample_resume.pdf', { force: true });
    cy.get('[data-testid="upload-progress"]', { timeout: 10000 }).should('be.visible');
    cy.get('[data-testid="upload-success"]', { timeout: 30000 }).should('be.visible');
  });

  it('should reject invalid file types', () => {
    cy.get('[data-testid="file-dropzone"]').attachFile('invalid_file.exe', { force: true });
    cy.get('[data-testid="upload-error"]').should('be.visible');
    cy.get('[data-testid="upload-error"]').should('contain', 'Invalid file type');
  });

  it('should reject files that are too large', () => {
    // Create a large file (11MB)
    cy.get('[data-testid="file-dropzone"]').attachFile('large_file.pdf', { force: true });
    cy.get('[data-testid="upload-error"]').should('be.visible');
    cy.get('[data-testid="upload-error"]').should('contain', 'File too large');
  });
});

describe('Job Management Flow', () => {
  beforeEach(() => {
    cy.login('test@example.com', 'password123');
    cy.visit('http://localhost:3000/dashboard/jobs');
  });

  it('should create a new job', () => {
    cy.get('[data-testid="create-job-button"]').click();
    cy.get('[data-testid="job-title-input"]').type('Test Job');
    cy.get('[data-testid="job-description-input"]').type('Test description');
    cy.get('[data-testid="save-job-button"]').click();
    
    cy.get('[data-testid="job-list"]').should('contain', 'Test Job');
  });

  it('should filter jobs by status', () => {
    cy.get('[data-testid="status-filter"]').select('active');
    cy.get('[data-testid="job-item"]').each(($el) => {
      cy.wrap($el).should('contain', 'Active');
    });
  });

  it('should search jobs', () => {
    cy.get('[data-testid="job-search-input"]').type('Engineer');
    cy.get('[data-testid="job-item"]').should('contain', 'Engineer');
  });
});

