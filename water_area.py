import numpy as np
from osgeo import gdal
import os
import matplotlib.pyplot as plt
import re
import matplotlib.patches as mpatches
from matplotlib.colors import ListedColormap
import sys

def extract_year_from_filename(filename):
    """
    Extracts a 4-digit year (like 1999 or 2023) from a filename string.
    
    Args:
        filename (str): The input filename.
        
    Returns:
        int: The extracted year, or None if no year is found.
    """
    # This regular expression looks for the first occurrence of '19xx' or '20xx'
    match = re.search(r'(19|20)\d{2}', filename)
    if match:
        return int(match.group(0))
    else:
        print(f"  - Warning: Could not find a year in filename: {filename}")
        return None

def calculate_water_area(filepath, green_band_num, nir_band_num, threshold, pixel_area):
    """
    Calculates the total area of water in a TIF file.
    This version takes a known pixel area as input.
    """
    dataset = gdal.Open(filepath)
    if dataset is None:
        return None

    try:
        green_array = dataset.GetRasterBand(green_band_num).ReadAsArray().astype(np.float32)
        nir_array = dataset.GetRasterBand(nir_band_num).ReadAsArray().astype(np.float32)

        np.seterr(divide='ignore', invalid='ignore')
        numerator = green_array - nir_array
        denominator = green_array + nir_array
        ndwi = np.divide(numerator, denominator, where=(denominator != 0))
        ndwi[np.isnan(ndwi)] = 0

        water_mask = ndwi > threshold
        water_pixel_count = np.sum(water_mask)
        
        total_water_area = water_pixel_count * pixel_area
        return total_water_area
    except Exception as e:
        print(f"  - Error processing file {os.path.basename(filepath)}: {e}")
        return None
    finally:
        dataset = None

def plot_area_over_time(time_series_data):
    """
    Creates and displays a line plot of water area over time.
    
    Args:
        time_series_data (list): A list of tuples, where each tuple is (year, area_in_sq_meters).
    """
    if not time_series_data:
        print("No data to plot.")
        return

    # Sort the data by year to ensure the line plot is correct
    time_series_data.sort()
    
    # Unpack the sorted data into separate lists for plotting
    years, areas_sq_meters = zip(*time_series_data)
    
    # Convert area to square kilometers for better readability on the plot
    areas_sq_km = [area / 1_000_000 for area in areas_sq_meters]
    
    # --- Create the Plot ---
    plt.figure(figsize=(12, 7))
    plt.plot(years, areas_sq_km, marker='o', linestyle='-', color='dodgerblue', label='Water Area')
    
    # Add titles and labels
    plt.title('Water Surface Area Over Time', fontsize=16)
    plt.xlabel('Year', fontsize=12)
    plt.ylabel('Area (Square Kilometers)', fontsize=12)
    
    # Customize the plot for clarity
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.xticks(years, rotation=45) # Ensure every year is a tick on the x-axis
    plt.tight_layout() # Adjust plot to prevent labels from overlapping
    
    # Add a legend
    plt.legend()
    
    # Display the plot
    plt.show()

if __name__ == '__main__':
    # --- Configuration ---
    #image_folder = "SatImage"  # The folder where your TIF files are located
    #image_folder = "E:\\teams\\Kantubek"
    if len(sys.argv) != 2:
        # If the number of arguments is wrong, print a helpful message and exit.
        print("\n--- ERROR: Missing folder path ---")
        print("Please provide the path to the image folder as a command-line argument.")
        print(f"Usage: python {sys.argv[0]} <path_to_your_folder>")
        print(r"Example: python water_area.py E:\Kantubek")
        sys.exit(1)  # Exit the script with an error code
    # --- Parameters for your specific data ---
    # Band numbers for Green and NIR
    image_folder = sys.argv[1]
    GREEN_BAND_IN_FILE = 2
    NIR_BAND_IN_FILE = 4
    
    # NDWI threshold for identifying water
    NDWI_THRESHOLD = 0.2
    
    PIXEL_AREA_SQ_METERS = 900.0
    
    # --- Main Execution ---
    # List to store our results as (year, area) tuples
    time_series_results = []
    
    print(f"Scanning for .tif files in folder: '{image_folder}'...")
    
    # Check if the folder exists
    if not os.path.isdir(image_folder):
        print(f"Error: Folder '{image_folder}' not found. Please create it and add your images.")
        sys.exit(1)
    else:
        # Loop through every file in the specified folder
        for filename in sorted(os.listdir(image_folder)):
            if filename.lower().endswith(('.tif', '.tiff')):
                print(f"\nProcessing file: {filename}...")
                
                # Construct the full path to the image
                full_path = os.path.join(image_folder, filename)
                
                # Extract the year from the filename
                year = extract_year_from_filename(filename)
                
                if year:
                    # Calculate the water area for the current image
                    area = calculate_water_area(
                        filepath=full_path,
                        green_band_num=GREEN_BAND_IN_FILE,
                        nir_band_num=NIR_BAND_IN_FILE,
                        threshold=NDWI_THRESHOLD,
                        pixel_area=PIXEL_AREA_SQ_METERS
                    )
                    
                    if area is not None:
                        print(f"  - Found Year: {year}, Calculated Water Area: {area / 1_000_000:,.2f} sq km")
                        # Add the result to our list
                        time_series_results.append((year, area))

        # --- After processing all files, generate the plot ---
        print("\n--- All files processed. Generating plot... ---")

        plot_area_over_time(time_series_results)
