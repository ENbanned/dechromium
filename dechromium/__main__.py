from __future__ import annotations

import sys


def main():
    args = sys.argv[1:]

    if not args or args[0] == "--help":
        _usage()
        return

    if args[0] == "serve":
        _serve(args[1:])
    elif args[0] == "version":
        from . import __version__
        print(f"dechromium {__version__}")
    else:
        print(f"Unknown command: {args[0]}")
        _usage()
        sys.exit(1)


def _serve(args: list[str]):
    host = "127.0.0.1"
    port = 3789

    for arg in args:
        if arg.startswith("--host="):
            host = arg.split("=", 1)[1]
        elif arg.startswith("--port="):
            port = int(arg.split("=", 1)[1])

    from . import Dechromium

    dc = Dechromium()
    try:
        dc.serve(host=host, port=port)
    except KeyboardInterrupt:
        pass
    finally:
        dc.stop_all()


def _usage():
    print("Usage: dechromium <command>")
    print()
    print("Commands:")
    print("  serve [--host=HOST] [--port=PORT]   Start REST API server")
    print("  version                              Show version")
    print()
    print("Python library:")
    print("  from dechromium import Dechromium")
    print("  dc = Dechromium()")
    print('  profile = dc.create("my-profile", platform="windows")')
    print("  browser = dc.start(profile.id)")


if __name__ == "__main__":
    main()
