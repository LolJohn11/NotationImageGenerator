import os
import csv
import ctypes
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from idlelib.tooltip import Hovertip

class VirtualKeyboardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Notation Image Generator")

        myappid = 'mycompany.myproduct.subproduct.version'  # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

        # Set window icon
        icon_path = os.path.join(os.getcwd(), "icon.ico")
        if os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)

        self.root.geometry("990x790")  # Window size

        self.assets_types = [
            ("T8 Default", "assets"),
            ("Xbox", "assets_xbox"),
            ("PlayStation", "assets_ps"),
        ]
        
        self.all_characters = [
            "None",
            "Alisa",
            "Asuka",
            "Azucena",
            "Bryan",
            "Claudio",
            "Devil Jin",
            "Dragunov",
            "Eddy",
            "Feng",
            "Hwoarang",
            "Jack 8",
            "Jin",
            "Jun",
            "Kazuya",
            "King",
            "Kuma",
            "Lars",
            "Law",
            "Lee",
            "Leo",
            "Leroy",
            "Lili",
            "Nina",
            "Panda",
            "Paul",
            "Raven",
            "Reina",
            "Shaheen",
            "Steve",
            "Victor",
            "Xiaoyu",
            "Yoshimitsu",
            "Zafina",
        ]
        
        # Open the MoveDict.csv and turn it into a dictionary
        movedict_csv = os.path.join(os.getcwd(), "data", "MoveDict.csv")
        with open(movedict_csv, mode='r') as file:
            csv_reader = csv.DictReader(file, delimiter=';')
         
            # Initialize an empty list to store the dictionaries
            self.MoveDict = []
            # Iterate through each row in the CSV file
            for row in csv_reader:
                # Append each row (as a dictionary) to the list
                self.MoveDict.append(row)
        
        # Open the CharMoves.csv and turn it into a dictionary
        charmoves_csv = os.path.join(os.getcwd(), "data", "CharMoves.csv")
        with open(charmoves_csv, mode='r') as file:
            csv_reader = csv.DictReader(file, delimiter=';')

            self.CharMoves = []
            for row in csv_reader:
                self.CharMoves.append(row)
          
        self.selected_images = []
        self.include_dark = tk.BooleanVar(value=False)

        # Initialize preview_frame
        self.preview_frame = tk.Frame(self.root)
        self.preview_frame.grid(row=8, column=0, columnspan=5, pady=5)
        
        # Setting variables
        self.images_folder_var = tk.StringVar(value="T8 Default")
        self.images_folder_var.trace_add("write", self.load_and_reload_assets)
        
        self.character_var = tk.StringVar(value="None")
        self.character_var.trace_add("write", self.update_character_images)

        self.character_image_buttons = []

        # Get the selected assets folder
        self.selected_assets = self.assets_types[0][1]

        self.create_widgets()

    def create_widgets(self):
        # Selected Images Display
        self.image_frame = tk.Frame(self.root)
        self.image_frame.grid(row=0, column=0, columnspan=5, pady=10)

        # Load Images from the selected folder, group them by prefix, and sort within each group
        image_files = self.load_and_group_images()

        self.image_buttons = [[] for _ in range(8)]
        self.tooltips = []

        for group in image_files:
            for filename in group:
                if "_Dark" in filename:
                    continue  # Skip buttons with "_Dark" suffix
                if "R9_" in filename:
                    continue  # Skip buttons with "R9" prefix

                # Fix the image_path for the default option
                image_path = os.path.join(self.selected_assets, filename)
                img = Image.open(image_path).resize((50, 50), Image.LANCZOS)  # Resize for display
                img_tk = ImageTk.PhotoImage(img)
                button = tk.Button(self.image_frame, image=img_tk, command=lambda i=image_path: self.toggle_image(i))
                button.image = img_tk

                # Determine the row based on the prefix
                row = min(int(filename.split('_')[0][1]), 8)  # Ensure row doesn't exceed 8
                self.image_buttons[row - 1].append(button)

                # Matching a tooltip with a button
                self.file_name = filename[6:][:-4]
                move_name = self.find_move_name(self.MoveDict, self.file_name)
                if move_name:
                    self.tooltips.append(Hovertip(button, move_name, hover_delay=300))

        # Arrange buttons in separate rows
        for i, row_buttons in enumerate(self.image_buttons):
            for j, button in enumerate(row_buttons):
                button.grid(row=i, column=j, padx=5, pady=5)
        
        # Drop-down menu for selecting assets
        assets_menu_label = tk.Label(self.root, text="Button style:")
        assets_menu_label.grid(row=i + 1, column=3, pady=10, columnspan=2)
        assets_menu = tk.OptionMenu(self.root, self.images_folder_var, *[option[0] for option in self.assets_types])
        assets_menu.grid(row=i + 1, column=4, pady=10, columnspan=2)

        # Drop-down menu for selecting a character
        character_label = tk.Label(self.root, text="Character:")
        character_label.grid(row=7, column=3, pady=10, columnspan=2)
        character_menu = tk.OptionMenu(self.root, self.character_var, *self.all_characters)
        character_menu.grid(row=7, column=4, pady=10, columnspan=2)
        
        # Image button for displaying the selected character
        self.character_image_button = tk.Button(self.root, state=tk.DISABLED, command=self.add_character_image)
        self.character_image_button.grid(row=7, column=3, pady=10, columnspan=1)
        
        # Backspace Button
        backspace_button = tk.Button(self.root, text="Backspace", command=self.remove_last_image)
        backspace_button.grid(row=i + 1, column=0, pady=5, columnspan=1)

        # Clear Button
        clear_button = tk.Button(self.root, text="Clear", command=self.clear_selected_images)
        clear_button.grid(row=i + 1, column=0, pady=5, columnspan=2)

        # Include Dark Checkbox
        include_dark_checkbox = tk.Checkbutton(self.root, text="Include dark notation", variable=self.include_dark)
        include_dark_checkbox.grid(row=i + 2, column=1, pady=10, columnspan=5)
        
        # Export Button
        export_button = tk.Button(self.root, text="Save as PNG", command=self.export_images)
        export_button.grid(row=i + 2, column=0, pady=10, columnspan=5)

        # Preview Field
        self.preview_frame = tk.Frame(self.root)
        self.preview_frame.grid(row=i + 3, column=0, columnspan=5, pady=5)

    # Function for finding the moves full names
    def find_move_name(self, *args):
        for data in self.MoveDict:
            if data['Move'] == self.file_name:
                return data['Name']
        return None  # Return None if the move is not found
    
    # Function for finding the moves for the selected Character
    def find_character_moves(self, *args):
        for data in self.CharMoves:
            if data['Character'] == self.character_var.get():
                return data['Moves']
        return None  # Return None if the character is not found
    
    def update_character_images(self, *args):
        
        # Get the selected character
        selected_character = self.character_var.get()

        #Update the image button with the selected character's image
        if selected_character == "None":
            self.character_image_button.configure(image='')
            self.character_image_button.config(state=tk.DISABLED)
        else:
            char_folder = os.path.join(os.getcwd(), "char")
            char_image_path = os.path.join(char_folder, selected_character + ".png")

            if os.path.exists(char_image_path):
                img = Image.open(char_image_path).resize((50, 50), Image.LANCZOS)  # Resize for display
                img_tk = ImageTk.PhotoImage(img)

                self.character_image_button.config(state=tk.NORMAL, image=img_tk, command=self.add_character_image)
                self.character_image_button.image = img_tk
            else:
                messagebox.showwarning("Image Not Found", f"Image not found for character: {selected_character}")
                self.character_var.set("None")
        
        # Clear existing character-specific buttons
        for button_row in self.character_image_buttons:
            for button in button_row:
                button.grid_forget()  # Hide the button

        if selected_character == "None":
            return  # No need to create character-specific buttons when "None" is selected

        # Get the moves for the selected character
        char_moves_str = self.find_character_moves(self.CharMoves, selected_character)
        char_moves = char_moves_str.split(", ")
        char_moves.sort()
        print(char_moves)
        # Initialize character-specific buttons
        self.character_image_buttons = []

        # Counter to keep track of the current column index
        column_index = 0

        # Iterate over the moves of the selected character
        for move in char_moves:
            # Create a row for each move
            button_row = []
            for filename in os.listdir(self.selected_assets):
                # Check if the filename contains the move string
                if move == filename[3:][:-4]:
                    if "_Dark" in filename:
                        continue  # Skip buttons with "_Dark" suffix

                    # Create and configure the button
                    image_path = os.path.join(self.selected_assets, filename)
                    img = Image.open(image_path).resize((50, 50), Image.LANCZOS)  # Resize for display
                    img_tk = ImageTk.PhotoImage(img)
                    button = tk.Button(self.image_frame, image=img_tk, command=lambda i=image_path: self.toggle_image(i))
                    button.image = img_tk
                    button_row.append(button)
                    
                    # Add tooltip if available
                    self.file_name = filename[3:][:-4]
                    move_name = self.find_move_name(self.MoveDict, self.file_name)
                    if move_name:
                        self.tooltips.append(Hovertip(button, move_name, hover_delay=300))

            # Add the row of buttons to the list
            self.character_image_buttons.append(button_row)

            # Place the buttons in the eighth row of the image buttons' grid
            for i, button in enumerate(button_row):
                button.grid(row=7, column=column_index, padx=5, pady=5)
                column_index += 1  # Increment column index for the next button

        # Update the preview field
        self.update_preview_field()

    def add_character_image(self):
        selected_character = self.character_var.get()

        if selected_character != "None":
            char_folder = os.path.join(os.getcwd(), "char")
            char_image_path = os.path.join(char_folder, selected_character + ".png")

            if os.path.exists(char_image_path):
                self.selected_images.append(char_image_path)
                self.update_selected_images_display()
    
    def load_and_reload_assets(self, *args):
        # Reload assets when the drop-down menu changes
        value_to_find = self.images_folder_var.get()  # Extract the string value
        index = next(i for i, option in enumerate(self.assets_types) if option[0] == value_to_find)  # Find the index
        new_asset_folder = self.assets_types[index][1]

        # Rebuilding the selected images list to make sure we are using the right assets
        temp_selected_images = []
        for item in self.selected_images:
            temp_selected_images.append(item.replace(self.selected_assets, new_asset_folder))

        self.selected_images = temp_selected_images

        # Set the asset folder to the currently selected asset option
        self.selected_assets = new_asset_folder

        # Update the widgets
        self.preview_frame.grid_forget()
        self.character_image_button.grid_forget()
        self.create_widgets()
        self.load_and_group_images()
        self.update_character_images()
        self.update_selected_images_display()
        self.update_preview_field()
    
    def load_and_group_images(self, *args):
        # Load Images from the selected folder, group them by prefix, and sort within each group
        image_files = sorted(os.listdir(self.selected_assets))
        image_files = sorted(image_files, key=lambda x: (x.split('_')[0], x))

        grouped_images = [[] for _ in range(8)]

        for filename in image_files:
            if "_Dark" in filename:
                continue  # Skip buttons with "_Dark" suffix

            image_path = os.path.join(self.selected_assets, filename)
            # Determine the row based on the prefix
            row = min(int(filename.split('_')[0][1]), 8)  # Ensure row doesn't exceed 8
            grouped_images[row - 1].append(filename)

        self.update_preview_field(grouped_images)

        return grouped_images

    def toggle_image(self, image_path):
        # Allow the same image to be added to the list more than once
        self.selected_images.append(image_path)
        self.update_selected_images_display()

    def remove_last_image(self):
        # Remove the last image from the list
        if self.selected_images:
            self.selected_images.pop()
            self.update_selected_images_display()

    def clear_selected_images(self):
        # Clear the entire list of selected images
        self.selected_images = []
        self.update_selected_images_display()
        self.update_preview_field()

    def update_selected_images_display(self):
        # Display the selected images
        for row_buttons in self.image_buttons:
            for button in row_buttons:
                button.config(state=tk.NORMAL)

        for i, image_path in enumerate(self.selected_images):
            img = Image.open(image_path).resize((50, 50), Image.LANCZOS)  # Resize for display
            img_tk = ImageTk.PhotoImage(img)

        # Update the preview field
        self.update_preview_field()

    def update_preview_field(self, grouped_images=None):
        # Destroy previous preview images
        for widget in self.preview_frame.winfo_children():
            widget.destroy()

        if grouped_images is None:
            # Load Images from the selected folder, group them by prefix, and sort within each group
            grouped_images = self.load_and_group_images()

        # Display the selected images in the preview field
        total_width = len(self.selected_images) * 50  # Original width without scaling
        max_width = 17 * 50  # Maximum width without scaling

        if total_width > max_width:
            # Scale down images dynamically
            scale_factor = max_width / total_width
            scaled_size = 50 * scale_factor

            for i, image_path in enumerate(self.selected_images):
                img = Image.open(image_path).resize((int(scaled_size), int(scaled_size)), Image.LANCZOS)
                img_tk = ImageTk.PhotoImage(img)
                label = tk.Label(self.preview_frame, image=img_tk)
                label.image = img_tk
                label.grid(row=0, column=i, padx=0)

        else:
            # Display images without scaling
            for i, image_path in enumerate(self.selected_images):
                img = Image.open(image_path).resize((50, 50), Image.LANCZOS)  # Resize for display
                img_tk = ImageTk.PhotoImage(img)
                label = tk.Label(self.preview_frame, image=img_tk)
                label.image = img_tk
                label.grid(row=0, column=i, padx=0)

    def export_images(self):
        if not self.selected_images:
            messagebox.showinfo("Error", "Cannot save an empty notation.")
            return

        # Combine selected images into a single image (in a row) with a transparent background
        total_width = len(self.selected_images) * 80  # Use original width for exported image
        total_height = 80  # Use original height for exported image
        combined_image = Image.new('RGBA', (total_width, total_height), (0, 0, 0, 0))  # Transparent background

        current_width = 0
        for image_path in self.selected_images:
            img = Image.open(image_path).resize((80, 80), Image.LANCZOS)  # Original size
            combined_image.paste(img, (current_width, 0), mask=img.convert('RGBA').split()[3])
            current_width += 80

        # Define the base file name
        base_filename = "notation.png"

        # Check if the file already exists
        if os.path.exists(base_filename):
            # If it does, find a unique file name
            suffix = 1
            while os.path.exists(f"notation_{suffix}.png"):
                suffix += 1

            # Update the base file name with the unique suffix
            base_filename = f"notation_{suffix}.png"

        # Save the combined image
        combined_image.save(base_filename)
        messagebox.showinfo("Save Successful", f"Image file(s) created successfully.")

        # Export dark image if checkbox is checked
        if self.include_dark.get():
            dark_image = Image.new('RGBA', (total_width, total_height), (0, 0, 0, 0))  # Transparent background
            current_width = 0

            for image_path in self.selected_images:
                dark_path = image_path.replace(".png", "_Dark.png")
                dark_img = Image.open(dark_path).resize((80, 80), Image.LANCZOS)  # Original size
                dark_image.paste(dark_img, (current_width, 0), mask=dark_img.convert('RGBA').split()[3])
                current_width += 80

            # Define the base file name for dark image
            dark_base_filename = base_filename.replace(".png", "_dark.png")

            # Check if the dark image file already exists
            if os.path.exists(dark_base_filename):
                # If it does, find a unique file name
                suffix = 1
                while os.path.exists(f"notation_{suffix}_dark.png"):
                    suffix += 1

                # Update the base file name with the unique suffix
                dark_base_filename = f"notation_{suffix}_dark.png"

            # Save the dark image
            dark_image.save(dark_base_filename)
            # messagebox.showinfo("Save Successful", f"Dark image file '{dark_base_filename}' created successfully.")

if __name__ == "__main__":
    root = tk.Tk()
    app = VirtualKeyboardApp(root)
    root.mainloop()
