# tests/integration/test_multimodal.py
import pytest
import base64
from unittest.mock import Mock, patch
from core.multimodal.image_analyzer import ImageAnalyzer
from PIL import Image
import io

@pytest.fixture
def image_analyzer():
    return ImageAnalyzer()

@pytest.fixture
def sample_code_image():
    # Create a sample image with code
    image = Image.new('RGB', (800, 600), color='white')
    # In a real test, you'd use an actual image with code
    return image

def test_image_analysis_success(image_analyzer, sample_code_image):
    """Test successful image analysis"""
    # Convert image to base64
    buffer = io.BytesIO()
    sample_code_image.save(buffer, format="PNG")
    image_data = base64.b64encode(buffer.getvalue()).decode()
    
    result = image_analyzer.analyze_code_image(image_data)
    
    assert result["success"] is True
    assert "extracted_text" in result
    assert "language" in result
    assert "structured_code" in result
    assert result["confidence"] > 0

@pytest.mark.asyncio
async def test_language_detection(image_analyzer):
    """Test programming language detection"""
    python_code = "def hello_world():\n    print('Hello, World!')"
    js_code = "function helloWorld() {\n    console.log('Hello, World!');\n}"
    
    python_result = image_analyzer._detect_language(python_code)
    js_result = image_analyzer._detect_language(js_code)
    
    assert python_result == "python"
    assert js_result == "javascript"

# tests/integration/test_refactoring.py
import pytest
from core.refactoring.refactor_engine import RefactoringEngine, RefactoringType

@pytest.fixture
def refactoring_engine():
    return RefactoringEngine()

def test_extract_function_detection(refactoring_engine):
    """Test detection of extract function opportunities"""
    long_function_code = """
def complex_function():
    # This function is too long
    data = []
    for i in range(100):
        if i % 2 == 0:
            data.append(i)
    # More code...
    result = process_data(data)
    return result
"""
    
    suggestions = refactoring_engine.analyze_code(long_function_code, "python")
    
    extract_suggestions = [s for s in suggestions if s.type == RefactoringType.EXTRACT_FUNCTION]
    assert len(extract_suggestions) > 0
    assert any("Extract function" in s.title for s in extract_suggestions)

def test_magic_number_detection(refactoring_engine):
    """Test detection of magic numbers"""
    code_with_magic_numbers = """
def calculate_area(radius):
    return 3.14159 * radius * radius

def calculate_total(items):
    total = 0
    for item in items:
        if item.value > 100:
            total += item.value * 1.15  # 15% tax
    return total
"""
    
    suggestions = refactoring_engine.analyze_code(code_with_magic_numbers, "python")
    
    magic_number_suggestions = [s for s in suggestions if s.type == RefactoringType.INTRODUCE_CONSTANT]
    assert len(magic_number_suggestions) > 0
    assert any("3.14159" in s.original_code for s in magic_number_suggestions)

# tests/integration/test_collaboration.py
import pytest
import asyncio
from core.collaboration.session_manager import CollaborationManager, SessionRole, Permission

@pytest.fixture
def collaboration_manager():
    return CollaborationManager()

@pytest.mark.asyncio
async def test_session_creation(collaboration_manager):
    """Test session creation"""
    session = await collaboration_manager.create_session(
        owner_id="user1",
        name="Test Session",
        code="print('Hello, World!')",
        language="python"
    )
    
    assert session.id is not None
    assert session.owner_id == "user1"
    assert session.code == "print('Hello, World!')"
    assert session.owner_id in session.collaborators
    assert session.collaborators[session.owner_id].role == SessionRole.OWNER

@pytest.mark.asyncio
async def test_session_joining(collaboration_manager):
    """Test joining a session"""
    # Create session
    session = await collaboration_manager.create_session(
        owner_id="user1",
        name="Test Session",
        code="print('Hello, World!')",
        language="python"
    )
    
    # Join session
    joined_session = await collaboration_manager.join_session(
        session_id=session.id,
        user_id="user2",
        user_name="User 2"
    )
    
    assert joined_session is not None
    assert "user2" in joined_session.collaborators
    assert joined_session.collaborators["user2"].role == SessionRole.VIEWER

@pytest.mark.asyncio
async def test_code_update_permissions(collaboration_manager):
    """Test code update permissions"""
    # Create session
    session = await collaboration_manager.create_session(
        owner_id="user1",
        name="Test Session",
        code="print('Hello, World!')",
        language="python"
    )
    
    # Join as viewer
    await collaboration_manager.join_session(
        session_id=session.id,
        user_id="user2",
        user_name="User 2"
    )
    
    # Try to update code as viewer (should fail)
    result = await collaboration_manager.update_code(
        session_id=session.id,
        user_id="user2",
        code="print('Updated code')"
    )
    assert result is False
    
    # Update code as owner (should succeed)
    result = await collaboration_manager.update_code(
        session_id=session.id,
        user_id="user1",
        code="print('Updated code')"
    )
    assert result is True
    assert session.code == "print('Updated code')"