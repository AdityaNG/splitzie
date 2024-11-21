"""Entry point for server."""

from server.cli import main  # pragma: no cover

if __name__ == "__main__":  # pragma: no cover
    import argparse

    parser = argparse.ArgumentParser(description="D3NavComma video processing")

    args = parser.parse_args()
    main(args)
