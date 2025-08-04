#!/usr/bin/env python3
import click
import requests
import json
import sys
from pathlib import Path
from typing import Optional
from .config import CLIConfig
from .commands.query import query_command
from .commands.analyze import analyze_command
from .commands.session import session_command
from .commands.version import version_command

@click.group()
@click.option('--config-file', type=click.Path(), help='Path to config file')
@click.option('--api-url', help='Override API URL')
@click.option('--api-key', help='Override API key')
@click.pass_context
def cli(ctx, config_file, api_url, api_key):
    """Open LLM Code Assistant CLI"""
    ctx.ensure_object(dict)
    
    # Load configuration
    config = CLIConfig()
    
    # Override with command line options if provided
    if api_url:
        config.set('api_url', api_url)
    if api_key:
        config.set('api_key', api_key)
    
    ctx.obj['config'] = config
    
    # Check API key
    if not config.get('api_key'):
        click.echo("Error: API key not configured. Set OPENLLM_API_KEY environment variable or use --api-key", err=True)
        sys.exit(1)

@cli.command()
@click.argument('question')
@click.option('--language', default='python', help='Programming language context')
@click.pass_context
def query(ctx, question, language):
    """Ask a coding question"""
    return query_command(ctx, question, language)

@cli.command()
@click.option('--file', '-f', type=click.Path(exists=True), required=True, help='Code file to analyze')
@click.option('--language', required=True, help='Programming language')
@click.option('--type', 'analysis_type', default='refactor', 
              type=click.Choice(['refactor', 'quality', 'security']), 
              help='Type of analysis')
@click.pass_context
def analyze(ctx, file, language, analysis_type):
    """Analyze code for improvements"""
    return analyze_command(ctx, file, language, analysis_type)

@cli.command()
@click.argument('session_name')
@click.option('--code', required=True, help='Initial code for the session')
@click.option('--language', default='python', help='Programming language')
@click.option('--public', is_flag=True, help='Make session publicly accessible')
@click.pass_context
def session(ctx, session_name, code, language, public):
    """Create a collaboration session"""
    return session_command(ctx, session_name, code, language, public)

@cli.group()
def version():
    """Knowledge graph version management"""
    pass

@version.command()
@click.option('--description', required=True, help='Version description')
@click.option('--author', default='cli', help='Version author')
@click.pass_context
def create(ctx, description, author):
    """Create a new knowledge graph version"""
    return version_command(ctx, 'create', description, author)

@version.command()
@click.pass_context
def list(ctx):
    """List all knowledge graph versions"""
    return version_command(ctx, 'list', None, None)

if __name__ == '__main__':
    cli()