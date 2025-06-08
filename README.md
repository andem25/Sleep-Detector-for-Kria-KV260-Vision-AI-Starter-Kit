# sleep_detector_cps - NOT RELEASED WORK IN PROGRESS
Sleep detector using kria KV260 AI vision and Bluecoin

# How to Install This Application

## 1. Flash Ubuntu on your Kria

Download and flash Ubuntu 22.04 for Kria from:
https://people.canonical.com/~platform/images/xilinx/kria-ubuntu-22.04/

## 2. Install and initialize `xlnx-config`

On first boot (while connected to the internet), run:

```bash
sudo snap install xlnx-config --classic --channel=2.x
sudo xlnx-config.sysinit
```
Leave all the configurations as default.
This will also upgrade all system packages.  
Then reboot:

```bash
sudo reboot
```

## 3. Remove the graphical interface

To save resources:

```bash
sudo systemctl get-default
sudo systemctl set-default multi-user.target
sudo reboot
```

## 4. Install PYNQ

1. Clone the repository:

   ```bash
   git clone https://github.com/Xilinx/Kria-PYNQ.git
   ```

2. Change into the directory:

   ```bash
   cd Kria-PYNQ/
   ```

3. Run the install script:

   ```bash
   sudo bash install.sh -b KV260
   ```

## 5. Access the PYNQ web interface

Open in your browser:

```
https://<your_kria_ip>:9090/lab
```

To find your IP address:

```bash
ip a
```

![Example output of `ip a`](path/to/ip_address_example.png)

The default password is `Xilinx`.


## 6. Configure the Bluetooth dongle

> **Note:** If you are using a different dongle than RTL8761BU, skip this section.

1. Create the firmware directory and download the firmware:

   ```bash
   sudo mkdir -p /lib/firmware/rtl_bt
   sudo wget -O /lib/firmware/rtl_bt/rtl8761bu_fw.bin \
     https://www.lwfinger.com/download/rtl_bt/rtl8761bu_fw.bin
   ```

2. Reboot and verify:

   ```bash
   sudo reboot
   bluetoothctl
   ```

3. Install dependencies and add `root` to the bluetooth group:

   ```bash
   sudo apt install python3-pip python3-distutils libglib2.0-dev
   sudo usermod -aG bluetooth root
   sudo reboot
   ```

## 7. Install Python libraries

After reboot, in your virtual environment (e.g., `sleep_venv`):

```bash
pip install blue-st-sdk bluepy opuslib
```

## 8. Set permissions for bluepy-helper

```bash
sudo setcap "cap_net_raw+eip cap_net_admin+eip" /usr/local/share/pynq-venv/lib/python3.10/site-packages/bluepy/bluepy-helper
sudo getcap /usr/local/share/pynq-venv/lib/python3.10/site-packages/bluepy/bluepy-helper
```

Fix a known issue with `blue_st_sdk`:

```bash
sudo sed -i '43c class DictPutSingleElement(collections.abc.MutableMapping):' /usr/local/share/pynq-venv/lib/python3.10/site-packages/blue_st_sdk/utils/dict_put_single_element.py
```
## 9. Clone your project

In the terminal (from the PYNQ web app):

```bash
git clone https://github.com/andem25/Sleep-Detector-for-Kria-KV260-Vision-AI-Starter-Kit/
cd Sleep-Detector-for-Kria-KV260-Vision-AI-Starter-Kit/
```

## 10. Run the application

Change into the project folder and run:

```bash
python app.py
```
