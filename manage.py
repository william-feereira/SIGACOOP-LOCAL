#!/usr/bin/env python
import os, sys
from pathlib import Path
if __name__ == "__main__":
    env = Path(__file__).resolve().parent / ".env"
    if env.exists():  # rodando sem Docker: lê o .env da pasta do projeto
        from dotenv import load_dotenv
        load_dotenv(env, override=False)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
