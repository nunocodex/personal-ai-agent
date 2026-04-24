# Contributing to personal-ai-agent

Thank you for your interest in contributing! 🎉

## How to contribute

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature`)
3. Make your changes
4. Run tests if available
5. Commit your changes (`git commit -m 'Add: your feature'`)
6. Push to the branch (`git push origin feature/your-feature`)
7. Open a Pull Request

## Adding a new agent

1. Create a new file in `agents/`
2. Follow the existing agent structure
3. Register the agent in `main.py`
4. Document it in `docs/agents.md`

## Adding a new document format

1. Add the loader in `tools/loaders.py`
2. Register the extension in `core/config.py`
3. Update `docs/setup.md` with any new dependencies

## Code style

- Follow PEP8 for Python code
- Add comments in English
- Keep functions small and focused

## Questions?

Open an issue on GitHub.
