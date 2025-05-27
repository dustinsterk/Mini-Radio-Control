# Mini-Radio Control GUI

This Python application provides a graphical user interface (GUI) to control an ESP32-based SI4732 radio receiver via a serial connection. It allows users to easily manage various radio functions without needing to send raw serial commands manually.

![Screenshot](screenshot.png)

## Features:

*   **Intuitive GUI:** A user-friendly interface built with `guizero` for controlling radio operations.
*   **Serial Port Management:**
    *   Automatically detects available serial ports.
    *   Attempts to pre-select a likely port based on common USB-to-Serial chip names (e.g., CH340, CP210, FTDI) or generic terms like "USB SERIAL".
    *   Allows users to select the correct port and **baud rate** for their radio from dropdown menus.
    *   Provides a "Connect"/"Disconnect" toggle button to establish, terminate, and re-establish the serial connection.
*   **Radio Control Functions:**
    *   Encoder Rotate (Frequency Up/Down, Menu Scroll)
    *   Encoder Button Press (implemented as a prominent text button)
    *   Volume Up/Down
    *   Next/Previous Band
    *   Next/Previous Mode (FM/LSB/USB/AM)
    *   Next/Previous Step Size
    *   Next/Previous Bandwidth
    *   AGC/Attenuator Next/Previous
    *   Backlight Brighter/Dimmer
    *   Calibration Up/Down
    *   Sleep Timer On/Off
*   **Real-time Status Display:**
    *   Firmware Version (e.g., "2.01" instead of "v2.01")
    *   Current Frequency (displayed in MHz for FM, kHz for AM/SSB, with BFO for SSB; units directly appended, e.g., "145.500MHz")
    *   Current Band and Mode (e.g., "SW/USB")
    *   Volume Level (e.g., "30 (48%)")
    *   Battery Level (e.g., "4.05V (80%)")
    *   Step Size, Bandwidth, AGC Status
    *   Signal Strength (RSSI and SNR)
*   **Configurable Cyclic Status Reading:**
    *   A checkbox (with a raised border style) allows users to enable or disable the continuous polling of status information from the radio.
    *   Status display fields are reset to placeholders when disconnected.
*   **Dark Theme:** A visually comfortable dark theme for the interface.
*   **User Experience Enhancements:**
    *   Connect button provides feedback on connection status and errors, including multi-line error messages.
    *   Warnings if trying to operate controls or checkbox while disconnected.
*   **Cross-Platform (Potentially):** Built with Python, `pyserial`, and `guizero`, making it potentially cross-platform (developed and tested on Linux).
*   **Linux Executable:** A pre-compiled executable for Linux (`Mini-Radio Control`) is available, created with PyInstaller.

## How it Works:

The application sends single-character commands to the SI4732 radio (as documented for many ESP32-SI4732 projects) over the selected serial port. When "Enable Cyclic Reading" is active and checked, it periodically reads a comma-separated status string from the radio, parses it, and updates the relevant display fields in the GUI. The cyclic reading is controlled via a checkbox, which sends a toggle command (`t`) to the radio to start or stop the log stream.

## Technologies Used:

*   **Python 3**
*   **pyserial:** For serial communication.
*   **guizero:** For creating the graphical user interface.

## Getting Started:

### Option 1: Using the Linux Executable (Recommended for Linux users)

1.  Download the `Mini-Radio Control` executable file. You can find this in the `dist` folder of this repository (once uploaded).
2.  Navigate to the directory where you downloaded the file.
3.  Make the file executable:
    ```bash
    chmod +x "Mini-Radio Control"
    ```
4.  Run the application:
    ```bash
    ./"Mini-Radio Control"
    ```

### Option 2: Running from Source (Python 3 required)

1.  **Prerequisites:**
    *   Ensure you have Python 3 installed on your system.
    *   An ESP32-SI4732 based radio receiver flashed with firmware that supports serial control and the described log output format.

2.  **Installation of Dependencies:**
    Open your terminal or command prompt and install the necessary Python libraries:
    ```bash
    pip install pyserial guizero
    ```

3.  **Running the Application:**
    *   Connect your ESP32-SI4732 radio to your computer via USB.
    *   Download or clone this repository.
    *   Navigate to the directory containing `MiniRadio.py` (or your script's name).
    *   Run the script:
        ```bash
        python3 MiniRadio.py
        ```
    *   The application will attempt to auto-select a serial port and will use a default baud rate (115200). Adjust these via the dropdowns if necessary.
    *   Click the "Connect" button. It will change to "Disconnect" upon successful connection.
    *   Check the "Enable Cyclic Reading" checkbox to see live status updates from the radio.
    *   Use the buttons to control your radio.

## Configuration:

*   **Serial Port & Baud Rate:** The application attempts to auto-select a serial port. Both port and baud rate can be selected from their respective dropdown menus before connecting.

## Known Issues / Limitations:

*   The reliability of cyclic status updates can sometimes be affected by the quality of the serial connection or the radio's responsiveness.

## Future Enhancements (Ideas):

*   More robust error handling and feedback for serial communication issues during operation.
*   Ability to save and load preferred settings (e.g., last used port and baud rate).
*   Visual feedback for ongoing commands or when the radio is busy.

## Contributing:

Contributions, bug reports, and feature requests are welcome! Please feel free to open an issue or submit a pull request.

## License:

This project is licensed under the MIT License - see the LICENSE.md file for details.
