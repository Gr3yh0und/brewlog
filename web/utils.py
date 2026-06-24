import os

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def load_env():
    """Parse .env from project root; return dict of key→value."""
    env = {}
    env_path = os.path.join(_ROOT, '.env')
    if os.path.isfile(env_path):
        with open(env_path, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, _, v = line.partition('=')
                    env[k.strip()] = v.strip()
    return env
