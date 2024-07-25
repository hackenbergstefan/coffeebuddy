![test](https://github.com/hackenbergstefan/coffeebuddy/workflows/test/badge.svg)
![flake8](https://github.com/hackenbergstefan/coffeebuddy/workflows/lint/badge.svg)

# coffeebuddy

Do you use a paper based tally sheet to count your team's coffee consumption? Throw it away and use `coffeebuddy`!

## Setup

Coffebuddy uses [pdm](https://pdm-project.org/en/latest/) to manage its python dependencies.

Coffeebuddy is designed as a server-clients infrastructure.
I'm using a RaspberryPi 4 as server and multiple RaspberryPis 3 as consumer endpoints.
The endpoints are equipped with a smartcard reader and a touch screen for interaction.

### Server

#### Hardware (recommendation)

- RaspberryPi 4
- External SSD to store database

#### Software

The server runs postgresql and uses certificated based authentication on client side.
Details are described in [Setting up postgresql database](./doc/postgresql.md).

### Client

#### Hardware (recommendation)

- RaspberryPi 3
- 7" touchscreen with 1024x600 pixel resolution
- Identiv uTrust 1401f PCSC cardreader
- 3D printed housing (see [doc/housing.md](./doc/housing.md)) including:
  - a PIR for presence detection (see [coffeebuddy/pir.py](./coffeebuddy/pir.py))
  - a multicolor LED for status indication (see [coffeebuddy/illumination.py](./coffeebuddy/illumination.py))

#### Software

1. Install cardreader dependencies
   If using a PCSC cardreader and a Debian based distributions:

   ```sh
   sudo apt install swig libpcsclite-dev pcscd pcsc-tools
   ```

2. Install Python dependencies

   ```sh
   pip install --user pdm

   pdm sync
   ```

3. Start `production` environment

    ```sh
    ./bin/run.py
    ```

##### Debugging

The `development` environment can be run using

```sh
FLASK_DEBUG=1 ./bin/run.py
```

## Tests

Run tests with `pytest -v tests`

## Troubleshooting

The final application uses a Raspberry Pi attached to a 7" touchscreen. Thus, the HTML an CSS is optimized for a display with a resolution of 1024x600.

### Proper configuration for Clients

#### Misc

At least I had to adjust the following settings:

- Fix screen resolution

  ```conf
  hdmi_group=2
  hdmi_mode=87
  hdmi_cvt 1024 600 60 3 0 0 1
  hdmi_drive=2
  ```

- If display has to be rotated by 180° adjust `/etc/X11/xorg.conf.d/40-libinput.conf`

  ```conf
  Section "InputClass"
      Identifier "libinput touchscreen catchall"
      MatchIsTouchscreen "on"
      MatchDevicePath "/dev/input/event*"
      Driver "libinput"
      Option "CalibrationMatrix" "-1 0 1 0 -1 1 0 0 1"
  EndSection
  ```

- Disable translation option in chrome

#### Card reader

Coffeebuddy works with PCSC reader and with SPI RFID module "RC522".
Latter is supported on Raspi by several python modules.
Although [mrfc522](https://github.com/pimylifeup/MFRC522-python) is widely used it leads to a high CPU consumption when polling for card.
[pi-rc522](https://github.com/ondryaso/pi-rc522) uses interrupt based SPI communication.

Both modules can be used and selected in [config.py](./config.py).
