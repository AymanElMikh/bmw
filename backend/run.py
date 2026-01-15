"""
Application Entry Point
Handles CLI configuration and application startup
"""
import os
import click
import uvicorn
from dotenv import load_dotenv
from configs.config import settings, config

# Load environment variables
load_dotenv()

def get_config_mode():
    """Determine configuration mode from environment"""
    env = os.environ.get('ENV', 'development').lower()
    
    mode_mapping = {
        'development': 'dev',
        'dev': 'dev',
        'testing': 'test',
        'test': 'test',
        'production': 'prod',
        'prod': 'prod'
    }
    
    return mode_mapping.get(env, 'dev')


@click.command()
@click.option(
    '--mode',
    default=None,
    type=click.Choice(['dev', 'test', 'prod'], case_sensitive=False),
    help='Specify the application configuration mode (overrides ENV variable)'
)
@click.option(
    '--host',
    default=None,
    help='The host IP address to bind to (default: from config)'
)
@click.option(
    '--port',
    default=None,
    type=int,
    help='The port number to listen on (default: from config)'
)
@click.option(
    '--reload/--no-reload',
    default=None,
    help='Enable auto-reload on code changes (default: True in dev mode)'
)
def run_app_cli(mode, host, port, reload):
    """
    Starts the FastAPI application with the specified configuration.
    """
    # Determine mode
    if mode is None:
        mode = get_config_mode()
    
    # Set environment variable for app to use
    os.environ['ENV'] = mode
    
    # Import app after setting environment
    from src import create_app
    from configs.config import config
    
    app = create_app()
    
    # Use CLI args or fall back to config
    final_host = host or config.HOST
    final_port = port or config.PORT
    final_reload = reload if reload is not None else config.DEBUG
    
    print(f"🚀 Starting {config.APP_NAME} v{config.APP_VERSION}")
    print(f"📊 Mode: {mode.upper()}")
    print(f"🌐 Server: http://{final_host}:{final_port}")
    print(f"📚 Docs: http://{final_host}:{final_port}/api/docs")
    print(f"🔄 Auto-reload: {final_reload}")
    print(f"🗄️  Database: {config.DATABASE_URL[:50]}...")
    print("-" * 60)
    
    uvicorn.run(
        "src:create_app",
        factory=True,
        host=final_host,
        port=final_port,
        reload=final_reload,
        log_level=config.LOG_LEVEL.lower()
    )


if __name__ == '__main__':
    run_app_cli()