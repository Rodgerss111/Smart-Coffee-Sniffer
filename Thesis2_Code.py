import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import math
# --- User-Defined Constants and Hardware Configuration ---
# You MUST fill in these values based on your specific circuit and components.
# Information from the TGS 2602 datasheet (provided by user) is referenced below.
# The load resistor (RL) in your voltage divider circuit.
# Based on your physical measurement.
LOAD_RESISTOR_OHMS = 453.0  # Ohms (Ω) - Based on your measurement
# The gain setting for your ADS1115. This affects the full-scale voltage range.
# For example, a gain of 1 means a range of ±4.096V, gain of 2/3 is ±6.144V.
# Standard circuit voltage (Vc) is 5.0 ± 0.2V, so a gain of 2/3 is appropriate.
ADS1115_GAIN = 1  # Example: 1 for a ±4.096V range.
# The ADC channel your TGS 2602 sensor is connected to.
# For example, ADS.P0, ADS.P1, ADS.P2, or ADS.P3.
ADC_CHANNEL = ADS.P0
# Number of readings to take for the calibration average.
CALIBRATION_READING_COUNT = 100
# --- Function Definitions ---
def calculate_sensor_resistance(adc_voltage):
   """
   Calculates the sensor resistance (Rs) from the ADC voltage reading.
   This is based on the voltage divider circuit formula.
 
   Args:
       adc_voltage (float): The voltage read from the ADC.
     
   Returns:
       float: The calculated sensor resistance in Ohms (Ω).
   """
   if adc_voltage == 0:
       return float('inf')
 
   # Define the reference voltage based on the ADS1115 gain setting.
   # For example, GAIN_ONE (±4.096V) for gain=1
   if ADS1115_GAIN == 1:
       adc_reference_voltage = 4.096
   elif ADS1115_GAIN == 2/3:
       adc_reference_voltage = 6.144
   else:
       adc_reference_voltage = 4.096  # Default case


   # Rs = RL * (V_ref - V_adc) / V_adc
   rs = LOAD_RESISTOR_OHMS * (adc_reference_voltage - adc_voltage) / adc_voltage
   return rs


def calibrate_sensor(adc_object):
   """
   Performs a calibration routine to determine the sensor's baseline resistance (Ro)
   in a clean air environment.
 
   Args:
       adc_object (AnalogIn): The analog input object for the sensor.
     
   Returns:
       float: The average baseline resistance (Ro) in Ohms.
   """
   print("\n--- Calibration Process ---")
   print("Please ensure the sensor is in a clean, fresh air environment.")
   print("Calibration will begin in 5 seconds...")
   time.sleep(5)
 
   print(f"Collecting {CALIBRATION_READING_COUNT} readings...")
 
   total_resistance = 0.0
   for i in range(CALIBRATION_READING_COUNT):
       # Read the voltage from the ADC channel
       voltage = adc_object.voltage
     
       # Calculate the sensor's resistance
       resistance = calculate_sensor_resistance(voltage)
     
       total_resistance += resistance
       print(f"Reading {i+1}/{CALIBRATION_READING_COUNT} - Voltage: {voltage:.4f}V, Resistance: {resistance:.2f}Ω")
       time.sleep(0.1) # Short delay between readings
     
   avg_resistance = total_resistance / CALIBRATION_READING_COUNT
   print(f"\nCalibration complete. Baseline Resistance (Ro) = {avg_resistance:.2f}Ω")
   return avg_resistance
def estimate_ammonia_ppm(rs_ro_ratio):
   """
   Estimates the concentration of Ammonia based on the Rs/Ro ratio.
   This formula is an approximation derived from the user-provided points.
 
   Args:
       rs_ro_ratio (float): The calculated resistance ratio.
     
   Returns:
       float: The estimated Ammonia concentration in ppm.
   """
   # Formula derived from user's points (0.65, 2) and (0.45, 25)
   # Concentration = 0.1036 * (Rs/Ro)^-6.8685
   if rs_ro_ratio <= 0:
     return float('inf')
   estimated_ppm = 0.1036 * (rs_ro_ratio)**(-6.8685)
   return estimated_ppm
def estimate_hydrogen_sulfide_ppm(rs_ro_ratio):
   """
   Estimates the concentration of Hydrogen Sulfide based on the Rs/Ro ratio.
   This formula is an approximation derived from the user-provided points.
 
   Args:
       rs_ro_ratio (float): The calculated resistance ratio.
     
   Returns:
       float: The estimated Hydrogen Sulfide concentration in ppm.
   """
   # Formula derived from user's points (0.7, 0.2) and (0.3, 2)
   # Concentration = 0.0758 * (Rs/Ro)^-2.7174
   if rs_ro_ratio <= 0:
     return float('inf')
   estimated_ppm = 0.0758 * (rs_ro_ratio)**(-2.7174)
   return estimated_ppm
def main():
   """
   The main program loop for reading and analyzing sensor data.
   """
   print("Initializing ADS1115 and TGS 2602 sensor...")
 
   try:
       # Create the I2C bus object. Make sure to update 'board.SCL' and 'board.SDA' if needed.
       i2c = busio.I2C(board.SCL, board.SDA)
     
       # Create the ADS1115 object
       ads = ADS.ADS1115(i2c, gain=ADS1115_GAIN)
     
       # Create an analog input object on the specified channel
       sensor_adc = AnalogIn(ads, ADC_CHANNEL)
     
   except Exception as e:
       print(f"Failed to initialize ADS1115: {e}")
       print("Please ensure your wiring is correct and the `adafruit-circuitpython-ads1x15` library is installed.")
       return
   # Calibrate the sensor to get the baseline resistance (Ro)
   baseline_ro = calibrate_sensor(sensor_adc)
 
   print("\n--- Starting Gas Detection ---")
 
   while True:
       try:
           # Get the raw ADC value and voltage
           raw_adc_value = sensor_adc.value
           current_voltage = sensor_adc.voltage
         
           # Calculate the current sensor resistance (Rs)
           current_rs = calculate_sensor_resistance(current_voltage)
         
           # The key metric for this sensor is the Rs/Ro ratio.
           if baseline_ro <= 0:
               print("Error: Baseline resistance is zero or negative. Cannot proceed.")
               break
         
           rs_ro_ratio = current_rs / baseline_ro
         
           # Use the characteristic curve functions to estimate concentrations for both gases
           ammonia_ppm = estimate_ammonia_ppm(rs_ro_ratio)
           h2s_ppm = estimate_hydrogen_sulfide_ppm(rs_ro_ratio)
         
           print(f"--- Sensor Data ---")
           print(f"ADC Gain: {ADS1115_GAIN}")
           print(f"Raw ADC Value: {raw_adc_value}")
           print(f"Current Voltage: {current_voltage:.4f}V")
           print(f"Current Resistance (Rs): {current_rs:.2f}Ω")
           print(f"Resistance Ratio (Rs/Ro): {rs_ro_ratio:.2f}")
           print("-" * 20)
           print(f"Ammonia Concentration: {ammonia_ppm:.2f} ppm")
           print(f"Hydrogen Sulfide Concentration: {h2s_ppm:.2f} ppm")
           print("-" * 30)
         
           time.sleep(2)  # Wait for 2 seconds before the next reading
         
       except KeyboardInterrupt:
           print("\nExiting sensor monitoring.")
           break
       except Exception as e:
           print(f"An error occurred during detection: {e}")
           break
if __name__ == "__main__":
   main()



