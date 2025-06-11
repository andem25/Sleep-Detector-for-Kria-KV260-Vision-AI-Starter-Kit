# Sleep detector for Kria KV260 Vision AI Starter Kit

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)

This project proposes a sleep detector using kria KV260 AI vision, a usb camera connected and the STMicroelectronics' Bluecoin.
## How does it work?
* You need to have a bluecoin applied to your earlobe in order to detect variations in head movement (forwards/backwards).
* The camera constantly captures images and sends them to the processing system.
* The processing system (the kria) evaluates the image through a neural network accelerated in the DPU if the user has yawned.
* If there are more than 3 yawns in the last 10 minutes, the gyroscope data capture is activated for one minute.
* If head movements are detected (therefore the user often raises and lowers their head), an alarm is activated to wake them up, otherwise after one minute the connection with the sensor is deactivated.
* Once 5 yawns are reached within 10 minutes, the user is notified to remember to stop and take a break.

⚠️ **Note: At the moment this version does not support any hardware for audio/light, it only shows a terminal output!**


![image](https://github.com/user-attachments/assets/4468c9cd-3f72-4170-8628-87a9e9b1ffb4)


# How to Install This Application
## Prerequisites:
1. A USB camera (to test this project we used this one https://depstech.com/en-eu/products/hd-1080p-webcam-with-microphone-d04)
2. A Bluecoin of STMicroelectronics with this firmware installed:
   https://www.st.com/en/embedded-software/fp-sns-allmems2.html
3. A bluetooth USB dongle: we used this one (https://www.asus.com/it/networking-iot-servers/adapters/all-series/usbbt400/) and there is a section where it's explained how to configure it. (this is not mandatory, use the dongle you wish)

## 1. Flash Ubuntu on your Kria KV260

Download and flash Ubuntu 22.04 for the Kria from:
https://people.canonical.com/~platform/images/xilinx/kria-ubuntu-22.04/

We recommend to use this version:
**iot-limerick-kria-classic-desktop-2204-x07-20230302-63.img** that you can download from 
https://people.canonical.com/~platform/images/xilinx/kria-ubuntu-22.04/iot-limerick-kria-classic-desktop-2204-x07-20230302-63.img.xz
## 2. Install and initialize `xlnx-config`

At first boot (while connected to the internet), run:

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

In order to save some resources we recommend to disable the greaphical interface:

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
The output should be something like:
![Screenshot 2025-06-11 125139](https://github.com/user-attachments/assets/8906825b-4444-4b5b-983e-45a5d810e6e1)

The default password is `Xilinx`.

You can open now a terminal session in this section:
![image](https://github.com/user-attachments/assets/c2816269-844b-4356-a27d-b763f0fc04b3)



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

After reboot, in the pynq environment:

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
## 9. Clone this project

Now rhat we have configured the environment, It's time to clone the repo!

```bash
git clone https://github.com/andem25/Sleep-Detector-for-Kria-KV260-Vision-AI-Starter-Kit/
```

## 10. Run the application
First check if the USB camera is connected and the bluecoin is on and reachable!

Get into the project folder and run:

```bash
cd Sleep-Detector-for-Kria-KV260-Vision-AI-Starter-Kit/
python main.py
```
To stop the app press `CTRL+C`

If you want you can set:
* The debug mode to troubleshoot some issues:
```bash
DBG=1 python main.py
```
* The name of the bluecoin you want to connect to:
```bash
BLUECOIN_TAG='tag' python main.py
```
If you don't specify these fields the default is 0 for DBG and if you do not specify BLUECOIN_TAG it will scan automatically to the first bluecoin it finds!

## The net we use to classify yawns
In order to classify yawns by the images that the camera captures we use a pretrained neural net (`net.xmodel`):
* in particular the mobilenetv2 (https://pytorch.org/hub/pytorch_vision_mobilenet_v2/)
* it has been finetuned using the Yawn Dataset (https://www.kaggle.com/datasets/davidvazquezcic/yawn-dataset)
* it has been quantized (int 8 bit) for the DPU DPUCZDX8G (with footprint 0x101000016010407) developed by Xilinx using Vitis AI 2.5 (https://github.com/Xilinx/Vitis-AI/releases/tag/v2.5, Docker: docker pull xilinx/vitis-ai:2.5)


