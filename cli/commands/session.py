# cli/commands/session.py
import click
import requests
import json
from typing import Dict, Any

def session_command(ctx, session_name: str, code: str, language: str, public: bool):
    """Create a collaboration session"""
    config = ctx.obj['config']
    api_url = config.get('api_url')
    api_key = config.get('api_key')
    
    # Use default timeout from configuration
    timeout = config.get('timeout', 30)
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'name': session_name,
        'code': code,
        'language': language,
        'is_public': public
    }
    
    try:
        response = requests.post(
            f"{api_url}/collaboration/sessions",
            headers=headers,
            json=payload,
            timeout=timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            session_id = result.get('id')
            click.echo(f"✅ Session created successfully!")
            click.echo(f"📋 Session ID: {session_id}")
            click.echo(f"🔗 Share URL: {api_url}/collaboration/session/{session_id}")
            
            if public:
                click.echo("🌐 Session is publicly accessible")
            else:
                click.echo("🔒 Session is private")
        else:
            click.echo(f"❌ Error: {response.status_code} - {response.text}", err=True)
            
    except requests.exceptions.RequestException as e:
        click.echo(f"❌ Connection error: {e}", err=True)
    except json.JSONDecodeError as e:
        click.echo(f"❌ JSON decode error: {e}", err=True)