# BrightKey

An elegant Windows screen brightness controller using DDC/CI protocol with keyboard shortcuts and native-like UI overlay.

## Features

- Control your monitor brightness with DDC/CI protocol commands
- Adjust brightness using convenient keyboard shortcuts
- Beautiful overlay UI
- Runs in system tray for easy access and management
- Lightweight and minimal resource usage

## Screenshots

![](./screenshots/brightkey.gif)

## How It Works

BrightKey uses the DDC/CI (Display Data Channel Command Interface) protocol to communicate directly with your monitor. This allows for hardware-level brightness adjustment that works with most modern monitors, including external displays.

## Installation

### Prerequisites

Make sure you have Python 3.6+ installed on your system.

### Option 1: From Source

1. Clone the repository:
```bash
git clone https://github.com/Yohane-nlm/BrightKey.git
cd BrightKey
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python brightkey.py
```

### Option 2: Executable (Windows)

Download the latest executable from the [Releases](https://github.com/Yohane-nlm/BrightKey/releases) page.

## Usage

After running BrightKey, it will minimize to the system tray.

### Default Keyboard Shortcuts

- `Win + Enter`: Increase brightness by 10%
- `Win + Shift`: Decrease brightness by 10%

The changes in brightness will be immediately reflected with a sleek overlay display that automatically fades out after a few seconds.

### System Tray

- Right-click on the system tray icon to access the menu
- Select "Exit" to close the application

## Dependencies

- PyQt5
- screen_brightness_control (for DDC/CI communication)
- keyboard

## Building from Source

To build the executable yourself:

```bash
pip install pyinstaller
pyinstaller -F -w brightkey.py
```

The executable will be created in the `dist` directory.

## Customization

You can modify the following aspects by editing the settings:

- Keyboard shortcuts
- Brightness increment/decrement step


## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Screen Brightness Control](https://github.com/Crozzers/screen_brightness_control) - For providing the DDC/CI brightness control interface
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - For the GUI framework

---

*BrightKey - Elegant brightness control at your fingertips*