# Mini-Radio Control GUI

This Python application provides a graphical user interface (GUI) to control an ESP32-based SI4732 radio receiver via a serial connection. It allows users to easily manage various radio functions without needing to send raw serial commands manually.

![Screenshot](screenshot.png)

## Features:

*   **Intuitive GUI:** A user-friendly interface built with `guizero` for controlling radio operations.
*   **Serial Port Management:**
    *   Automatically detects available serial ports.
    *   Allows users to select the correct port for their radio (defaults to the last detected port or one containing "ACM" or "USB").
    *   Provides a "Connect" button to establish/re-establish the serial connection.
*   **Radio Control Functions:**
    *   Encoder Rotate (Frequency Up/Down, Menu Scroll)
    *   Encoder Button Press
    *   Volume Up/Down
    *   Next/Previous Band
    *   Next/Previous Mode (FM/LSB/USB/AM)
    *   Next/Previous Step Size
    *   Next/Previous Bandwidth
    *   AGC/Attenuator Up/Down
    *   Backlight Brighter/Dimmer
    *   Calibration Up/Down
    *   Sleep Timer On/Off
*   **Real-time Status Display:**
    *   Firmware Version
    *   Current Frequency (displayed in MHz for FM, kHz for AM/SSB, with BFO for SSB)
    *   Current Mode and Band Name
    *   Volume Level
    *   Signal Strength (RSSI and SNR)
*   **Configurable Cyclic Status Reading:**
    *   A checkbox allows users to enable or disable the continuous polling of status information from the radio. This is useful if the serial communication interferes with radio reception.
*   **Dark Theme:** A visually comfortable dark theme for the interface.
*   **Cross-Platform (Potentially):** Built with Python, `pyserial`, and `guizero`, making it potentially cross-platform (developed and tested on Linux).

## How it Works:

The application sends single-character commands to the SI4732 radio (as documented for many ESP32-SI4732 projects) over the selected serial port. When "Enable Cyclic Reading" is active and checked, it periodically reads a comma-separated status string from the radio, parses it, and updates the relevant display fields in the GUI. The cyclic reading is controlled via a checkbox, which sends a toggle command (`t`) to the radio to start or stop the log stream.

## Technologies Used:

*   **Python 3**
*   **pyserial:** For serial communication.
*   **guizero:** For creating the graphical user interface.

## Getting Started:

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
        python MiniRadio.py
        ```
    *   Select the correct serial port for your radio from the dropdown menu.
    *   Click the "Connect" button.
    *   Check the "Enable Cyclic Reading" checkbox to see live status updates from the radio.
    *   Use the buttons to control your radio!

## Configuration:

*   **Serial Port:** The application attempts to auto-select a sensible default serial port. If this is incorrect, please select the appropriate port from the dropdown menu.
*   **Baud Rate:** Currently hardcoded to `115200`. This is a common baud rate for ESP32 projects but may need adjustment if your radio firmware uses a different rate.

## Known Issues / Limitations:

*   The reliability of cyclic status updates can sometimes be affected by the quality of the serial connection or the radio's responsiveness.
*   Layout has been optimized for a specific setup; minor adjustments might be needed for different screen resolutions or font settings.

## Future Enhancements (Ideas):

*   More robust error handling for serial communication.
*   Ability to save and load preferred settings (e.g., last used port).
*   Visual feedback for ongoing commands.
*   More detailed parsing and display of all available status parameters.

## Contributing:

Contributions, bug reports, and feature requests are welcome! Please feel free to open an issue or submit a pull request.

## License:

This project is licensed under the MIT License - see the LICENSE.md file for details.
