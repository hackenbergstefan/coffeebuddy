![test](https://github.com/hackenbergstefan/coffeetag/workflows/test/badge.svg)
![flake8](https://github.com/hackenbergstefan/coffeetag/workflows/flake8/badge.svg)

# coffeetag

Do you use a paper based tally sheet to count your team's coffee consumption? Throw it away and use `coffeetag`!

## Usage

1. Optional: Create virtual environment
    ```bash
    python3 -m venv .env
    . .env/bin/activate
    pip install -r requirements.txt
    ```
2. Connect a pcsc smart card reader. I use a [uTrust 4701f](https://support.identiv.com/4701f/). Drivers for Ubuntu can be installed for example by
    ```sh
    sudo apt install pcscd pcsc-tools
    ```
3. Start `production` environment
    ```sh
    ./bin/run.py
    ```
    or `development` environment
    ```sh
    FLASK_ENV=development ./bin/run.py
    ```


## Tests
Run tests with `python -m unittest test/test_app.py`
