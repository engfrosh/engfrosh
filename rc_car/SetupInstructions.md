## Hardware List

- 64GB MicroSD Card
- Raspberry Pi 4, 2GB of RAM
- (?) SD Card - USB adapter

## Hardware Setup

1. [Download Raspberry Pi OS](https://www.raspberrypi.org/software/operating-systems/),
the _with desktop_ version makes it easier to debug and setup.
2. Flash your micro sd card with the image. I use [Balena Etcher](https://www.balena.io/etcher/)
but Raspberry Pi has their [own imager](https://www.raspberrypi.org/software/) as another option.
3. Connect a display and keyboard, and go through the setup following the prompts. Make 
sure to connect it to your WAN/LAN so that you can connect to it without a monitor.

### Setting up for the Camera
1. Enable the camera through the config `$ sudo raspi-config` then __Interface Options__ -> Camera -> Enable
You should now be able to check that it is working by running a command such as `$ raspistill -o Desktop/image.jpg`
