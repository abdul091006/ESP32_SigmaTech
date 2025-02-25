import network
import time
import urequests
import machine

# 🔹 Konfigurasi WiFi & Ubidots
SSID = "APKel4"
PASSWORD = "aboutyou"
UBIDOTS_TOKEN = "BBUS-V2fREN0LZcJDUBCbZ2UXtDnbImhS3D"
DEVICE_LABEL = "demo-machine"  # Ubidots lebih suka lowercase tanpa spasi

# 🔹 Variabel di Ubidots
VARIABLE_LABEL_PIR = "pir"
VARIABLE_LABEL_LDR = "ldr"
VARIABLE_LABEL_TEMP = "temperature"

# 🔹 Inisialisasi PIN
pir = machine.Pin(5, machine.Pin.IN)  # PIR di GPIO 5
ldr = machine.ADC(machine.Pin(32))  # LDR di GPIO 32
temp_sensor = machine.ADC(machine.Pin(33))  # LM35 di GPIO 33

# 🔹 Konfigurasi ADC (agar bisa membaca hingga 3.3V)
ldr.atten(machine.ADC.ATTN_11DB)
temp_sensor.atten(machine.ADC.ATTN_11DB)

def connect_wifi():
    """Menghubungkan ESP32 ke WiFi"""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(SSID, PASSWORD)
        for _ in range(20):  # Tunggu max 20 detik
            if wlan.isconnected():
                break
            time.sleep(1)
    if wlan.isconnected():
        print("Connected! IP:", wlan.ifconfig()[0])
    else:
        print("Failed to connect to WiFi!")

def read_sensors():
    """Membaca nilai PIR, LDR, dan Sensor Suhu"""
    pir_value = pir.value()
    ldr_value = ldr.read()  # Nilai ADC 0-4095

    # 🔥 Perbaikan: Konversi nilai suhu lebih akurat
    temp_raw = temp_sensor.read()  # Nilai ADC mentah
    voltage = temp_raw * 3.3 / 4095  # Konversi ke voltase
    temp_value = round(voltage * 100, 2)  # LM35: 10mV per 1°C → dikali 100

    print(f"DEBUG - PIR: {pir_value}, LDR: {ldr_value}, TEMP: {temp_value}°C")  # Debugging
    return pir_value, ldr_value, temp_value

def send_to_ubidots(pir_val, ldr_val, temp_val):
    """Mengirim data ke Ubidots"""
    url = f"https://industrial.api.ubidots.com/api/v1.6/devices/{DEVICE_LABEL}"
    headers = {
        "X-Auth-Token": UBIDOTS_TOKEN,
        "Content-Type": "application/json"
    }

    # 🔥 Perbaikan: Pastikan data dalam format yang benar
    data = {
        VARIABLE_LABEL_PIR: {"value": int(pir_val)},  # Pastikan integer
        VARIABLE_LABEL_LDR: {"value": int(ldr_val)},  # Pastikan integer
        VARIABLE_LABEL_TEMP: {"value": temp_val}  # Float dengan 2 desimal
    }

    try:
        print("Sending data:", data)  # Debugging output
        response = urequests.post(url, json=data, headers=headers)
        print("Send Status:", response.status_code)
        print("Response:", response.text)  # Debugging output
        response.close()
    except Exception as e:
        print("Send Error:", e)

def main():
    """Loop utama ESP32"""
    connect_wifi()
    while True:
        try:
            pir_val, ldr_val, temp_val = read_sensors()  # Baca sensor
            send_to_ubidots(pir_val, ldr_val, temp_val)  # Kirim data
            time.sleep(5)  # Delay 5 detik
        except Exception as e:
            print("Main Error:", e)
            time.sleep(10)

if __name__ == "__main__":
    main()

