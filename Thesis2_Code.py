import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import math

# --- User-Defined Constants and Hardware Configuration ---
# You MUST fill in these values based on your specific circuit and components.
# Information from the TGS 2602 datasheet (provided by user) is referenced below.

# --- TGS 2602 Sensor Configuration ---
# The load resistor (RL) in your voltage divider circuit.
LOAD_RESISTOR_OHMS_TGS = 453.0  # Ohms (Ω) - Based on your measurement
# The ADC channel your TGS 2602 sensor is connected to.
ADC_CHANNEL_TGS = ADS.P0

# --- MiCS-5524 Sensor Configuration ---
# The Adafruit MiCS-5524 breakout board uses a fixed 10 kΩ load resistor.
LOAD_RESISTOR_OHMS_MICS = 10000.0 # Ohms (Ω)
# The ADC channel your MiCS-5524 sensor is connected to.
ADC_CHANNEL_MICS = ADS.P1

# --- ADS1115 ADC Configuration ---
# The gain setting for your ADS1115. This affects the full-scale voltage range.
# For example, a gain of 1 means a range of ±4.096V, gain of 2/3 is ±6.144V.
ADS1115_GAIN = 1

# Number of readings to take for the calibration average.
CALIBRATION_READING_COUNT = 100

# --- Function Definitions ---

def calculate_sensor_resistance(adc_voltage, load_resistor_ohms):
    """
    Calculates the sensor resistance (Rs) from the ADC voltage reading.
    This is based on the voltage divider circuit formula.
    
    Args:
        adc_voltage (float): The voltage read from the ADC.
        load_resistor_ohms (float): The resistance of the load resistor in Ohms.
        
    Returns:
        float: The calculated sensor resistance in Ohms (Ω).
    """
    if adc_voltage == 0:
        return float('inf')
    
    # Define the reference voltage based on the ADS1115 gain setting.
    if ADS1115_GAIN == 1:
        adc_reference_voltage = 4.096
    elif ADS1115_GAIN == 2/3:
        adc_reference_voltage = 6.144
    else:
        adc_reference_voltage = 4.096
    
    # Rs = RL * (V_ref - V_adc) / V_adc
    rs = load_resistor_ohms * (adc_reference_voltage - adc_voltage) / adc_voltage
    return rs

def calibrate_sensor(adc_object, sensor_name):
    """
    Performs a calibration routine to determine the sensor's baseline resistance (Ro)
    in a clean air environment.
    
    Args:
        adc_object (AnalogIn): The analog input object for the sensor.
        sensor_name (str): The name of the sensor being calibrated.
        
    Returns:
        float: The average baseline resistance (Ro) in Ohms.
    """
    print(f"\n--- Calibration Process: {sensor_name} ---")
    print("Please ensure the sensor is in a clean, fresh air environment.")
    print("Calibration will begin in 5 seconds...")
    time.sleep(5)
    
    print(f"Collecting {CALIBRATION_READING_COUNT} readings...")
    
    total_resistance = 0.0
    for i in range(CALIBRATION_READING_COUNT):
        voltage = adc_object.voltage
        resistance = calculate_sensor_resistance(voltage, LOAD_RESISTOR_OHMS_TGS if sensor_name == 'TGS 2602' else LOAD_RESISTOR_OHMS_MICS)
        total_resistance += resistance
        print(f"Reading {i+1}/{CALIBRATION_READING_COUNT} - Voltage: {voltage:.4f}V, Resistance: {resistance:.2f}Ω")
        time.sleep(0.1)
        
    avg_resistance = total_resistance / CALIBRATION_READING_COUNT
    print(f"\nCalibration complete for {sensor_name}. Baseline Resistance (Ro) = {avg_resistance:.2f}Ω")
    return avg_resistance

# --- TGS 2602 Estimation Functions ---

def estimate_ammonia_ppm_tgs(rs_ro_ratio):
    """
    Estimates the concentration of Ammonia based on the TGS 2602's Rs/Ro ratio.
    """
    if rs_ro_ratio <= 0:
      return float('inf')
    estimated_ppm = 0.1036 * (rs_ro_ratio)**(-6.8685)
    return estimated_ppm

def estimate_hydrogen_sulfide_ppm_tgs(rs_ro_ratio):
    """
    Estimates the concentration of Hydrogen Sulfide based on the TGS 2602's Rs/Ro ratio.
    """
    if rs_ro_ratio <= 0:
      return float('inf')
    estimated_ppm = 0.0758 * (rs_ro_ratio)**(-2.7174)
    return estimated_ppm

# --- MiCS-5524 Estimation Functions ---

def estimate_co_ppm(rs_ro_ratio):
    """
    Estimates CO concentration from the MiCS-5524 based on user-provided points.
    """
    if rs_ro_ratio <= 0:
      return float('inf')
    estimated_ppm = 0.176 * (rs_ro_ratio)**(-1.05)
    # Check if the estimated value is within the typical detection range (1-1000ppm)
    if 1 <= estimated_ppm <= 1000:
        return estimated_ppm
    return "Out of Range"

def estimate_ethanol_ppm(rs_ro_ratio):
    """
    Estimates Ethanol concentration from the MiCS-5524 based on user-provided points.
    """
    if rs_ro_ratio <= 0:
      return float('inf')
    estimated_ppm = 1.15 * (rs_ro_ratio)**(-2.05)
    # Check if the estimated value is within the typical detection range (10-500ppm)
    if 10 <= estimated_ppm <= 500:
        return estimated_ppm
    return "Out of Range"
    
def estimate_hydrogen_ppm(rs_ro_ratio):
    """
    Estimates Hydrogen concentration from the MiCS-5524 based on user-provided points.
    """
    if rs_ro_ratio <= 0:
      return float('inf')
    estimated_ppm = 1.6 * (rs_ro_ratio)**(-1.7)
    # Check if the estimated value is within the typical detection range (1-1000ppm)
    if 1 <= estimated_ppm <= 1000:
        return estimated_ppm
    return "Out of Range"

def estimate_ammonia_ppm_mics(rs_ro_ratio):
    """
    Estimates Ammonia concentration from the MiCS-5524 based on user-provided points.
    """
    if rs_ro_ratio <= 0:
      return float('inf')
    estimated_ppm = 1290 * (rs_ro_ratio)**(6.72)
    # Check if the estimated value is within the typical detection range (1-500ppm)
    if 1 <= estimated_ppm <= 500:
        return estimated_ppm
    return "Out of Range"
    
def estimate_methane_ppm(rs_ro_ratio):
    """
    Estimates Methane concentration from the MiCS-5524 based on user-provided points.
    """
    if rs_ro_ratio <= 0:
      return float('inf')
    estimated_ppm = 1.25e16 * (rs_ro_ratio)**(-28)
    # Check if the estimated value is within the typical detection range (>1000ppm)
    if estimated_ppm > 1000:
        return estimated_ppm
    return "Out of Range"

def main():
    """
    The main program loop for reading and analyzing sensor data.
    """
    print("Initializing ADS1115 and gas sensors...")
    
    try:
        # Create the I2C bus object
        i2c = busio.I2C(board.SCL, board.SDA)
        
        # Create the ADS1115 object
        ads = ADS.ADS1115(i2c, gain=ADS1115_GAIN)
        
        # Create analog input objects for both sensors
        tgs_sensor_adc = AnalogIn(ads, ADC_CHANNEL_TGS)
        mics_sensor_adc = AnalogIn(ads, ADC_CHANNEL_MICS)
        
    except Exception as e:
        print(f"Failed to initialize ADS1115: {e}")
        print("Please ensure your wiring is correct and the `adafruit-circuitpython-ads1x15` library is installed.")
        return

    # Calibrate both sensors
    baseline_ro_tgs = calibrate_sensor(tgs_sensor_adc, "TGS 2602")
    baseline_ro_mics = calibrate_sensor(mics_sensor_adc, "MiCS-5524")
    
    print("\n--- Starting Gas Detection ---")
    
    while True:
        try:
            # Read and process TGS 2602 data
            raw_adc_value_tgs = tgs_sensor_adc.value
            current_voltage_tgs = tgs_sensor_adc.voltage
            current_rs_tgs = calculate_sensor_resistance(current_voltage_tgs, LOAD_RESISTOR_OHMS_TGS)
            rs_ro_ratio_tgs = current_rs_tgs / baseline_ro_tgs if baseline_ro_tgs > 0 else float('inf')
            
            ammonia_ppm_tgs = estimate_ammonia_ppm_tgs(rs_ro_ratio_tgs)
            h2s_ppm_tgs = estimate_hydrogen_sulfide_ppm_tgs(rs_ro_ratio_tgs)
            
            # Read and process MiCS-5524 data
            raw_adc_value_mics = mics_sensor_adc.value
            current_voltage_mics = mics_sensor_adc.voltage
            current_rs_mics = calculate_sensor_resistance(current_voltage_mics, LOAD_RESISTOR_OHMS_MICS)
            rs_ro_ratio_mics = current_rs_mics / baseline_ro_mics if baseline_ro_mics > 0 else float('inf')
            
            co_ppm = estimate_co_ppm(rs_ro_ratio_mics)
            ethanol_ppm = estimate_ethanol_ppm(rs_ro_ratio_mics)
            hydrogen_ppm = estimate_hydrogen_ppm(rs_ro_ratio_mics)
            ammonia_ppm_mics = estimate_ammonia_ppm_mics(rs_ro_ratio_mics)
            methane_ppm = estimate_methane_ppm(rs_ro_ratio_mics)
            
            # Print combined output
            print(f"--- Sensor Data (ADC Gain: {ADS1115_GAIN}) ---")
            print(f"\n--- TGS 2602 ---")
            print(f"Raw ADC Value: {raw_adc_value_tgs}")
            print(f"Current Voltage: {current_voltage_tgs:.4f}V")
            print(f"Resistance Ratio (Rs/Ro): {rs_ro_ratio_tgs:.2f}")
            print(f"Ammonia Concentration: {ammonia_ppm_tgs:.2f} ppm")
            print(f"Hydrogen Sulfide Concentration: {h2s_ppm_tgs:.2f} ppm")
            
            print(f"\n--- MiCS-5524 ---")
            print(f"Raw ADC Value: {raw_adc_value_mics}")
            print(f"Current Voltage: {current_voltage_mics:.4f}V")
            print(f"Resistance Ratio (Rs/Ro): {rs_ro_ratio_mics:.2f}")
            print(f"CO Concentration: {co_ppm} ppm")
            print(f"Ethanol Concentration: {ethanol_ppm} ppm")
            print(f"Hydrogen Concentration: {hydrogen_ppm} ppm")
            print(f"Ammonia Concentration: {ammonia_ppm_mics} ppm")
            print(f"Methane Concentration: {methane_ppm} ppm")
            
            print("-" * 30)
            time.sleep(2)
            
        except KeyboardInterrupt:
            print("\nExiting sensor monitoring.")
            break
        except Exception as e:
            print(f"An error occurred during detection: {e}")
            break

if __name__ == "__main__":
    main()
