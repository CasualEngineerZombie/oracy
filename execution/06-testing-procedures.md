# Testing Procedures

Comprehensive guide for testing the Oracy AI platform - unit tests, integration tests, and end-to-end testing.

## Table of Contents

1. [Testing Overview](#testing-overview)
2. [Backend Testing](#backend-testing)
3. [Frontend Testing](#frontend-testing)
4. [Integration Testing](#integration-testing)
5. [E2E Testing](#e2e-testing)
6. [AI Pipeline Testing](#ai-pipeline-testing)
7. [Performance Testing](#performance-testing)
8. [Test Data Management](#test-data-management)

---

## Testing Overview

### Test Pyramid

```
         /\
        /  \
       / E2E \      <- Few tests, high coverage
      /--------\        (Playwright)
     /          \
    /Integration \   <- Medium tests
   /--------------\      (API tests)
  /                \
 /    Unit Tests    \ <- Many tests, fast
/--------------------\    (pytest, vitest)
```

### Test Environments

| Environment | Purpose | Database |
|-------------|---------|----------|
| Unit Tests | Fast, isolated | SQLite/in-memory |
| Integration | Component interaction | Test PostgreSQL |
| E2E | Full user flows | Staging database |

---

## Backend Testing

### Running Backend Tests

```bash
cd server
source .venv/bin/activate

# Run all tests
pytest

# Run specific test file
pytest apps/users/tests/test_models.py

# Run specific test
pytest apps/users/tests/test_models.py::TestUserModel::test_create_user

# Run with coverage
pytest --cov=apps --cov-report=html --cov-report=term

# Run in parallel
pytest -n auto

# Run with verbose output
pytest -v

# Run failed tests only
pytest --lf
```

### Test Configuration

```ini
# pytest.ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.test
python_files = tests.py test_*.py *_tests.py
addopts = -v --tb=short --strict-markers
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

### Writing Django Tests

```python
# apps/users/tests/test_models.py
import pytest
from django.core.exceptions import ValidationError
from apps.users.models import User


@pytest.mark.django_db
class TestUserModel:
    """Test User model functionality."""
    
    def test_create_user(self):
        """Test creating a regular user."""
        user = User.objects.create_user(
            email='teacher@school.edu',
            password='testpass123',
            first_name='Jane',
            last_name='Smith'
        )
        
        assert user.email == 'teacher@school.edu'
        assert user.first_name == 'Jane'
        assert user.is_active is True
        assert user.is_staff is False
        assert user.check_password('testpass123')
    
    def test_create_superuser(self):
        """Test creating a superuser."""
        admin = User.objects.create_superuser(
            email='admin@oracy.ai',
            password='adminpass123'
        )
        
        assert admin.is_staff is True
        assert admin.is_superuser is True
    
    def test_email_required(self):
        """Test that email is required."""
        with pytest.raises(ValueError):
            User.objects.create_user(email='', password='test123')


@pytest.mark.django_db
class TestUserAPI:
    """Test User API endpoints."""
    
    def test_register_user(self, api_client):
        """Test user registration."""
        response = api_client.post('/api/auth/register/', {
            'email': 'new@school.edu',
            'password': 'securepass123',
            'first_name': 'New',
            'last_name': 'Teacher'
        })
        
        assert response.status_code == 201
        assert User.objects.filter(email='new@school.edu').exists()
    
    def test_login_user(self, api_client, user_factory):
        """Test user login."""
        user = user_factory(email='test@school.edu', password='testpass')
        
        response = api_client.post('/api/auth/token/', {
            'email': 'test@school.edu',
            'password': 'testpass'
        })
        
        assert response.status_code == 200
        assert 'access' in response.data
        assert 'refresh' in response.data
```

### Fixtures

```python
# conftest.py
import pytest
from rest_framework.test import APIClient
from apps.users.models import User
from apps.students.models import Student, Cohort


@pytest.fixture
def api_client():
    """Return API client."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user):
    """Return authenticated API client."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        email='test@school.edu',
        password='testpass123',
        first_name='Test',
        last_name='Teacher'
    )


@pytest.fixture
def cohort(db):
    """Create a test cohort."""
    return Cohort.objects.create(
        name='Year 7A',
        academic_year='2024-2025'
    )


@pytest.fixture
def student(db, cohort):
    """Create a test student."""
    return Student.objects.create(
        first_name='Alice',
        last_name='Johnson',
        cohort=cohort,
        date_of_birth='2012-03-15'
    )


@pytest.fixture
def sample_transcript():
    """Return sample transcript data."""
    return {
        "duration_seconds": 45.5,
        "full_text": "Today I will explain photosynthesis.",
        "segments": [
            {
                "start": 0.0,
                "end": 4.5,
                "text": "Today I will explain photosynthesis.",
                "words": [
                    {"word": "Today", "start": 0.0, "end": 0.6},
                    {"word": "I", "start": 0.7, "end": 0.8},
                    {"word": "will", "start": 0.9, "end": 1.1},
                ]
            }
        ]
    }
```

### Mocking External Services

```python
# Test with mocked AI services
from unittest.mock import Mock, patch


@pytest.mark.django_db
class TestAIPipeline:
    """Test AI pipeline with mocked services."""
    
    @patch('apps.analysis.services.stt.WhisperSTTService.transcribe')
    def test_transcribe_recording(self, mock_transcribe, recording):
        """Test transcription with mocked STT."""
        mock_transcribe.return_value = Mock(
            full_text='Test transcript',
            duration_seconds=30.0,
            words=[{'word': 'Test', 'start': 0.0, 'end': 0.5}]
        )
        
        # Run transcription
        result = transcribe_recording(recording.id)
        
        assert result['full_text'] == 'Test transcript'
        mock_transcribe.assert_called_once()
    
    @patch('openai.OpenAI')
    def test_llm_scoring(self, mock_openai, evidence_candidates):
        """Test LLM scoring with mocked API."""
        # Mock OpenAI response
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = Mock(
            choices=[Mock(
                message=Mock(
                    content='{"strand_scores": {"physical": "expected"}}'
                )
            )]
        )
        mock_openai.return_value = mock_client
        
        scorer = LLMScorer(api_key='test-key')
        result = scorer.score(evidence_candidates)
        
        assert 'strand_scores' in result
```

---

## Frontend Testing

### Running Frontend Tests

```bash
cd client

# Run all tests
npm run test

# Run in watch mode
npm run test:watch

# Run with coverage
npm run test:coverage

# Run specific file
npm run test -- src/components/Button.test.tsx

# Run E2E tests
npm run test:e2e
```

### Writing Component Tests

```typescript
// src/components/Button.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { Button } from './Button'

describe('Button', () => {
  it('renders with correct text', () => {
    render(<Button>Click me</Button>)
    
    expect(screen.getByText('Click me')).toBeInTheDocument()
  })
  
  it('calls onClick when clicked', () => {
    const handleClick = vi.fn()
    render(<Button onClick={handleClick}>Click me</Button>)
    
    fireEvent.click(screen.getByText('Click me'))
    
    expect(handleClick).toHaveBeenCalledTimes(1)
  })
  
  it('is disabled when loading', () => {
    render(<Button isLoading>Loading</Button>)
    
    expect(screen.getByRole('button')).toBeDisabled()
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })
  
  it('applies variant classes correctly', () => {
    const { rerender } = render(<Button variant="primary">Primary</Button>)
    expect(screen.getByRole('button')).toHaveClass('bg-blue-600')
    
    rerender(<Button variant="secondary">Secondary</Button>)
    expect(screen.getByRole('button')).toHaveClass('bg-gray-200')
  })
})
```

### Testing Hooks

```typescript
// src/hooks/useAuth.test.ts
import { renderHook, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useAuth } from './useAuth'
import * as api from '../api/auth'

describe('useAuth', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })
  
  it('logs in user successfully', async () => {
    const mockLogin = vi.spyOn(api, 'login').mockResolvedValue({
      access: 'fake-token',
      refresh: 'fake-refresh'
    })
    
    const { result } = renderHook(() => useAuth())
    
    await act(async () => {
      await result.current.login('test@school.edu', 'password')
    })
    
    expect(mockLogin).toHaveBeenCalledWith('test@school.edu', 'password')
    expect(result.current.isAuthenticated).toBe(true)
    expect(localStorage.getItem('token')).toBe('fake-token')
  })
  
  it('handles login error', async () => {
    vi.spyOn(api, 'login').mockRejectedValue(new Error('Invalid credentials'))
    
    const { result } = renderHook(() => useAuth())
    
    await act(async () => {
      try {
        await result.current.login('test@school.edu', 'wrong')
      } catch (e) {
        // Expected error
      }
    })
    
    expect(result.current.isAuthenticated).toBe(false)
    expect(result.current.error).toBe('Invalid credentials')
  })
})
```

### Testing API Integration

```typescript
// src/api/assessments.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { getAssessments, createAssessment } from './assessments'
import { apiClient } from './client'

vi.mock('./client')

describe('Assessments API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })
  
  it('fetches assessments list', async () => {
    const mockData = {
      results: [{ id: '1', title: 'Test Assessment' }],
      count: 1
    }
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockData })
    
    const result = await getAssessments()
    
    expect(apiClient.get).toHaveBeenCalledWith('/api/assessments/')
    expect(result).toEqual(mockData)
  })
  
  it('creates new assessment', async () => {
    const newAssessment = {
      student_id: 'student-1',
      mode: 'presenting',
      prompt: 'Explain gravity'
    }
    const mockResponse = { id: 'assessment-1', ...newAssessment }
    vi.mocked(apiClient.post).mockResolvedValue({ data: mockResponse })
    
    const result = await createAssessment(newAssessment)
    
    expect(apiClient.post).toHaveBeenCalledWith('/api/assessments/', newAssessment)
    expect(result).toEqual(mockResponse)
  })
})
```

---

## Integration Testing

### API Integration Tests

```python
# tests/integration/test_assessment_flow.py
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile


@pytest.mark.integration
@pytest.mark.django_db
class TestAssessmentFlow:
    """Test complete assessment creation and processing flow."""
    
    def test_create_assessment_and_upload(
        self, authenticated_client, student
    ):
        """Test creating assessment and uploading video."""
        # Create assessment
        response = authenticated_client.post('/api/assessments/', {
            'student_id': str(student.id),
            'mode': 'presenting',
            'prompt': 'Explain the water cycle'
        })
        assert response.status_code == 201
        assessment_id = response.data['id']
        
        # Get upload URL
        response = authenticated_client.post(
            f'/api/assessments/{assessment_id}/upload-url/',
            {'filename': 'test_video.mp4', 'content_type': 'video/mp4'}
        )
        assert response.status_code == 200
        assert 'upload_url' in response.data
        assert 'recording_id' in response.data
        
        # Complete upload
        recording_id = response.data['recording_id']
        response = authenticated_client.post(
            f'/api/assessments/{assessment_id}/complete-upload/',
            {'recording_id': recording_id}
        )
        assert response.status_code == 200
        
        # Verify recording status
        response = authenticated_client.get(
            f'/api/recordings/{recording_id}/status/'
        )
        assert response.status_code == 200
        assert response.data['status'] == 'pending'
```

### WebSocket Tests

```python
# tests/integration/test_websocket.py
import pytest
from channels.testing import WebsocketCommunicator
from config.asgi import application


@pytest.mark.asyncio
@pytest.mark.integration
async def test_assessment_progress_websocket(user):
    """Test WebSocket updates during assessment processing."""
    communicator = WebsocketCommunicator(
        application,
        f'/ws/assessments/{assessment_id}/'
    )
    
    # Connect
    connected, _ = await communicator.connect()
    assert connected
    
    # Authenticate
    await communicator.send_json_to({
        'type': 'authenticate',
        'token': 'valid-jwt-token'
    })
    
    # Wait for progress update
    response = await communicator.receive_json_from()
    assert response['type'] == 'progress_update'
    assert 'percent' in response
    
    await communicator.disconnect()
```

---

## E2E Testing

### Playwright Setup

```bash
# Install Playwright
npm init playwright@latest

# Install browsers
npx playwright install

# Run E2E tests
npx playwright test
```

### Writing E2E Tests

```typescript
// e2e/assessment.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Assessment Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login')
    await page.fill('[name="email"]', 'test@school.edu')
    await page.fill('[name="password"]', 'testpass')
    await page.click('button[type="submit"]')
    await page.waitForURL('/dashboard')
  })
  
  test('teacher can create assessment', async ({ page }) => {
    // Navigate to assessments
    await page.click('text=Assessments')
    await page.click('text=New Assessment')
    
    // Fill form
    await page.selectOption('[name="student"]', 'Alice Johnson')
    await page.selectOption('[name="mode"]', 'presenting')
    await page.fill('[name="prompt"]', 'Explain photosynthesis')
    
    // Submit
    await page.click('text=Create Assessment')
    
    // Verify success
    await expect(page.locator('text=Assessment created')).toBeVisible()
    await expect(page).toHaveURL(/\/assessments\/\w+$/)
  })
  
  test('teacher can review draft report', async ({ page }) => {
    // Go to completed assessment
    await page.goto('/assessments/test-assessment-id')
    
    // Wait for report to load
    await expect(page.locator('text=Draft Report')).toBeVisible()
    
    // Verify scores are displayed
    await expect(page.locator('text=Physical')).toBeVisible()
    await expect(page.locator('text=Linguistic')).toBeVisible()
    
    // Click on evidence clip
    await page.click('[data-testid="evidence-clip-1"]')
    
    // Verify video player seeks to timestamp
    const video = page.locator('video')
    await expect(video).toHaveAttribute('currentTime', /\d+/)
  })
  
  test('video upload shows progress', async ({ page }) => {
    // Create assessment
    await page.goto('/assessments/new')
    await page.selectOption('[name="student"]', 'Alice Johnson')
    
    // Upload file
    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles('fixtures/sample_video.mp4')
    
    // Verify progress bar appears
    await expect(page.locator('[data-testid="upload-progress"]')).toBeVisible()
    
    // Wait for completion
    await expect(page.locator('text=Upload complete')).toBeVisible({ timeout: 30000 })
  })
})
```

---

## AI Pipeline Testing

### Testing Feature Extraction

```python
# apps/analysis/tests/test_feature_extraction.py
import pytest
from apps.analysis.pipeline.extract_features import FeatureExtractor


class TestFeatureExtraction:
    """Test feature extraction from transcripts."""
    
    def test_extract_word_count(self):
        """Test word count calculation."""
        extractor = FeatureExtractor()
        
        transcript = {
            'words': [
                {'word': 'Hello', 'start': 0.0, 'end': 0.5},
                {'word': 'world', 'start': 0.6, 'end': 1.0},
            ]
        }
        
        features = extractor.extract(transcript)
        
        assert features['word_count'] == 2
    
    def test_detect_fillers(self):
        """Test filler word detection."""
        extractor = FeatureExtractor()
        
        transcript = {
            'words': [
                {'word': 'Um', 'start': 0.0, 'end': 0.3},
                {'word': 'I', 'start': 0.5, 'end': 0.6},
                {'word': 'uh', 'start': 1.0, 'end': 1.2},
                {'word': 'think', 'start': 1.5, 'end': 1.8},
            ]
        }
        
        features = extractor.extract(transcript)
        
        assert features['filler_count'] == 2
        assert 'um' in features['fillers']
        assert 'uh' in features['fillers']
    
    def test_calculate_speaking_rate(self):
        """Test speaking rate calculation."""
        extractor = FeatureExtractor()
        
        transcript = {
            'duration_seconds': 60.0,
            'words': [{'word': f'word{i}'} for i in range(120)]
        }
        
        features = extractor.extract(transcript)
        
        # 120 words / 60 seconds * 60 = 120 WPM
        assert features['speaking_rate'] == 120.0
```

### Benchmark Testing

```python
# apps/benchmarks/tests/test_benchmark_engine.py
import pytest
import json
from apps.analysis.pipeline.benchmark import BenchmarkEngine


class TestBenchmarkEngine:
    """Test BDL evaluation engine."""
    
    @pytest.fixture
    def bdl_definition(self):
        return {
            'version': '1.0.0',
            'age_band': '11-12',
            'mode': 'presenting',
            'strands': {
                'physical': {
                    'indicators': [
                        {
                            'id': 'phys_01',
                            'descriptor': 'Maintains steady pace',
                            'criteria': {'speaking_rate': {'min': 100, 'max': 140}}
                        }
                    ]
                }
            }
        }
    
    def test_match_speaking_rate(self, bdl_definition):
        """Test matching speaking rate criteria."""
        engine = BenchmarkEngine(bdl_definition)
        
        features = {'speaking_rate': 120}
        matches = engine.evaluate(features)
        
        assert len(matches) == 1
        assert matches[0]['indicator_id'] == 'phys_01'
        assert matches[0]['strand'] == 'physical'
```

---

## Performance Testing

### Load Testing with Locust

```python
# locustfile.py
from locust import HttpUser, task, between


class OracyUser(HttpUser):
    wait_time = between(1, 5)
    
    def on_start(self):
        """Login before starting tasks."""
        response = self.client.post('/api/auth/token/', {
            'email': 'loadtest@school.edu',
            'password': 'testpass'
        })
        self.token = response.json()['access']
        self.headers = {'Authorization': f'Bearer {self.token}'}
    
    @task(3)
    def get_assessments(self):
        """Simulate browsing assessments."""
        self.client.get('/api/assessments/', headers=self.headers)
    
    @task(1)
    def create_assessment(self):
        """Simulate creating assessment."""
        self.client.post('/api/assessments/', {
            'student_id': 'test-student-id',
            'mode': 'presenting',
            'prompt': 'Test prompt'
        }, headers=self.headers)
    
    @task(2)
    def get_report(self):
        """Simulate viewing reports."""
        self.client.get(
            '/api/reports/draft/test-report-id/',
            headers=self.headers
        )
```

```bash
# Run load test
locust -f locustfile.py --host=http://localhost:8000

# Open http://localhost:8089
# Set: 100 users, spawn rate 10
```

---

## Test Data Management

### Fixtures and Factories

```python
# apps/core/factories.py
import factory
from apps.users.models import User
from apps.students.models import Student, Cohort
from apps.assessments.models import Assessment


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
    
    email = factory.Sequence(lambda n: f'user{n}@school.edu')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    password = factory.PostGenerationMethodCall('set_password', 'testpass')


class CohortFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Cohort
    
    name = factory.Sequence(lambda n: f'Year 7-{chr(65 + n)}')
    academic_year = '2024-2025'


class StudentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Student
    
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    cohort = factory.SubFactory(CohortFactory)
    date_of_birth = factory.Faker('date_of_birth', minimum_age=11, maximum_age=12)


class AssessmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Assessment
    
    student = factory.SubFactory(StudentFactory)
    mode = factory.Iterator(['presenting', 'explaining', 'persuading'])
    prompt = factory.Faker('sentence')
```

### Test Database Setup

```bash
# Reset test database
python manage.py flush --database=test

# Load test fixtures
python manage.py loaddata fixtures/test_data.json --database=test

# Generate test data
python manage.py generate_test_data --students=50 --assessments=200