# Contributing to Workspace Guardian

Thank you for your interest in contributing to Workspace Guardian! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)

## Code of Conduct

This project follows a code of conduct to ensure a welcoming environment:

- Be respectful and inclusive
- Accept constructive criticism gracefully
- Focus on what's best for the community
- Show empathy towards other contributors

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 16+
- Git
- Databricks workspace access
- Familiarity with FastAPI and React

### Setting Up Development Environment

1. **Fork and clone the repository**

```bash
git clone https://github.com/your-username/workspace-guardian.git
cd workspace-guardian
```

2. **Run the setup script**

```bash
./scripts/init_project.sh
```

3. **Configure environment**

```bash
cp env.template .env
# Edit .env with your credentials
```

4. **Test the setup**

```bash
cd backend
source venv/bin/activate
export $(cat ../.env | xargs)
python ../scripts/test_connection.py
```

## Development Workflow

### Branch Naming

Use descriptive branch names:

- `feature/add-user-authentication`
- `bugfix/fix-approval-expiration`
- `docs/update-readme`
- `refactor/optimize-delta-queries`

### Making Changes

1. **Create a feature branch**

```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes**

Edit code following our coding standards (see below)

3. **Test your changes**

```bash
# Test backend
cd backend
python -m pytest

# Test frontend
cd frontend
npm run test
```

4. **Commit with descriptive messages**

```bash
git add .
git commit -m "feat: add user authentication to API endpoints"
```

### Commit Message Format

We follow conventional commits:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

Examples:
```
feat: add expiration date validation for approvals
fix: resolve Delta table connection timeout
docs: update deployment guide with K8s examples
refactor: optimize approval lookup queries
```

## Coding Standards

### Python (Backend)

#### Style Guide

- Follow PEP 8
- Use type hints
- Maximum line length: 88 characters (Black formatter)
- Use docstrings for all functions and classes

#### Example:

```python
from typing import List, Optional
from datetime import datetime

def get_approved_apps(
    workspace_id: str,
    include_expired: bool = False
) -> List[dict]:
    """
    Get list of approved apps for a workspace.
    
    Args:
        workspace_id: The Databricks workspace ID
        include_expired: Whether to include expired approvals
        
    Returns:
        List of approved app dictionaries
        
    Raises:
        ValueError: If workspace_id is invalid
    """
    # Implementation
    pass
```

#### Linting

```bash
cd backend
pip install black flake8 mypy
black app/
flake8 app/
mypy app/
```

### JavaScript/React (Frontend)

#### Style Guide

- Use ESLint configuration provided
- Use functional components with hooks
- Use meaningful variable names
- Add PropTypes or TypeScript types

#### Example:

```jsx
import React, { useState, useEffect } from 'react'
import PropTypes from 'prop-types'

function AppCard({ app, onApprove, onRevoke }) {
  const [isLoading, setIsLoading] = useState(false)
  
  useEffect(() => {
    // Effect logic
  }, [app.id])
  
  const handleApprove = async () => {
    setIsLoading(true)
    try {
      await onApprove(app)
    } finally {
      setIsLoading(false)
    }
  }
  
  return (
    <div className="app-card">
      {/* JSX */}
    </div>
  )
}

AppCard.propTypes = {
  app: PropTypes.object.isRequired,
  onApprove: PropTypes.func.isRequired,
  onRevoke: PropTypes.func.isRequired
}

export default AppCard
```

#### Linting

```bash
cd frontend
npm run lint
```

### CSS

- Use CSS modules or styled-components
- Follow BEM naming convention for classes
- Use CSS variables for colors and common values
- Mobile-first responsive design

## Testing

### Backend Tests

```bash
cd backend
source venv/bin/activate
python -m pytest tests/ -v
```

### Frontend Tests

```bash
cd frontend
npm test
```

### Integration Tests

```bash
# Start both services
./scripts/run_tests.sh
```

### Test Coverage

Aim for >80% test coverage:

```bash
# Backend
pytest --cov=app tests/

# Frontend
npm test -- --coverage
```

## Submitting Changes

### Pull Request Process

1. **Update documentation**

If you've changed APIs or added features, update:
- README.md
- API documentation
- Inline code comments

2. **Create pull request**

- Use a clear, descriptive title
- Reference any related issues
- Describe what changed and why
- Include screenshots for UI changes
- List any breaking changes

3. **Pull request template**

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Screenshots (if applicable)
Add screenshots for UI changes

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
```

4. **Code review**

- Address reviewer comments
- Make requested changes
- Keep discussions professional

5. **Merge**

Once approved, your PR will be merged!

## Project Structure

Understanding the codebase:

```
workspace-guardian/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── models.py            # Pydantic models
│   │   ├── databricks_client.py # Databricks API wrapper
│   │   └── delta_manager.py     # Delta table operations
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Main app component
│   │   ├── components/          # React components
│   │   ├── services/            # API client
│   │   └── styles/              # CSS styles
│   └── package.json
└── scripts/                     # Helper scripts
```

## Key Areas for Contribution

We welcome contributions in these areas:

### High Priority

- [ ] User authentication and authorization
- [ ] Multi-workspace support improvements
- [ ] Performance optimization for large datasets
- [ ] Audit logging for all approval actions
- [ ] Email notifications for expiring approvals

### Medium Priority

- [ ] Export functionality (CSV, JSON)
- [ ] Advanced filtering and search
- [ ] Batch approval operations
- [ ] Dashboard with analytics
- [ ] Dark mode theme

### Low Priority

- [ ] Additional UI themes
- [ ] Mobile app
- [ ] Slack/Teams integration
- [ ] Custom approval workflows
- [ ] API rate limiting

## Questions?

- Check existing [Issues](https://github.com/workspace-guardian/issues)
- Create a new issue for bugs or feature requests
- Reach out to maintainers

## Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- Project documentation

Thank you for contributing! 🎉




