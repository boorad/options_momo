# US Equities Options Momentum Day Trade

### Reference

* [Easy Trading Strategy Optimization with backtesting.py](https://medium.com/@chris_42047/simple-trading-strategy-optimization-with-backtesting-py-python-tutorial-3bdb96ebb500)
* [VumMan Chu Swing Free](https://www.tradingview.com/script/q23anHmP-VuManChu-Swing-Free/)

## Development

### Python Setup

Add to `~/.bashrc`, `~/.zshrc` or similar:

```sh
# python stuffs
alias py39='/usr/local/Cellar/python@3.9/3.9.12_1/bin/python3'

alias vact='source .venv/bin/activate'
alias vdeact='deactivate'

function vcreate() {
    RED="\033[0;31m"
    LIGHT_RED="\033[1;31m"
    GREEN="\033[0;32m"
    if [ -z $1 ]; then
	echo -e "${RED}Usage: vcreate /path/to/python_interpreter${NC}\nExample: vcreate py39"
	return
    fi
    venv_name=".venv"
    echo -e "${GREEN}Creating virtual environment (name=${venv_name})...${NC}"
    eval "$1 -m venv .venv"
    echo -e "${GREEN}Activating virtual environment (name=${venv_name})...${NC}"
    vact
    poetry_version="1.1.15"
    echo -e "${GREEN}Installing Poetry (version=${poetry_version})...${NC}"
    python -m pip install poetry==${poetry_version}
    if [ -f "./pyproject.toml" ]; then
	echo -e "${GREEN}Installing dependencies...${NC}"
	poetry install
    fi
    echo -e "${GREEN}Deactivating virtual environment (name=${venv_name})...${NC}"
    vdeact
    echo -e "${GREEN}Virtual environment (name=${venv_name}) setup complete.${NC}"
    echo -e "${LIGHT_RED}Use 'vact' to activate virtual environment, and 'vdeact' to deactivate it.${NC}"
}
```

### Running

    cd {repo}
    vcreate py39
    vact
    poetry install # if not already done
    py39 {script}
