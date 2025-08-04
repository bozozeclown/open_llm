import click
import requests
import json
from pathlib import Path
from typing import Dict, Any

def analyze_command(ctx, file_path: str, language: str, analysis_type: str):
    """Execute code analysis command"""
    config = ctx.obj['config']
    api_url = config.get('api_url')
    api_key = config.get('api_key')
    
    # Read the file
    try:
        with open(file_path, 'r') as f:
            code_content = f.read()
    except Exception as e:
        click.echo(f"❌ Error reading file: {e}", err=True)
        return
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'content': f"Analyze this {language} code for {analysis_type} improvements",
        'context': {
            'code': code_content,
            'language': language,
            'file_path': str(file_path),
            'analysis_type': analysis_type
        },
        'metadata': {
            'source': 'cli',
            'analysis_type': analysis_type
        }
    }
    
    try:
        response = requests.post(
            f"{api_url}/process",
            headers=headers,
            json=payload,
            timeout=config.get('timeout', 60)  # Longer timeout for analysis
        )
        
        if response.status_code == 200:
            result = response.json()
            click.echo(f"✅ Analysis Results:\n{result['content']}")
            
            # Show suggestions if available
            if 'metadata' in result and 'suggestions' in result['metadata']:
                suggestions = result['metadata']['suggestions']
                click.echo(f"\n💡 Suggestions:")
                for i, suggestion in enumerate(suggestions, 1):
                    click.echo(f"  {i}. {suggestion}")
        else:
            click.echo(f"❌ Error: {response.status_code} - {response.text}", err=True)
            
    except requests.exceptions.RequestException as e:
        click.echo(f"❌ Connection error: {e}", err=True)
    except json.JSONDecodeError as e:
        click.echo(f"❌ JSON decode error: {e}", err=True)