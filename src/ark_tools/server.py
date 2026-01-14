"""
ARK-TOOLS Server Module
======================

Entry point for running the API server.
"""

import uvicorn
from ark_tools.api import create_app
from ark_tools import config


def main():
    """Main entry point for ark-server command"""
    app = create_app()
    
    uvicorn.run(
        app,
        host=config.API_HOST,
        port=config.API_PORT,
        reload=config.DEBUG,
        log_level="info" if config.DEBUG else "warning"
    )


if __name__ == '__main__':
    main()