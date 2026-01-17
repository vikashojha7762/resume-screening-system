# Contributing Guidelines

Thank you for your interest in contributing to the Resume Screening System!

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Respect different viewpoints

## How to Contribute

### Reporting Bugs

1. **Check Existing Issues**
   - Search for similar issues
   - Check if already fixed

2. **Create Issue**
   - Use bug report template
   - Include:
     - Steps to reproduce
     - Expected behavior
     - Actual behavior
     - Environment details

3. **Provide Information**
   - Error messages
   - Logs
   - Screenshots
   - System information

### Suggesting Features

1. **Check Roadmap**
   - Review planned features
   - Check if already suggested

2. **Create Feature Request**
   - Use feature template
   - Describe use case
   - Explain benefits
   - Provide examples

3. **Discussion**
   - Engage in discussion
   - Provide feedback
   - Help refine ideas

### Submitting Code

1. **Fork Repository**
2. **Create Branch**
   ```bash
   git checkout -b feature/your-feature
   ```
3. **Make Changes**
   - Follow code style
   - Write tests
   - Update documentation
4. **Test Changes**
   ```bash
   pytest
   npm test
   ```
5. **Commit**
   ```bash
   git commit -m "feat: Add new feature"
   ```
6. **Push**
   ```bash
   git push origin feature/your-feature
   ```
7. **Create Pull Request**

## Development Process

### Branch Naming

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation
- `refactor/` - Code refactoring
- `test/` - Test additions
- `chore/` - Maintenance tasks

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `style` - Code style
- `refactor` - Refactoring
- `test` - Tests
- `chore` - Maintenance

**Examples:**
```
feat(api): Add resume bulk upload endpoint

fix(matching): Correct score calculation for edge cases

docs(readme): Update installation instructions
```

### Pull Request Process

1. **Update Documentation**
   - Update relevant docs
   - Add code comments
   - Update changelog

2. **Write Tests**
   - Unit tests for new code
   - Integration tests if needed
   - Update existing tests

3. **Ensure Quality**
   - All tests pass
   - No linter errors
   - Code coverage maintained
   - Documentation updated

4. **Request Review**
   - Assign reviewers
   - Add labels
   - Link related issues

5. **Address Feedback**
   - Respond to comments
   - Make requested changes
   - Update PR description

## Code Review Guidelines

### For Authors

- Keep PRs focused and small
- Write clear descriptions
- Respond to feedback promptly
- Be open to suggestions

### For Reviewers

- Be constructive and respectful
- Focus on code, not person
- Explain reasoning
- Approve when ready

## Testing Requirements

### Coverage Goals

- **New Code:** > 80% coverage
- **Critical Paths:** > 90% coverage
- **Overall:** Maintain > 80%

### Test Types

- **Unit Tests:** All new functions
- **Integration Tests:** API endpoints
- **E2E Tests:** Critical user flows

## Documentation

### Code Documentation

- Docstrings for all functions
- Type hints required
- Inline comments for complex logic

### User Documentation

- Update user guides if UI changes
- Add examples for new features
- Update screenshots if needed

## Release Process

1. **Version Bump**
   - Update version numbers
   - Update changelog

2. **Create Release Branch**
   ```bash
   git checkout -b release/v1.0.0
   ```

3. **Final Testing**
   - Run full test suite
   - Manual testing
   - Performance testing

4. **Tag Release**
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

5. **Deploy**
   - Deploy to staging
   - Verify deployment
   - Deploy to production

## Questions?

- **GitHub Discussions:** For questions
- **Email:** dev-team@resumescreening.com
- **Slack:** #development channel (internal)

Thank you for contributing! 🎉

