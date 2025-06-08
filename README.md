# sleep_detector_cps - NOT RELEASED WORK IN PROGRESS
Sleep detector using kria KV260 AI vision and Bluecoin

# How to Install This Application

## 1. Flash Ubuntu on your Kria

Scarica e flasha Ubuntu 22.04 per Kria da:
https://people.canonical.com/~platform/images/xilinx/kria-ubuntu-22.04/

## 2. Install and initialize `xlnx-config`

Al primo avvio (e connesso a Internet), esegui:

```bash
sudo snap install xlnx-config --classic --channel=2.x
sudo xlnx-config.sysinit
```

Questo aggiornerà anche tutti i pacchetti di sistema.  
Quindi, riavvia il dispositivo:

```bash
sudo reboot
```

## 3. Rimuovi l’interfaccia grafica

Per risparmiare risorse:

```bash
sudo systemctl get-default
sudo systemctl set-default multi-user.target
sudo reboot
```

## 4. Installa PYNQ

1. Clona il repository:

   ```bash
   git clone https://github.com/Xilinx/Kria-PYNQ.git
   ```

2. Entra nella cartella:

   ```bash
   cd Kria-PYNQ/
   ```

3. Avvia lo script di installazione:

   ```bash
   sudo bash install.sh -b KV260
   ```

## 5. Accedi all’interfaccia web di PYNQ

Apri nel browser:

```
https://<IP_della_tua_Kria>:9090/lab
```

Per trovare il tuo indirizzo IP:

```bash
ip a
```

![Esempio output di `ip a`](path/to/ip_address_example.png)

La password di default è `Xilinx`.

## 6. Clona il progetto

Dal terminale (dalla web-app di PYNQ):

```bash
git clone https://github.com/andem25/Sleep-Detector-for-Kria-KV260-Vision-AI-Starter-Kit/tree/main
```

## 7. Configura il dongle Bluetooth

> **Nota:** se usi un dongle diverso da RTL8761BU, puoi saltare questo passaggio.

1. Crea la cartella firmware e scarica il modulo:

   ```bash
   sudo mkdir -p /lib/firmware/rtl_bt
   sudo wget -O /lib/firmware/rtl_bt/rtl8761bu_fw.bin      https://www.lwfinger.com/download/rtl_bt/rtl8761bu_fw.bin
   ```

2. Riavvia e verifica:

   ```bash
   sudo reboot
   bluetoothctl
   ```

3. Installa dipendenze e aggiungi `root` al gruppo bluetooth:

   ```bash
   sudo apt install python3-pip python3-distutils libglib2.0-dev
   sudo usermod -aG bluetooth root
   sudo reboot
   ```

## 8. Installa le librerie Python

Dopo il riavvio, nel tuo virtualenv (es. `sleep_venv`):

```bash
pip install blue-st-sdk bluepy opuslib
```

## 9. Imposta i permessi su Bluepy-helper

```bash
sudo setcap "cap_net_raw+eip cap_net_admin+eip"   /home/ubuntu/sleep_venv/lib/python3.10/site-packages/bluepy/bluepy-helper

sudo getcap /home/ubuntu/sleep_venv/lib/python3.10/site-packages/bluepy/bluepy-helper
```

Correggi un problema noto con `blue_st_sdk`:

```bash
sudo sed -i '43c class DictPutSingleElement(collections.abc.MutableMapping):'   /usr/local/share/pynq-venv/lib/python3.10/site-packages/blue_st_sdk/utils/dict_put_single_element.py
```

## 10. Avvia l’applicazione

Entra nella cartella del progetto e lancia:

```bash
python app.py
```
