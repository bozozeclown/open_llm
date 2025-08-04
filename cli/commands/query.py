# cli/commands/query.py
import click
import requests
import json
from typing import Dict, Any

def query_command(ctx, question: str, language: str):
    """Execute a query command"""
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
        'content': question,
        'metadata': {
            'language': language,
            'source': 'cli'
        }
    }
    
    try:
        response = requests.post(
            f"{api_url}/process",
            headers=headers,
            json=payload,
            timeout=timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            click.echo(f"✅ Response:\n{result['content']}")
            
            # Show additional metadata if available
            if 'metadata' in result and result['metadata']:
                metadata = result['metadata']
                click.echo(f"\n📊 Metadata:")
                if 'processing' in metadata:
                    processing = metadata['processing']
                    click.echo(f"  Provider: {processing.get('provider', 'unknown')}")
                    click.echo(f"  SLA Tier: {processing.get('sla_tier', 'standard')}")
        else:
            click.echo(f"❌ Error: {response.status_code} - {response.text}", err=True)
            
    except requests.exceptions.RequestException as e:
        click.echo(f"❌ Connection error: {e}", err=True)
    except json.JSONDecodeError as e:
        click.echo(f"❌ JSON decode error: {e}", err=True)