"""CLI interface for server project.

Launches the server
"""

from .server import app


def main(args):  # pragma: no cover
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, access_log=True)
