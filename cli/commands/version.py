import click
import requests
import json
from typing import Dict, Any

def version_command(ctx, action: str, description: str, author: str):
    """Handle version management commands"""
    config = ctx.obj['config']
    api_url = config.get('api_url')
    api_key = config.get('api_key')
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    if action == 'create':
        payload = {
            'description': description,
            'author': author
        }
        
        try:
            response = requests.post(
                f"{api_url}/versions",
                headers=headers,
                json=payload,
                timeout=config.get('timeout', 30)
            )
            
            if response.status_code == 200:
                result = response.json()
                click.echo(f"✅ Version created successfully!")
                click.echo(f"📋 Version ID: {result['version_id']}")
                click.echo(f"📝 Description: {description}")
                click.echo(f"👤 Author: {author}")
            else:
                click.echo(f"❌ Error: {response.status_code} - {response.text}", err=True)
                
        except requests.exceptions.RequestException as e:
            click.echo(f"❌ Connection error: {e}", err=True)
        except json.JSONDecodeError as e:
            click.echo(f"❌ JSON decode error: {e}", err=True)
    
    elif action == 'list':
        try:
            response = requests.get(
                f"{api_url}/versions",
                headers=headers,
                timeout=config.get('timeout', 30)
            )
            
            if response.status_code == 200:
                result = response.json()
                versions = result.get('versions', [])
                
                if not versions:
                    click.echo("No versions found.")
                    return
                
                click.echo("📚 Knowledge Graph Versions:")
                click.echo("-" * 50)
                
                for version in versions:
                    click.echo(f"📋 {version['version_id'][:8]}...")
                    click.echo(f"   📝 {version['description']}")
                    click.echo(f"   👤 {version['author']}")
                    click.echo(f"   📅 {version['timestamp']}")
                    if version.get('tags'):
                        click.echo(f"   🏷️  {', '.join(version['tags'])}")
                    click.echo()
            else:
                click.echo(f"❌ Error: {response.status_code} - {response.text}", err=True)
                
        except requests.exceptions.RequestException as e:
            click.echo(f"❌ Connection error: {e}", err=True)
        except json.JSONDecodeError as e:
            click.echo(f"❌ JSON decode error: {e}", err=True)