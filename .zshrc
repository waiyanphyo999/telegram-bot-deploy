[ -f "$HOME/.env" ] && source "$HOME/.env"
[ -f "$HOME/.user_env" ] && source "$HOME/.user_env"

# Force UTF-8 encoding for Python I/O to handle Unicode characters
export PYTHONIOENCODING=utf-8
export UV_BREAK_SYSTEM_PACKAGES=true
export PIP_BREAK_SYSTEM_PACKAGES=1
alias gh="TERM=dumb gh"
