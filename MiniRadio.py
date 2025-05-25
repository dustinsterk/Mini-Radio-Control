#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import os # For path manipulation
import serial  # For serial communication
import serial.tools.list_ports # To list serial ports
from guizero import App, PushButton, Text, Combo, Picture # Box import removed
from PIL import Image # For image manipulation
from guizero import CheckBox # Checkbox added (capitalization corrected)

# --- Configuration ---
# BAUD_RATE is replaced by dynamic selection
DEFAULT_BAUD_RATE = 115200

# --- Global variable for the serial connection ---
ser = None
connected_port = None # Stores the name of the currently connected port
log_mode_active = False # Now controlled by the checkbox

# --- Constants for battery calculation ---
MIN_BATTERY_VOLTAGE = 3.2
MAX_BATTERY_VOLTAGE = 4.2
MAX_VOLUME = 63
# PERCENTAGE_MULTIPLIER = 100 # Used directly in the code

def toggle_connection():
    """Toggles the serial connection (connects if disconnected, disconnects if connected)."""
    global ser, connected_port, log_mode_active # log_mode_active added

    # If already connected, disconnect
    if ser and ser.is_open:
        print("INFO: Disconnecting from serial port...")
        if log_mode_active:
            print("INFO: Attempting to disable radio logging before disconnecting.")
            # We don't strictly need to check the return of send_serial_command_internal here,
            # as we are disconnecting anyway.
            send_serial_command_internal('t')
        
        ser.close()
        ser = None
        connected_port = None
        log_mode_active = False
        if hasattr(app, 'connect_button'):
            app.connect_button.text = "Connect"
            app.connect_button.text_color = dark_theme_text_color # Reset to default
        if hasattr(app, 'enable_cyclic_reading'):
            app.enable_cyclic_reading.value = 0
        reset_status_display() # Reset status fields
        print("INFO: Disconnected.")
        return

    # If not connected, try to connect
    try:
        selected_port = app.port_selector.value # Read port from dropdown
        if not selected_port or selected_port == "No ports found": # Changed German string
            print("No valid port selected.")
            if hasattr(app, 'connect_button'): # Nur aktualisieren, wenn Button existiert
                app.connect_button.text = "No port\nselected" # Zeilenumbruch hinzugefügt
                app.connect_button.text_color = "#FFA726" # Orange
            return

        selected_baud_rate_str = app.baud_rate_selector.value
        try:
            selected_baud_rate = int(selected_baud_rate_str)
        except ValueError:
            print(f"Invalid baud rate selected: {selected_baud_rate_str}. Using default.")
            selected_baud_rate = DEFAULT_BAUD_RATE # Fallback to default

        print(f"Attempting connection to {selected_port} at {selected_baud_rate} baud...")
        ser = serial.Serial(selected_port, selected_baud_rate, timeout=1)
        connected_port = selected_port # Store connected port
        print(f"Successfully connected to {connected_port}.")
        if hasattr(app, 'connect_button'): # Check if button exists before updating
            app.connect_button.text = "Disconnect" # Button now shows "Disconnect"
            app.connect_button.text_color = "#66BB6A" # Grün

        # Automatically attempt to enable cyclic reading on successful connection
        print("INFO: Attempting to enable cyclic reading automatically after connection.")
        # We want logging to be ON. log_mode_active is currently False (or should be after error handling).
        # Sending 't' should toggle the radio's logging to ON.
        if send_serial_command_internal('t'):
            log_mode_active = True # Now app believes logging is ON
            if hasattr(app, 'enable_cyclic_reading'):
                app.enable_cyclic_reading.value = 1 # Check the box
            print("INFO: Cyclic reading enabled automatically.")
        else:
            # If sending 't' failed, log_mode_active remains False (or should be explicitly set)
            # and the checkbox remains unchecked.
            log_mode_active = False # Ensure it's false if command failed
            if hasattr(app, 'enable_cyclic_reading'):
                app.enable_cyclic_reading.value = 0 # Ensure box is unchecked
            print("WARN: Failed to automatically enable cyclic reading. Please use the checkbox.")


    except serial.SerialException as e:
        print(f"ERROR: Error opening serial port {selected_port}: {e}")
        if hasattr(app, 'connect_button'):
            app.connect_button.text = "Connection\nfailed" # Zeilenumbruch hinzugefügt
            app.connect_button.text_color = "#EF5350" # Red
        ser = None # Ensure ser is None if connection fails
        if hasattr(app, 'enable_cyclic_reading'): app.enable_cyclic_reading.value = 0 # Uncheck if connection fails
        log_mode_active = False # Ensure log mode is off
        reset_status_display() # Reset status fields on connection error
    except Exception as e: # Other unexpected errors
        print(f"ERROR: Unexpected error during serial initialization ({selected_port}): {e}")
        if hasattr(app, 'connect_button'):
            app.connect_button.text = "Unexpected\nerror" # Zeilenumbruch hinzugefügt
            app.connect_button.text_color = "#EF5350" # Red
        ser = None
        if hasattr(app, 'enable_cyclic_reading'): app.enable_cyclic_reading.value = 0
        log_mode_active = False
        reset_status_display() # Reset status fields on unexpected error
        print("INFO: Log mode deactivated due to unexpected initialization error.")

def send_serial_command_internal(command_char):
    """Sends a single character as a command to the serial interface."""
    global ser, log_mode_active # Declare log_mode_active here to set it on errors
    if not ser or not ser.is_open:
        print("WARN: Serial port not open. Please use 'Connect' button.")
        if hasattr(app, 'connect_button'):
            app.connect_button.text = "Not\nconnected!" # Zeilenumbruch hinzugefügt
            app.connect_button.text_color = "#FFA726"
        return False # Indicate failure, do not attempt to connect here

    if ser and ser.is_open:
        try:
            ser.write(command_char.encode('ascii')) # Commands are single ASCII characters
            print(f"Command sent: {command_char}")
        except serial.SerialException as e_write:
            print(f"ERROR: Error writing to serial port: {e_write}")
            if hasattr(app, 'connect_button'):
                app.connect_button.text = "Write\nerror!" # Zeilenumbruch hinzugefügt
                app.connect_button.text_color = "#EF5350" # Red
            # Do NOT close the port or change log_mode_active on a simple write error.
            return False
        except Exception as e_generic_send: # Other unexpected errors
            print(f"ERROR: Unexpected error sending command '{command_char}': {e_generic_send}")
            if hasattr(app, 'connect_button'):
                app.connect_button.text = "Send\nerror!" # Zeilenumbruch hinzugefügt
                app.connect_button.text_color = "#EF5350" # Red
            # Do NOT close the port or change log_mode_active on a generic send error.
            return False
        return True # Indicate success
    # This print should ideally not be reached if the initial check for ser and ser.is_open is done.
    print(f"WARN: Command '{command_char}' not sent, serial port state unexpected.")
    return False # Indicate failure

def send_serial_command(command_char): # Wrapper for external calls
    send_serial_command_internal(command_char)

def cleanup():
    """Cleanup tasks when closing the application."""
    global ser, connected_port, log_mode_active
    print("INFO: Application is closing.")
    # Ensure app.tk exists before trying to access winfo_exists
    # and also ensure app itself is not None
    app_exists = app and hasattr(app, 'tk') and app.tk

    if ser and ser.is_open:
        # If logging was active, try to turn it off on the radio before closing port
        if log_mode_active:
            print("INFO: Attempting to disable radio logging before closing port...")
            try:
                ser.write('t'.encode('ascii')) # Send 't' to toggle logging off
                # A short delay might be beneficial for the command to be processed by the radio
                # However, time.sleep() in a GUI app's main thread during cleanup can be tricky.
                # For now, just send and hope for the best, or make it non-blocking if issues arise.
                print("INFO: 't' command sent to attempt disabling radio logging.")
            except Exception as e_cleanup_write:
                print(f"WARN: Could not send 't' command during cleanup: {e_cleanup_write}")
        ser.close()
        print(f"Serial port {connected_port} closed.")
        connected_port = None
    if app_exists and app.tk.winfo_exists(): # Check if the window still exists
        app.destroy()
    sys.exit(0) # Clean exit

# --- Helper functions for display formatting ---
def format_agc_display(agc_value_str):
    try:
        agc_idx = int(agc_value_str)
        if agc_idx == 0: return "Auto"
        # Assumption: agc_idx=1 means Att 0dB, agc_idx=2 means Att 1dB etc.
        return f"Manual (Att {agc_idx -1}dB)"
    except ValueError:
        return "---" # Fallback if conversion fails

def format_battery_display(voltage_str):
    try:
        voltage = float(voltage_str)
        clamped_v = max(MIN_BATTERY_VOLTAGE, min(voltage, MAX_BATTERY_VOLTAGE))
        percentage = 0
        denominator = MAX_BATTERY_VOLTAGE - MIN_BATTERY_VOLTAGE
        if denominator > 0: # Avoid division by zero
            percentage = ((clamped_v - MIN_BATTERY_VOLTAGE) / denominator) * 100
        else: # If MIN_BATTERY_VOLTAGE == MAX_BATTERY_VOLTAGE
            percentage = 100 if voltage >= MAX_BATTERY_VOLTAGE else 0
        percentage = max(0, min(100, round(percentage))) # Ensure it's between 0 and 100
        return f"{voltage:.2f}V ({percentage}%)"
    except ValueError: # If voltage_str cannot be converted to float
        return f"{voltage_str}V (?%)" # Show raw value with question mark

def format_volume_display(volume_value):
    try:
        vol = int(volume_value)
        # Basic validation for volume range
        if not (0 <= vol <= MAX_VOLUME):
            print(f"WARN: Volume value {vol} out of expected range (0-{MAX_VOLUME}).")
            # Decide how to handle out-of-range: show error, clamp, or show raw
            return f"{volume_value} (ERR)" # Example: show error
        percentage = round((vol / MAX_VOLUME) * 100) if MAX_VOLUME > 0 else 0
        return f"{vol} ({percentage}%)"
    except ValueError:
        return f"{volume_value} (--%)"

def parse_and_update_radio_status(log_string):
    """Parses the log string from the radio and updates GUI elements."""
    # If not connected, don't try to update the GUI with potentially stale data
    if not (ser and ser.is_open):
        # This check helps prevent updates if data arrives after a disconnect
        # or if this function is somehow called when not connected.
        # The main reset of the display happens in toggle_connection.
        print("WARN: parse_and_update_radio_status called but not connected. Skipping update.")
        return

    try:
        parts = log_string.split(',')
        if len(parts) < 15:
            print(f"WARN: Incomplete log string: {log_string} (expected 15 parts, got {len(parts)})")
            return

        # Extracting some key values (indices are 0-based) - comments for clarity
        fw_version = parts[0]
        current_frequency_khz = int(parts[1])
        try:
            current_bfo_hz = int(parts[2])
            current_cal_hz = int(parts[3])
        except ValueError: # Handles empty string or non-integer
            current_bfo_hz = 0
            current_cal_hz = 0
        band_name = parts[4] # Band name
        current_mode = parts[5] # Current mode
        volume_str = parts[9] # Volume (as string for format_volume_display)
        step_size = parts[6] # New for Step Size
        bandwidth = parts[7] # New for Bandwidth
        agc_value_str = parts[8] # New for AGC Status (as string for format_agc_display)
        rssi = int(parts[10]) # RSSI value
        # Ensure band_name is not empty before using
        if not band_name:
            band_name = "Unknown" # Fallback for empty band name
        snr = int(parts[11])
        battery_voltage_str = parts[13] # Neu für Batteriespannung (als String)
        
        # Update GUI elements (assuming they exist and are named app.status_frequency etc.)
        # Frequency display logic: FM in MHz, AM/SSB and others in kHz
        if current_mode == "FM":
            # FM: currentFrequency is in 10 kHz units, display in MHz
            display_frequency_mhz = (current_frequency_khz * 10) / 1000.0
            app.status_frequency.value = f"{display_frequency_mhz:.2f}MHz"
        elif current_mode in ["LSB", "USB"]:
            # SSB: Display Frequency (Hz) = (currentFrequency kHz * 1000) + currentBFO Hz
            # current_frequency_khz is already in kHz for SSB
            actual_freq_khz = current_frequency_khz + (current_bfo_hz / 1000.0)
            app.status_frequency.value = f"{actual_freq_khz:.1f}kHz (Calibration: {current_cal_hz}Hz)"
        else:
            # AM and other modes: currentFrequency is in 1 kHz units, display in kHz
            display_frequency_khz = current_frequency_khz
            app.status_frequency.value = f"{display_frequency_khz}kHz"

        if hasattr(app, 'status_fw_version'):
            fw_display_text = "---"  # Default value if fw_version is empty or invalid
            
            # fw_version is the value from parts[0]
            if isinstance(fw_version, str) and fw_version.strip():
                raw_fw = fw_version.strip()
                # Specific case for format "201" -> "2.01"
                if len(raw_fw) == 3 and raw_fw.isdigit():
                    major = raw_fw[0]
                    minor = raw_fw[1:]
                    fw_display_text = f"{major}.{minor}" # "v" entfernt
                else:
                    # Remove "v" or "V" from the beginning, if present
                    if raw_fw.lower().startswith('v'):
                        fw_display_text = raw_fw[1:]
                    else:
                        fw_display_text = raw_fw
            app.status_fw_version.value = fw_display_text
        if hasattr(app, 'status_mode_band'): # Order changed to Band/Mode
            app.status_mode_band.value = f"{band_name}/{current_mode}"
        if hasattr(app, 'status_volume'): # Now uses format_volume_display
            app.status_volume.value = format_volume_display(volume_str)
        if hasattr(app, 'status_step'):
            app.status_step.value = f"{step_size}"
        if hasattr(app, 'status_bw'):
            app.status_bw.value = f"{bandwidth}"
        if hasattr(app, 'status_agc'):
            app.status_agc.value = format_agc_display(agc_value_str)
        if hasattr(app, 'status_battery'):
            app.status_battery.value = format_battery_display(battery_voltage_str)
        if hasattr(app, 'status_signal'):
            app.status_signal.value = f"RSSI: {rssi}dBuV, SNR: {snr}dB"

    except ValueError as e:
        print(f"ERROR: Error parsing numeric value in log string: {log_string} - {e}")
    except IndexError as e:
        print(f"ERROR: Index error parsing log string (not enough parts?): {log_string} - {e}")
    except Exception as e:
        print(f"ERROR: Unexpected error parsing radio status '{log_string}': {e}")

def check_serial_data():
    """Periodically checks for serial data if log mode is active."""
    global ser, log_mode_active
    # Diagnostic print can be re-enabled if needed:
    # if ser: print(f"CSR: log={log_mode_active}, open={ser.is_open}, wait={ser.in_waiting if ser.is_open else 'N/A'}")

    if log_mode_active and ser and ser.is_open and ser.in_waiting > 0: # Check log_mode_active and connection first
        try:
            log_line = ser.readline().decode('ascii', errors='ignore').strip()
            if log_line:
                # print(f"Radio Log: {log_line}") # For debugging
                parse_and_update_radio_status(log_line) # Ensure this is called
        except Exception as e:
            print(f"Error reading from serial port: {e}")
            # Consider if log_mode_active should be set to False here if reading fails consistently

def toggle_cyclic_reading():
    global log_mode_active, ser
    new_log_state = app.enable_cyclic_reading.value == 1
    print(f"INFO: Checkbox toggled. Requested log state: {new_log_state}")

    if not ser or not ser.is_open:
        print("WARN: Cannot change cyclic reading: Serial port not open.")
        app.enable_cyclic_reading.value = 0
        if hasattr(app, 'connect_button'): # Update connect button with warning
            app.connect_button.text = "Not\nconnected!"
            app.connect_button.text_color = "#FFA726" # Orange
        log_mode_active = False
        return

    # Nur senden, wenn der Status sich wirklich ändert
    if log_mode_active != new_log_state:
        if send_serial_command_internal('t'):
            log_mode_active = new_log_state
            print(f"INFO: Cyclic reading {'enabled' if log_mode_active else 'disabled'} by checkbox.")
        else:
            print("WARN: Failed to toggle log mode. Reverting checkbox.")
            app.enable_cyclic_reading.value = 1 if log_mode_active else 0
    else:
        print("INFO: Log mode already in requested state.")


# --- GUI Setup ---
# Get the directory where the script is located
script_dir = os.path.dirname(__file__)

# Colors for Dark Theme
# Window height adjusted for new status fields
app = App(title="Mini-Radio Control", width=410, height=880, layout="grid") # Height slightly increased
app.encoder_icon_scaled = None # Store scaled icon image on the app object
app.bg = '#2E2E2E' # Dark background for Dark Theme
dark_theme_text_color = "#E0E0E0" # Light gray for text
dark_theme_button_bg = "#4A4A4A"  # Medium dark gray for buttons
dark_theme_combo_bg = "#3A3A3A" # Slightly lighter gray for dropdown
dark_theme_combo_text_color = "#E0E0E0" # Light gray for dropdown text

BAUD_RATES = ["9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"]
# Get detailed information about serial ports
ports_info = list(serial.tools.list_ports.comports())
available_ports = [p.device for p in ports_info]
auto_selected_port = None

if not available_ports:
    available_ports = ["No ports found"] # Fallback if no ports are found
    print("No serial ports found.")
else:
    print(f"Found ports: {available_ports}")
    # Auto-Auswahl Logik
    # Keywords to look for in port description or name
    PORT_KEYWORDS = ["CH340", "CP210", "FTDI", "USB SERIAL", "SERIAL", "ACM", "USB-SERIAL", "UART"]
    for port_obj in ports_info:
        desc = (port_obj.description or "").upper()
        name = (port_obj.name or "").upper() # port.name is usually the base name like 'ttyUSB0' or 'COM3'
        device_path = port_obj.device
        if any(keyword in desc or keyword in name for keyword in PORT_KEYWORDS):
            auto_selected_port = device_path
            print(f"Auto-selected port '{auto_selected_port}' based on keywords in description/name.")
            break # Use the first match

app.tk.resizable(False, False) # Window size not resizable
app.when_closed = cleanup      # Call cleanup function on closing

# Add uniform padding to the window
app.tk.config(padx=10, pady=10)

# --- Port Selection and Connect ---
current_grid_row = 0 # Start directly with port selection in row 0
Text(app, text="Serial Port:", grid=[0, current_grid_row], align="left").text_color = dark_theme_text_color # Starts now in row 1
app.port_selector = Combo(app, options=available_ports, grid=[1, current_grid_row], width=15, align="left")
app.port_selector.bg = dark_theme_combo_bg
app.port_selector.text_color = dark_theme_combo_text_color

# Port-Vorauswahl
if auto_selected_port and auto_selected_port in available_ports:
    app.port_selector.value = auto_selected_port
elif available_ports and available_ports[0] != "No ports found":
    # Fallback: Select the last port if auto-selection was not successful
    app.port_selector.value = available_ports[-1] # Selects the last port in the list

# Connect button spans two rows and has an increased height
app.connect_button = PushButton(app, text="Connect", command=toggle_connection, grid=[2, current_grid_row, 1, 2], width=10, height=3)
app.connect_button.bg = dark_theme_button_bg
app.connect_button.text_color = dark_theme_text_color # Standard Textfarbe für den Button
current_grid_row += 1

# --- Baud Rate Selection ---
Text(app, text="Baud Rate:", grid=[0, current_grid_row], align="left").text_color = dark_theme_text_color
app.baud_rate_selector = Combo(app, options=BAUD_RATES, selected=str(DEFAULT_BAUD_RATE), grid=[1, current_grid_row], width=15, align="left")
app.baud_rate_selector.bg = dark_theme_combo_bg
app.baud_rate_selector.text_color = dark_theme_combo_text_color
current_grid_row += 1


# Empty line for spacing above the checkbox
Text(app, text="", grid=[0, current_grid_row, 3, 1]) # Span all relevant columns
current_grid_row += 1

# --- Checkbox for Cyclic Reading ---
app.enable_cyclic_reading = CheckBox(app, text="Enable Cyclic Reading", command=toggle_cyclic_reading, grid=[0, current_grid_row, 3, 1], align="left")
app.enable_cyclic_reading.text_color = dark_theme_text_color
# Access the underlying tkinter widget and set relief to "flat"
app.enable_cyclic_reading.tk.config(relief="flat", borderwidth=0)
current_grid_row += 1

# --- Control Definitions ---
# Structure: (Label Text, Command1, Text Button1, Command2, Text Button2, Type ["pair" or "single"])
controls_data = [
    ("Encoder Button",      None, None,          None, None,       "single"), # Text "Press" (txt1) removed, will use icon
    ("Encoder Rotate",      'R', "Right",        'r', "Left",      "pair"),
    ("Band",                'B', "Next",    	 'b', "Previous",  "pair"), # Band wieder vor Mode
    ("Mode",               	'M', "Next",    	 'm', "Previous",  "pair"), # Mode wieder nach Band
    ("Calibration",        	'I', "Up",        	 'i', "Down",      "pair"),
    ("Step Size",        	'S', "Next",     	 's', "Previous",  "pair"),
    ("Bandwidth",          	'W', "Next",     	 'w', "Previous",  "pair"),
    ("AGC/Att",             'A', "Next",         'a', "Previous",  "pair"),
    ("Volume",          	'V', "Up",      	 'v', "Down",      "pair"),
    ("Backlight",    		'L', "Brighter",     'l', "Dimmer",    "pair"),
    ("Sleep",               'O', "On",         	 'o', "Off",       "pair"),
]

# --- Radio Status Display Area ---
# This will be row 1 (after Port selection in row 0)
status_text_config = {"align": "left", "width": "fill"} # text_color removed, set individually

# Empty line for spacing above the status area
Text(app, text="", grid=[0, current_grid_row, 3, 1]) # Span all relevant columns
current_grid_row += 1

fw_label = Text(app, text="FW Version:", grid=[0, current_grid_row], **status_text_config)
fw_label.text_color = dark_theme_text_color
app.status_fw_version = Text(app, text="---", grid=[1, current_grid_row, 2, 1], **status_text_config) # Spans 2 cols
app.status_fw_version.text_color = dark_theme_text_color
current_grid_row += 1

battery_label = Text(app, text="Battery:", grid=[0, current_grid_row], **status_text_config)
battery_label.text_color = dark_theme_text_color
app.status_battery = Text(app, text="--- (--%)", grid=[1, current_grid_row, 2, 1], **status_text_config) # Corrected placeholder
app.status_battery.text_color = dark_theme_text_color
current_grid_row += 1

freq_label = Text(app, text="Frequency:", grid=[0, current_grid_row], **status_text_config)
freq_label.text_color = dark_theme_text_color
app.status_frequency = Text(app, text="---", grid=[1, current_grid_row, 2, 1], **status_text_config) # Spans 2 cols, space removed
app.status_frequency.text_color = dark_theme_text_color
current_grid_row += 1

mode_band_label = Text(app, text="Band/Mode:", grid=[0, current_grid_row], **status_text_config)
mode_band_label.text_color = dark_theme_text_color
app.status_mode_band = Text(app, text="---/---", grid=[1, current_grid_row, 2, 1], **status_text_config)
app.status_mode_band.text_color = dark_theme_text_color
current_grid_row += 1

step_label = Text(app, text="Step Size:", grid=[0, current_grid_row], **status_text_config)
step_label.text_color = dark_theme_text_color
app.status_step = Text(app, text="---", grid=[1, current_grid_row, 2, 1], **status_text_config)
app.status_step.text_color = dark_theme_text_color
current_grid_row += 1

bw_label = Text(app, text="Bandwidth:", grid=[0, current_grid_row], **status_text_config)
bw_label.text_color = dark_theme_text_color
app.status_bw = Text(app, text="---", grid=[1, current_grid_row, 2, 1], **status_text_config)
app.status_bw.text_color = dark_theme_text_color
current_grid_row += 1

agc_label = Text(app, text="AGC Status:", grid=[0, current_grid_row], **status_text_config)
agc_label.text_color = dark_theme_text_color
app.status_agc = Text(app, text="---", grid=[1, current_grid_row, 2, 1], **status_text_config)
app.status_agc.text_color = dark_theme_text_color
current_grid_row += 1

signal_label = Text(app, text="Signal:", grid=[0, current_grid_row], **status_text_config)
signal_label.text_color = dark_theme_text_color
app.status_signal    = Text(app, text="RSSI: --, SNR: --", grid=[1, current_grid_row, 2, 1], **status_text_config)
app.status_signal.text_color = dark_theme_text_color
current_grid_row += 1 

volume_label = Text(app, text="Volume:", grid=[0, current_grid_row], **status_text_config)
volume_label.text_color = dark_theme_text_color
app.status_volume    = Text(app, text="-- (--%)", grid=[1, current_grid_row, 2, 1], **status_text_config) # Corrected placeholder
app.status_volume.text_color = dark_theme_text_color
current_grid_row += 1

# Empty line for spacing below the status area
Text(app, text="", grid=[0, current_grid_row, 3, 1]) # Span all relevant columns
current_grid_row += 1 # Increment row for the actual controls to start below status

def reset_status_display():
    """Resets all status display Text widgets to their initial placeholder values."""
    if hasattr(app, 'status_fw_version'): app.status_fw_version.value = "---"
    if hasattr(app, 'status_battery'): app.status_battery.value = "--- (--%)"
    if hasattr(app, 'status_frequency'): app.status_frequency.value = "---"
    if hasattr(app, 'status_mode_band'): app.status_mode_band.value = "---/---"
    if hasattr(app, 'status_step'): app.status_step.value = "---"
    if hasattr(app, 'status_bw'): app.status_bw.value = "---"
    if hasattr(app, 'status_agc'): app.status_agc.value = "---"
    if hasattr(app, 'status_signal'): app.status_signal.value = "RSSI: --, SNR: --"
    if hasattr(app, 'status_volume'): app.status_volume.value = "-- (--%)"
    print("INFO: Status display fields reset.")


for label, cmd1, txt1, cmd2, txt2, ctrl_type in controls_data:
    lbl = Text(app, text=f"{label}:", grid=[0, current_grid_row], align="left")
    lbl.text_color = dark_theme_text_color

    # text_color is set after creation
    button_properties = {"width": 10, "align": "right"}

    if ctrl_type == "pair":
        # Decrement button (cmd2, txt2) on the left
        btn_decrement = PushButton(app, text=txt2, command=lambda c=cmd2: send_serial_command(c), grid=[1, current_grid_row], **button_properties)
        btn_decrement.bg = dark_theme_button_bg
        btn_decrement.text_color = dark_theme_text_color

        # Increment button (cmd1, txt1) on the right
        btn_increment = PushButton(app, text=txt1, command=lambda c=cmd1: send_serial_command(c), grid=[2, current_grid_row], **button_properties)
        btn_increment.bg = dark_theme_button_bg
        btn_increment.text_color = dark_theme_text_color
    elif ctrl_type == "single":
        # Use a Picture widget as a clickable icon button
        # cmd1 is the command (e.g., 'e'), txt1 is None (icon is used instead of text)
        if label == "Encoder Button": # Be specific for the encoder button
            icon_filename = "buttonpress.png" # Name of your icon file
            icon_path_abs = os.path.join(script_dir, icon_filename)
            ICON_SIZE = (210, 48) # Desired icon size in pixels (width, height) - Doubled size

            pil_img = Image.open(icon_path_abs)
            # Resize the image using LANCZOS for better quality
            app.encoder_icon_scaled = pil_img.resize(ICON_SIZE, Image.Resampling.LANCZOS)

            # Place the Picture widget directly in the app's grid, spanning 2 columns and aligned left.
            picture_button = Picture(
                app, # Parent is the main app
                image=app.encoder_icon_scaled,
                grid=[1, current_grid_row, 2, 1], # Spans columns 1 & 2
                align="right" # Align the picture to the left within the spanned columns
            )
            # cmd1 is 'e' for the Encoder Button from controls_data.
            picture_button.when_clicked = lambda event_data: send_serial_command("e")

    current_grid_row += 1

# Auto-connect on start attempt (currently commented out)
#app.after(100, init_serial)

# Repeat the check_serial_data function every 200ms
app.repeat(200, check_serial_data)

app.display()