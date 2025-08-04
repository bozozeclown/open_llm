import pytest
import asyncio
import httpx
from pathlib import Path

@pytest.mark.asyncio
async def test_health_endpoint():
    """Test the health check endpoint"""
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

@pytest.mark.asyncio
async def test_basic_query():
    """Test basic query processing"""
    async with httpx.AsyncClient() as client:
        payload = {
            "content": "What is Python?",
            "metadata": {}
        }
        response = await client.post("http://localhost:8000/process", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data

def test_requirements_imports():
    """Test that all required packages can be imported"""
    required_packages = [
        'torch',
        'transformers', 
        'fastapi',
        'uvicorn',
        'asyncpg',
        'redis',
        'networkx',
        'spacy',
        'plotly',
        'PIL',
        'pydantic',
        'click'
    ]
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError as e:
            pytest.fail(f"Failed to import {package}: {e}")