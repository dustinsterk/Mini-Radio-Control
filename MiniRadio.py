#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import serial  # Für die serielle Kommunikation
import serial.tools.list_ports # Zum Auflisten der seriellen Ports
from guizero import App, PushButton, Text, Combo # Combo hinzugefügt
from guizero import CheckBox # Checkbox hinzugefügt (Großschreibung korrigiert)

# --- Konfiguration ---
# SERIAL_PORT wird durch dynamische Auswahl ersetzt
BAUD_RATE = 115200            # Übliche Baudrate, ggf. anpassen, falls Ihr Radio eine andere verwendet

# --- Globale Variable für die serielle Verbindung ---
ser = None
connected_port = None # Speichert den Namen des aktuell verbundenen Ports
log_mode_active = False # Wird jetzt durch die Checkbox gesteuert

def init_serial():
    """Initialisiert die serielle Verbindung."""
    global ser, connected_port, log_mode_active # log_mode_active hinzugefügt
    try:
        # Schließe eine eventuell bestehende Verbindung, bevor eine neue geöffnet wird
        if ser and ser.is_open:
            print(f"Closing existing connection to {connected_port}")
            ser.close()

        selected_port = app.port_selector.value # Port aus dem Dropdown lesen
        if not selected_port or selected_port == "No ports found": # Changed German string
            print("No valid port selected.")
            if hasattr(app, 'connect_button'): # Nur aktualisieren, wenn Button existiert
                app.connect_button.text = "No port selected" # Translated
                app.connect_button.text_color = "#FFA726" # Orange
            return

        print(f"Attempting connection to {selected_port} at {BAUD_RATE} baud...")
        ser = serial.Serial(selected_port, BAUD_RATE, timeout=1)
        connected_port = selected_port # Verbundenen Port speichern
        print(f"Successfully connected to {connected_port}.")
        if hasattr(app, 'connect_button'): # Check if button exists before updating
            app.connect_button.text = f"Connected" # Changed from "Verbunden" to "Connected"
            app.connect_button.text_color = "#66BB6A" # Grün

        # On successful connection, log_mode_active state is determined by the checkbox handler.
        # init_serial itself does not send 't' or change log_mode_active on success.

    except serial.SerialException as e:
        print(f"ERROR: Error opening serial port {selected_port}: {e}")
        if hasattr(app, 'connect_button'):
            app.connect_button.text = "Connection failed" # Translated
            app.connect_button.text_color = "#EF5350" # Rot
        ser = None # Sicherstellen, dass ser None ist, wenn die Verbindung fehlschlägt
        if hasattr(app, 'enable_cyclic_reading'): app.enable_cyclic_reading.value = 0 # Uncheck if connection fails
        log_mode_active = False # Ensure log mode is off
    except Exception as e: # Andere unerwartete Fehler
        print(f"ERROR: Unexpected error during serial initialization ({selected_port}): {e}")
        if hasattr(app, 'connect_button'):
            app.connect_button.text = "Unexpected error" # Translated
            app.connect_button.text_color = "#EF5350" # Rot
        ser = None
        if hasattr(app, 'enable_cyclic_reading'): app.enable_cyclic_reading.value = 0
        log_mode_active = False
        print("INFO: Log mode deactivated due to unexpected initialization error.")

def send_serial_command_internal(command_char, is_toggle_command=False):
    """Sendet ein einzelnes Zeichen als Kommando an die serielle Schnittstelle."""
    global ser, log_mode_active # log_mode_active hier deklarieren, um es bei Fehlern zu setzen
    if not ser or not ser.is_open:
        print("WARN: Serial port not open. Please use 'Connect' button.")
        if hasattr(app, 'connect_button'):
            app.connect_button.text = "Not connected!"
            app.connect_button.text_color = "#FFA726"
        return False # Indicate failure, do not attempt to connect here

    if ser and ser.is_open:
        try:
            ser.write(command_char.encode('ascii')) # Kommandos sind einzelne ASCII-Zeichen
            print(f"Command sent: {command_char}")
        except serial.SerialException as e_write:
            print(f"ERROR: Error writing to serial port: {e_write}")
            if hasattr(app, 'connect_button'):
                app.connect_button.text = "Write error!" # Translated
                app.connect_button.text_color = "#EF5350" # Rot
            if ser: ser.close(); ser = None
            if hasattr(app, 'enable_cyclic_reading'): app.enable_cyclic_reading.value = 0
            log_mode_active = False # Ensure log mode is off
            print("INFO: Log mode deactivated due to serial write error.")
            return False
        except Exception as e_generic_send: # Andere unerwartete Fehler
            print(f"ERROR: Unexpected error sending command '{command_char}': {e_generic_send}")
            if hasattr(app, 'connect_button'):
                app.connect_button.text = "Send error!" # Translated
                app.connect_button.text_color = "#EF5350" # Rot
            if ser: ser.close(); ser = None
            if hasattr(app, 'enable_cyclic_reading'): app.enable_cyclic_reading.value = 0
            log_mode_active = False # Ensure log mode is off
            print("INFO: Log mode deactivated due to unexpected send error.")
            return False
        return True # Indicate success
    # This else block should ideally not be reached if the initial check for ser and ser.is_open is done.
    # However, to be safe:
    print(f"WARN: Command '{command_char}' not sent, serial port state unexpected.")
    return False # Indicate failure

def send_serial_command(command_char): # Wrapper for external calls
    send_serial_command_internal(command_char)

def cleanup():
    """Aufräumarbeiten beim Schließen der Anwendung."""
    global ser, connected_port, log_mode_active
    print("INFO: Application is closing.")
    if ser and ser.is_open:
        ser.close()
        print(f"Serial port {connected_port} closed.")
        connected_port = None
    if app.tk.winfo_exists(): # Prüfen, ob das Fenster noch existiert
        app.destroy()
    sys.exit(0) # Sauberes Beenden

def parse_and_update_radio_status(log_string):
    """Parses the log string from the radio and updates GUI elements."""
    try:
        parts = log_string.split(',')
        if len(parts) < 15:
            print(f"WARN: Incomplete log string: {log_string} (expected 15 parts, got {len(parts)})")
            return

        # Extracting some key values (indices are 0-based)
        fw_version = parts[0]
        current_frequency_khz = int(parts[1])
        try:
            current_bfo_hz = int(parts[2])
        except ValueError: # Handles empty string or non-integer
            current_bfo_hz = 0
        band_name = parts[4]
        current_mode = parts[5]
        volume = int(parts[9])
        rssi = int(parts[10])
        # Ensure band_name is not empty before using
        if not band_name:
            band_name = "Unknown"
        snr = int(parts[11])

        # Update GUI elements (assuming they exist and are named app.status_frequency etc.)
        # Frequency display logic: FM in MHz, AM/SSB and others in kHz
        if current_mode == "FM":
            # FM: currentFrequency is in 10 kHz units, display in MHz
            display_frequency_mhz = (current_frequency_khz * 10) / 1000.0
            app.status_frequency.value = f"{display_frequency_mhz:.2f} MHz"
        elif current_mode in ["LSB", "USB"]:
            # SSB: Display Frequency (Hz) = (currentFrequency kHz * 1000) + currentBFO Hz
            # current_frequency_khz is already in kHz for SSB
            actual_freq_khz = current_frequency_khz + (current_bfo_hz / 1000.0)
            app.status_frequency.value = f"{actual_freq_khz:.1f} kHz (BFO: {current_bfo_hz}Hz)"
        else:
            # AM and other modes: currentFrequency is in 1 kHz units, display in kHz
            display_frequency_khz = current_frequency_khz
            app.status_frequency.value = f"{display_frequency_khz} kHz"

        if hasattr(app, 'status_fw_version'):
            fw_display_text = "---"  # Standardwert, falls fw_version leer oder ungültig ist
            
            # fw_version ist hier der Wert aus parts[0]
            if isinstance(fw_version, str) and fw_version.strip():
                raw_fw = fw_version.strip()
                # Spezifischer Fall für das Format "201" -> "v2.01"
                if len(raw_fw) == 3 and raw_fw.isdigit():
                    major = raw_fw[0]
                    minor = raw_fw[1:]
                    fw_display_text = f"v{major}.{minor}"
                else:
                    # Allgemeiner Fallback:
                    # Wenn es numerisch ist und nicht mit 'v' beginnt, 'v' voranstellen
                    if not raw_fw.lower().startswith('v') and \
                       (raw_fw.isdigit() or (raw_fw.count('.') == 1 and raw_fw.replace('.', '', 1).isdigit())):
                        fw_display_text = f"v{raw_fw}"
                    else:  # Ansonsten so anzeigen, wie es ist (z.B. "alpha", "v1.2.3-beta")
                        fw_display_text = raw_fw
            app.status_fw_version.value = fw_display_text
        if hasattr(app, 'status_mode_band'):
            app.status_mode_band.value = f"{current_mode}/{band_name}" # Removed spaces around '/'
        if hasattr(app, 'status_volume'):
            app.status_volume.value = f"{volume}" # Removed "Vol: " prefix
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
        log_mode_active = False
        return

    # Nur senden, wenn der Status sich wirklich ändert
    if log_mode_active != new_log_state:
        if send_serial_command_internal('t', is_toggle_command=True):
            log_mode_active = new_log_state
            print(f"INFO: Cyclic reading {'enabled' if log_mode_active else 'disabled'} by checkbox.")
        else:
            print("WARN: Failed to toggle log mode. Reverting checkbox.")
            app.enable_cyclic_reading.value = 1 if log_mode_active else 0
    else:
        print("INFO: Log mode already in requested state.")

# --- GUI Setup ---
# Fensterbreite erhöht und Höhe reduziert
app = App(title="Mini-Radio Control", width=410, height=755, layout="grid") # Adjusted width, increased height for new spacer
app.bg = '#2E2E2E' # Dunkler Hintergrund für Dark Theme

# Farben für Dark Theme
dark_theme_text_color = "#E0E0E0" # Helles Grau für Text
dark_theme_button_bg = "#4A4A4A"  # Mitteldunkles Grau für Buttons
dark_theme_combo_bg = "#3A3A3A" # Etwas helleres Grau für Dropdown
dark_theme_combo_text_color = "#E0E0E0" # Helles Grau für Dropdown-Text

# Verfügbare serielle Ports ermitteln
available_ports = [port.device for port in serial.tools.list_ports.comports()]
if not available_ports:
    available_ports = ["No ports found"] # Fallback, wenn keine Ports da sind
    print("No serial ports found.")
else:
    print(f"Found ports: {available_ports}")

app.tk.resizable(False, False) # Window size not resizable
app.when_closed = cleanup      # Funktion cleanup beim Schließen aufrufen

# Einheitlichen Rand (Padding) zum Fenster hinzufügen
app.tk.config(padx=10, pady=10)

# --- Port Auswahl und Verbinden ---
current_grid_row = 0 # Beginnen direkt mit der Port-Auswahl in Zeile 0
Text(app, text="Serial Port:", grid=[0, current_grid_row], align="left").text_color = dark_theme_text_color # Starts now in row 1
app.port_selector = Combo(app, options=available_ports, grid=[1, current_grid_row], width=15, align="left")
app.port_selector.bg = dark_theme_combo_bg
app.port_selector.text_color = dark_theme_combo_text_color
# Standardmäßig den letzten Port aus der Liste auswählen, falls Ports vorhanden sind
if available_ports and available_ports[0] != "No ports found":
    app.port_selector.value = available_ports[-1] # Wählt den letzten Port in der Liste

app.connect_button = PushButton(app, text="Connect", command=init_serial, grid=[2, current_grid_row], width=10) # Corrected grid position
app.connect_button.bg = dark_theme_button_bg
app.connect_button.text_color = dark_theme_text_color # Standard Textfarbe für den Button
current_grid_row += 1

# Leere Zeile für Abstand über der Checkbox
Text(app, text="", grid=[0, current_grid_row, 3, 1]) # Span all relevant columns
current_grid_row += 1

# --- Checkbox for Cyclic Reading ---
app.enable_cyclic_reading = CheckBox(app, text="Enable Cyclic Reading", command=toggle_cyclic_reading, grid=[0, current_grid_row, 3, 1], align="left")
app.enable_cyclic_reading.text_color = dark_theme_text_color
current_grid_row += 1

# --- Definition der Steuerelemente ---
# Struktur: (Label-Text, Kommando1, Text Button1, Kommando2, Text Button2, Typ ["pair" oder "single"])
controls_data = [
    ("Encoder Rotate",      'R', "Right",        'r', "Left",      "pair"),
    ("Encoder Button",      'e', "Press",        None, None,       "single"),
    ("Volume",          	'V', "Up",      	 'v', "Down",      "pair"),
    ("Band",                'B', "Next",    	 'b', "Previous",  "pair"),
    ("Mode",               	'M', "Next",    	 'm', "Previous",  "pair"),
    ("Step Size",        	'S', "Next",     	 's', "Previous",  "pair"),
    ("Bandwidth",          	'W', "Next",     	 'w', "Previous",  "pair"),
    ("AGC/Att",             'A', "Up",        	 'a', "Down",      "pair"),
    ("Backlight",    		'L', "Brighter",     'l', "Dimmer",    "pair"),
    ("Calibration",        	'I', "Up",        	 'i', "Down",      "pair"),
    ("Sleep",               'O', "On",         	 'o', "Off",       "pair"),
]

# --- Radio Status Display Area ---
# This will be row 1 (after Port selection in row 0)
status_text_config = {"align": "left", "width": "fill"} # Removed text_color

# Leere Zeile für Abstand über dem Statusbereich
Text(app, text="", grid=[0, current_grid_row, 3, 1]) # Span all relevant columns
current_grid_row += 1

fw_label = Text(app, text="FW Version:", grid=[0, current_grid_row], **status_text_config)
fw_label.text_color = dark_theme_text_color
app.status_fw_version = Text(app, text="---", grid=[1, current_grid_row, 2, 1], **status_text_config) # Spans 2 cols
app.status_fw_version.text_color = dark_theme_text_color
current_grid_row += 1
freq_label = Text(app, text="Frequency:", grid=[0, current_grid_row], **status_text_config)
freq_label.text_color = dark_theme_text_color
app.status_frequency = Text(app, text="--- MHz", grid=[1, current_grid_row, 2, 1], **status_text_config) # Spans 2 cols
app.status_frequency.text_color = dark_theme_text_color
current_grid_row += 1

mode_band_label = Text(app, text="Mode/Band:", grid=[0, current_grid_row], **status_text_config)
mode_band_label.text_color = dark_theme_text_color
app.status_mode_band = Text(app, text="---/---", grid=[1, current_grid_row, 2, 1], **status_text_config)
app.status_mode_band.text_color = dark_theme_text_color
current_grid_row += 1

volume_label = Text(app, text="Volume:", grid=[0, current_grid_row], **status_text_config)
volume_label.text_color = dark_theme_text_color
app.status_volume    = Text(app, text="--", grid=[1, current_grid_row, 2, 1], **status_text_config)
app.status_volume.text_color = dark_theme_text_color
current_grid_row += 1

signal_label = Text(app, text="Signal:", grid=[0, current_grid_row], **status_text_config)
signal_label.text_color = dark_theme_text_color
app.status_signal    = Text(app, text="RSSI: --, SNR: --", grid=[1, current_grid_row, 2, 1], **status_text_config)
app.status_signal.text_color = dark_theme_text_color
current_grid_row += 1 

# Leere Zeile für Abstand unter dem Statusbereich
Text(app, text="", grid=[0, current_grid_row, 3, 1]) # Span all relevant columns
current_grid_row += 1 # Increment row for the actual controls to start below status

for label, cmd1, txt1, cmd2, txt2, ctrl_type in controls_data:
    lbl = Text(app, text=f"{label}:", grid=[0, current_grid_row], align="left")
    lbl.text_color = dark_theme_text_color

    # text_color wird nach der Erstellung gesetzt
    button_properties = {"width": 10}

    if ctrl_type == "pair":
        # Decrement-Button (cmd2, txt2) links
        btn_decrement = PushButton(app, text=txt2, command=lambda c=cmd2: send_serial_command(c), grid=[1, current_grid_row], **button_properties)
        btn_decrement.bg = dark_theme_button_bg
        btn_decrement.text_color = dark_theme_text_color

        # Increment-Button (cmd1, txt1) rechts
        btn_increment = PushButton(app, text=txt1, command=lambda c=cmd1: send_serial_command(c), grid=[2, current_grid_row], **button_properties)
        btn_increment.bg = dark_theme_button_bg
        btn_increment.text_color = dark_theme_text_color
    elif ctrl_type == "single":
        # Einzelner Button erstreckt sich über die Breite von zwei normalen Buttons
        # Feste Breite (z.B. Summe der Breiten zweier gepaarter Buttons) und Zentrierung des Widgets
        single_button_config = {
            "width": 27, # Zeichenbreite, passend zu 2x width=10 der anderen Buttons
            "align": "right" # Aligns the widget within the spanned columns, as requested
        }
        btn_single = PushButton(
            app,
            text=txt1,
            command=lambda c=cmd1: send_serial_command(c),
            grid=[1, current_grid_row, 2, 1], # Spans columns 1 and 2 (original button columns)
            **single_button_config)
        btn_single.bg = dark_theme_button_bg
        btn_single.text_color = dark_theme_text_color
    current_grid_row += 1

# Auto-Verbindung beim Startversuch
#app.after(100, init_serial)

# Repeat the check_serial_data function every 300ms
app.repeat(300, check_serial_data)

app.display()