import struct
import base64
import sys
import os
import shutil
from PIL import Image
from io import BytesIO

class GXWriter:
    def __init__(self, gcode_path):
        self.gcode_path = gcode_path
        self.bmp = None
        self.gcode = None
        self.print_time = 0
        self.filament_usage = 0
        self.filament_usage_left = 0  # Enable dual extruder support
        self.layer_height = 0
        self.print_speed = 60
        self.bed_temp = 0
        self.print_temp = 0
        self.print_temp_left = 0
        self.multi_extruder_type = 1  # Set for dual extruder
        
        self.load_gcode()
        self.extract_metadata()
        self.bmp = self.extract_and_convert_thumbnail() or self.generate_blank_bmp()
    
    def load_gcode(self):
        """Load G-code from the provided file."""
        try:
            with open(self.gcode_path, "r", encoding="utf-8", errors="ignore") as file:
                self.gcode = file.readlines()
            
            # Ensure extruders T0 and T1 are set correctly
            for i, line in enumerate(self.gcode):
                if line.strip() == "; Executable_black_start":
                    self.gcode.insert(i + 1, "T0 ; Set first extruder\n")
                    self.gcode.insert(i + 2, "T1 ; Set second extruder\n")
                    break
        except Exception as e:
            print(f"Error loading G-code: {e}")
            self.gcode = []
    
    def extract_metadata(self):
        """Extract metadata like print time, filament usage, and temperatures from G-code."""
        for line in self.gcode:
            if line.startswith('; estimated printing time (normal mode) ='):
                time_parts = line.split('=')[1].strip().split()
                h, m, s = 0, 0, 0
                for part in time_parts:
                    if "h" in part:
                        h = int(part.replace("h", ""))
                    elif "m" in part:
                        m = int(part.replace("m", ""))
                    elif "s" in part:
                        s = int(part.replace("s", ""))
                self.print_time = h * 3600 + m * 60 + s
            elif line.startswith('; filament used [mm] ='):
                values = line.split('=')[1].strip().split(',')
                if len(values) > 1:
                    self.filament_usage = int(float(values[0].strip()))
                    self.filament_usage_left = int(float(values[1].strip()))  # Enable second extruder
                else:
                    self.filament_usage = int(float(values[0].strip()))
            elif line.startswith('; layer_height ='):
                self.layer_height = int(float(line.split('=')[1].strip()) * 1000)
            elif line.startswith('; machine_max_speed_x ='):
                self.print_speed = int(line.split('=')[1].strip())
            elif line.startswith('; first_layer_bed_temperature ='):
                self.bed_temp = int(line.split('=')[1].strip())
            elif line.startswith('; nozzle_temperature ='):
                temps = line.split('=')[1].strip().split(',')
                self.print_temp = int(temps[0])
                if len(temps) > 1:
                    self.print_temp_left = int(temps[1])
    
    def extract_and_convert_thumbnail(self):
        """Extract PNG thumbnail from G-code and convert it to BMP format."""
        base64_png = ""
        inside_thumbnail_block = False
        for line in self.gcode:
            if "thumbnail begin" in line:
                inside_thumbnail_block = True
            elif "thumbnail end" in line:
                inside_thumbnail_block = False
                break
            elif inside_thumbnail_block:
                base64_png += line.strip().lstrip('; ')
        
        if base64_png:
            try:
                png_data = base64.b64decode(base64_png)
                png_image = Image.open(BytesIO(png_data)).convert("RGB").resize((80, 60))
                bmp_io = BytesIO()
                png_image.save(bmp_io, format="BMP")
                return bmp_io.getvalue()
            except Exception as e:
                print(f"Error extracting or converting thumbnail: {e}")
        return None

    def generate_blank_bmp(self):
        """Generate a blank BMP image in case no thumbnail is found."""
        img = Image.new("RGB", (80, 60), color=(255, 255, 255))
        bmp_io = BytesIO()
        img.save(bmp_io, format="BMP")
        return bmp_io.getvalue()
    
    def encode_gx(self):
        """Generate the binary GX file format."""
        if self.gcode is None or self.bmp is None:
            print("Error: Missing G-code or BMP thumbnail.")
            return None
        
        gcode_bytes = "".join(self.gcode).encode('latin-1')
        buff = b"xgcode 1.0\n\0"
        buff += struct.pack("<4i", 0, 58, 14512, 14512)
        buff += struct.pack("<iiih", max(self.print_time, 1), self.filament_usage, self.filament_usage_left, self.multi_extruder_type)
        buff += struct.pack("<8h", self.layer_height, 0, 2, self.print_speed, self.bed_temp, self.print_temp, self.print_temp_left, 1)
        buff += self.bmp
        buff += gcode_bytes
        return buff
    
    def save_gx(self):
        """Replace the original G-code file with the GX format."""
        gx_data = self.encode_gx()
        if gx_data:
            temp_path = self.gcode_path + ".tmp"
            with open(temp_path, "wb") as f:
                f.write(gx_data)
            shutil.move(temp_path, self.gcode_path)
            print(f"G-code successfully converted to GX format: {self.gcode_path}")
        else:
            print("Failed to generate GX file.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python GXWriter.py input.gcode")
        sys.exit(1)
    
    input_gcode = sys.argv[1]
    
    writer = GXWriter(input_gcode)
    writer.save_gx()
