# ESPN Fantasy Football Streamlit Application

Interactive visualization of your (ESPN) fantasy football league's historical data.

## Hosting

TODO: Docker, env vars, etc.

## Development

### Setup with uv

1. Install uv
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Create virtual environment
   ```bash
   uv venv
   ```

3. Activate virtual environment
   ```bash
   source .venv/bin/activate
   ```

4. Install dependencies
   ```bash
   uv pip install -e .
   ```

5. Install development dependencies (optional)
   ```bash
   uv pip install -e ".[dev]"
   ```

