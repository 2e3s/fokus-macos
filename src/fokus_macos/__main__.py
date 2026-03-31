try:
    from .app import main
except ImportError:
    from fokus_macos.app import main


if __name__ == "__main__":
    raise SystemExit(main())
