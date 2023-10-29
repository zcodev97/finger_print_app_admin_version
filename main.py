import time
import serial
from tkinter import ttk
# from fingerprint_project.fingerprint_files.Adafruit_CircuitPython_Fingerprint import adafruit_fingerprint
import tkinter as tk
from tkinter import messagebox
import tkinter.simpledialog
import psycopg2
from PIL import Image, ImageTk
from tkinter import filedialog
import os
import shutil
import uuid
from datetime import datetime, timezone
import adafruit_fingerprint
uart = serial.Serial("COM8", baudrate=57600, timeout=1)

finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

##################################################


def db_connection_delete_fingerprint(finger_print_id_to_delete):
    try:
        # Database connection parameters
        dbname = 'test'
        user = 'test'
        password = 'test'
        host = 'localhost'
        port = '5432'  # Typically 5432 for PostgreSQL
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        # SQL DELETE query
        delete_query = f"""
        DELETE FROM fingerprintapp_employee
        WHERE finger_print_id = '{finger_print_id_to_delete}';
        """
        cursor = conn.cursor()
        cursor.execute(delete_query)
        conn.commit()

        print('deleted')
        return True
    except Exception as error:
        print(error)
        return False
    finally:
        cursor.close()
        conn.close()


def db_connection_add_new_fingerprint(new_uuid, finger_print_id, fullname, description, image_name_with_extension):

    try:

        # Database connection parameters
        dbname = 'test'
        user = 'test'
        password = 'test'
        host = 'localhost'
        port = '5432'  # Typically 5432 for PostgreSQL
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )

        finger_print_id = finger_print_id
        fullname = fullname
        description = description
        shift = 2
        image = 'images/' + image_name_with_extension
        created_by_id = 1
        created_at = datetime.now(timezone.utc)

        # SQL INSERT query
        insert_query = """
        INSERT INTO fingerprintapp_employee (id, finger_print_id, fullname,
        description, shift, image, created_by_id, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """
        # Create a cursor object to interact with the database

        cur = conn.cursor()

        # Execute the INSERT query
        cur.execute(insert_query, (str(new_uuid), finger_print_id,
                                   fullname, description,
                                   shift, image, created_by_id, created_at))

        conn.commit()

        print(f'inserted new fingerprint for user {fullname}')
        return True
    except Exception as error:
        print(error)
        return False
    finally:
        cur.close()
        conn.close()


def get_fingerprint():
    """Get a finger-print image, template it, and see if it matches!"""
    print("Waiting for image...")
    while finger.get_image() != adafruit_fingerprint.OK:
        pass
    print("Templating...")
    if finger.image_2_tz(1) != adafruit_fingerprint.OK:
        return False
    print("Searching...")
    if finger.finger_search() != adafruit_fingerprint.OK:
        return False
    return True


# pylint: disable=too-many-branches
def get_fingerprint_detail():
    """Get a finger print image, template it, and see if it matches!
    This time, print out each error instead of just returning on failure"""
    print("Getting image...", end="")
    i = finger.get_image()
    if i == adafruit_fingerprint.OK:
        print("Image taken")
    else:
        if i == adafruit_fingerprint.NOFINGER:
            print("No finger detected")
        elif i == adafruit_fingerprint.IMAGEFAIL:
            print("Imaging error")
        else:
            print("Other error")
        return False

    print("Templating...", end="")
    i = finger.image_2_tz(1)
    if i == adafruit_fingerprint.OK:
        print("Templated")
    else:
        if i == adafruit_fingerprint.IMAGEMESS:
            print("Image too messy")
        elif i == adafruit_fingerprint.FEATUREFAIL:
            print("Could not identify features")
        elif i == adafruit_fingerprint.INVALIDIMAGE:
            print("Image invalid")
        else:
            print("Other error")
        return False

    print("Searching...", end="")
    i = finger.finger_fast_search()
    # pylint: disable=no-else-return
    # This block needs to be refactored when it can be tested.
    if i == adafruit_fingerprint.OK:
        print("Found fingerprint!")
        return True
    else:
        if i == adafruit_fingerprint.NOTFOUND:
            print("No match found")
        else:
            print("Other error")
        return False


# pylint: disable=too-many-statements
def enroll_finger(location):

    if get_fingerprint():
        print('error finger print founded !!')
        return

    """Take a 2 finger images and template it, then store in 'location'"""
    for fingerimg in range(1, 3):
        if fingerimg == 1:
            print("Place finger on sensor...", end="")
        else:
            print("Place same finger again...", end="")

        while True:
            i = finger.get_image()
            if i == adafruit_fingerprint.OK:
                print("Image taken")
                break
            if i == adafruit_fingerprint.NOFINGER:
                print(".", end="")
            elif i == adafruit_fingerprint.IMAGEFAIL:
                print("Imaging error")
                return False
            else:
                print("Other error")
                return False

        print("Templating...", end="")
        i = finger.image_2_tz(fingerimg)
        if i == adafruit_fingerprint.OK:
            print(i)
            print("Templated")
        else:
            if i == adafruit_fingerprint.IMAGEMESS:
                print("Image too messy")
            elif i == adafruit_fingerprint.FEATUREFAIL:
                print("Could not identify features")
            elif i == adafruit_fingerprint.INVALIDIMAGE:
                print("Image invalid")
            else:
                print("Other error")
            return False

        if fingerimg == 1:
            print("Remove finger")
            time.sleep(1)
            while i != adafruit_fingerprint.NOFINGER:
                i = finger.get_image()

    print("Creating model...", end="")
    i = finger.create_model()
    if i == adafruit_fingerprint.OK:
        print("Created")
    else:
        if i == adafruit_fingerprint.ENROLLMISMATCH:
            print("Prints did not match")
        else:
            print("Other error")
        return False

    print("Storing model #%d..." % location, end="")
    i = finger.store_model(location)
    if i == adafruit_fingerprint.OK:
        print("Stored")
    else:
        if i == adafruit_fingerprint.BADLOCATION:
            print("Bad storage location")
        elif i == adafruit_fingerprint.FLASHERR:
            print("Flash storage error")
        else:
            print("Other error")
        return False

    return True


##################################################


def get_num(max_number):
    """Use input() to get a valid number from 0 to the maximum size
    of the library. Retry till success!"""
    i = -1
    while (i > max_number - 1) or (i < 0):
        try:
            i = int(input("Enter ID # from 0-{}: ".format(max_number - 1)))
        except ValueError:
            pass
    return i


class FingerprintApp(tk.Tk):

    def __init__(self):
        super().__init__()
        # Font styles

        self.image_name_with_extension = ''
        self.screen_width = self.winfo_screenwidth()
        self.screen_height = self.winfo_screenheight()
        self.geometry(f"{self.screen_width}x{self.screen_height}")

        # Fonts
        self.label_font = ("Arial", 22)
        self.entry_font = ("Arial", 20)

        # Employee Name
        self.emp_full_name_label = tk.Label(self, text="Employee Full Name",
                                            font=self.label_font, bg='#f4f4f4')
        self.emp_full_name_label.grid(
            row=0, column=0, pady=10, padx=10, sticky="w")

        self.emp_full_name = ttk.Entry(self, font=self.entry_font, width=40)
        self.emp_full_name.grid(row=1, column=0, pady=5, padx=10)

        # Employee Description
        self.emp_description_label = tk.Label(self, text="Employee Description",
                                              font=self.label_font, bg='#f4f4f4')
        self.emp_description_label.grid(
            row=2, column=0, pady=10, padx=10, sticky="w")

        self.emp_description = ttk.Entry(self, font=self.entry_font, width=40)
        self.emp_description.grid(row=3, column=0, pady=5, padx=10)

        # Buttons on the right side
        self.copy_button = tk.Button(self, text="Load Employee Image", command=self.copy_images,
                                     font=("Arial", 20, 'bold'))
        self.copy_button.grid(row=0, column=1, pady=20, padx=10)

        self.label = tk.Label(self, text="Choose an option:",
                              font=("Arial", 20, 'bold'))
        self.label.grid(row=1, column=1, pady=20, padx=10)

        self.enroll_button = tk.Button(self, text="Enroll FingerPrint", bg="#33cc33", fg='white',
                                       command=self.enroll, font=("Arial", 20, 'bold'))
        self.enroll_button.grid(row=2, column=1, pady=10, padx=10)

        self.find_button = tk.Button(self, text="Find FingerPrint", fg='white', bg='blue',
                                     command=self.find, font=("Arial", 20, 'bold'))
        self.find_button.grid(row=3, column=1, pady=10, padx=10)

        self.delete_button = tk.Button(self, text="Delete FingerPrint", bg='red', fg='white',
                                       command=self.delete, font=("Arial", 20, 'bold'))
        self.delete_button.grid(row=4, column=1, pady=10, padx=10)

        self.exit_btn = tk.Button(self, text="Exit", command=self.exit,
                                  bg='black', fg='white', font=("Arial", 20, 'bold'))
        self.exit_btn.grid(row=5, column=1, pady=10, padx=10)

    def copy_images(self):
        if (len(self.emp_full_name.get()) == 0):
            messagebox.showinfo("Alert", "Enter Full Name!")
            return
        if (len(self.emp_description.get()) == 0):
            messagebox.showinfo("Alert", "Enter Description!")
            return
        # Ask the user to select image files
        file_paths = filedialog.askopenfilenames(title="Select Image Files", filetypes=[
                                                 ("Image Files", "*.png *.jpg *.jpeg *.gif *.bmp")])

        if not file_paths:
            return  # User canceled file selection

        # Destination folder
        destination_folder = "/home/abdulaziz/Desktop/finger_print_system/fingerprint_project/media/images"

        # Copy selected images to the destination folder
        for file_path in file_paths:
            new_uuid = uuid.uuid4()
            file_name = os.path.basename(file_path)
            file_extension = os.path.splitext(file_name)[1]
            file_name_without_extension = os.path.splitext(file_name)[0]
            # print("File Name with Extension:", file_name)
            # print("File Extension:", file_extension)
            # print("File Name without Extension:", file_name_without_extension)

            destination_path = os.path.join(destination_folder, str(new_uuid) + '_' +
                                            self.emp_full_name.get() + '_' +
                                            self.emp_description.get() + file_extension)
            shutil.copy(file_path, destination_path)

            self.image_name_with_extension = str(
                new_uuid) + '_' + self.emp_full_name.get() + '_' + self.emp_description.get() + file_extension

        messagebox.showinfo("Alert", "Images copied successfully!")

    def exit(self):
        self.destroy()

    def enroll(self):
        new_uuid = uuid.uuid4()
        if (len(self.emp_full_name.get()) == 0):
            messagebox.showinfo("Alert", "Enter Full Name!")
            return
        if (len(self.emp_description.get()) == 0):
            messagebox.showinfo("Alert", "Enter Description!")
            return
        location = get_num()
        if location == None:
            messagebox.showerror("Error", "Failed to enroll fingerprint.")
        else:
            if enroll_finger(location):
                db_connection_add_new_fingerprint(new_uuid, location, self.emp_full_name.get(),
                                                  self.emp_description.get(),
                                                  self.image_name_with_extension)
                self.image_name_with_extension = ''
                messagebox.showinfo(
                    "Success", "Fingerprint enrolled successfully!")
            else:
                messagebox.showerror("Error", "Failed to enroll fingerprint.")

    def find(self):
        if get_fingerprint():
            messagebox.showinfo(
                "Detected", f"Detected #{finger.finger_id} with confidence {finger.confidence}")
        else:
            messagebox.showerror("Error", "Finger not found.")

    def delete(self):
        location = get_num()
        if finger.delete_model(location) == adafruit_fingerprint.OK:
            db_connection_delete_fingerprint(location)
            messagebox.showinfo("Success", "Fingerprint deleted successfully!")
        else:
            messagebox.showerror("Error", "Failed to delete fingerprint.")

# Function to get number for enroll or delete (simplified for GUI use)


def get_num():
    try:
        number = tk.simpledialog.askinteger("Input", "Enter ID # from 1-999:")
        return number
    except:
        return -1


if __name__ == "__main__":
    app = FingerprintApp()
    app.mainloop()
