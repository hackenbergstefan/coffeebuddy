![test](https://github.com/hackenbergstefan/coffeebuddy/workflows/test/badge.svg)
![flake8](https://github.com/hackenbergstefan/coffeebuddy/workflows/lint/badge.svg)

# coffeebuddy

Do you use a paper based tally sheet to count your team's coffee consumption? Throw it away and use `coffeebuddy`!

## Setup

Coffebuddy uses [pdm](https://pdm-project.org/en/latest/) to manage its python dependencies.

0. Install pdm

   ```sh
   curl -sSL https://pdm-project.org/install-pdm.py | python3 -
   ```

1. Install dependencies

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

## Application

The final application uses a Raspberry Pi attached to a 7" touchscreen. Thus, the HTML an CSS is optimized for a display with a resolution of 1024x600.

### How to setup a client Raspberry Pi

1. Flash latest RapberryPi OS
2. Fix screen resolution:

   ```conf
   # /boot/firmware/config.txt
   [all]
   max_usb_current=1

   hdmi_force_hotplug=1
   hdmi_group=2
   hdmi_mode=87
   hdmi_cvt 1024 600 60 3 0 0 1
   hdmi_drive=2

   start_x=1
   ```

   And change `dtoverlay=vc4-kms-v3d` to

   ```conf
   dtoverlay=vc4-fkms-v3d
   ```

3. If display has to be rotated by 180° adjust `/etc/X11/xorg.conf.d/40-libinput.conf`

   ```conf
   Section "InputClass"
       Identifier "libinput touchscreen catchall"
       MatchIsTouchscreen "on"
       MatchDevicePath "/dev/input/event*"
       Driver "libinput"
       Option "CalibrationMatrix" "-1 0 1 0 -1 1 0 0 1"
   EndSection
   ```

   Rotate the display by using an autostart file

   ```conf
   # ~/.config/autostart/rotate.desktop

   [Desktop Entry]
   Name=Rotate
   Type=Application
   Exec=xrandr --output HDMI-1 --rotate inverted
   ```

4. Install required or helpful packages:

   ```sh
   sudo apt install swig libpcsclite-dev pcscd pcsc-tools  vim screen unclutter
   ```

5. Start chrome once and disable translation option.
6. Clone this repo and install requirements:

   ```sh
   git clone https://github.com/hackenbergstefan/coffeebuddy.git
   cd coffeebuddy
   curl -sSL https://pdm-project.org/install-pdm.py | python3 -
   pdm sync
   ```

7. Create and copy certificates for database connection:

   ```sh
   scp coffeebuddyserver:~/coffeebuddy/database/certs/ca/root.crt coffeebuddy01:~/.postgresql/
   scp coffeebuddyserver:"~/coffeebuddy/database/certs/client_coffeebuddy01/postgresql.*" coffeebuddy01:~/.postgresql/
   ```

8. Create and adjust `config_<client>.py`.
9. Enable autostart:

   ```sh
   mkdir ~/.config/autostart
   cp raspi/coffeebuddy.desktop ~/.config/autostart/
   ```

10. Enable gpio service:

    ```sh
    sudo systemctl enable pigpiod
    ```

#### Card reader

Coffeebuddy works with PCSC reader and with SPI RFID module "RC522".
Latter is supported on Raspi by several python modules.
Although [mrfc522](https://github.com/pimylifeup/MFRC522-python) is widely used it leads to a high CPU consumption when polling for card.
[pi-rc522](https://github.com/ondryaso/pi-rc522) uses interrupt based SPI communication.

Both modules can be used and selected in [config.py](./config.py).
