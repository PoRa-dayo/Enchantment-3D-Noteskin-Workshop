import tkinter as tk
from tkinter import ttk,messagebox,filedialog
from PIL import Image, ImageTk, ImageSequence
import os, re, shutil, queue, threading, json, copy, sys, tempfile, random
from pathlib import Path
from itertools import combinations

# Each list represents a folder structure to look for
# e.g. ["NoteSkins", "dance"] is NoteSkins/dance
TARGET_PATHS = [
    ["NoteSkins", "dance"]
]
FOLDER_OPTIONS = {
    "Stepmania 5/ITGmania/Etterna/OutFox": ["Stepmania 5", "ITGmania", "Etterna", "OutFox"],
    "NotITG/OpenITG": ["NotITG", "OpenITG"]
}

# Root path is the path containing Customizations, Previews, etc.
# This path is the path containing this .py
if getattr(sys, "frozen", False):
    # Running as a packaged executable
    root_path = Path(sys.executable).resolve().parent.parent
    this_path = Path(sys.executable).resolve().parent
else:
    # Running as a Python script inside Program/
    root_path = Path(__file__).resolve().parent.parent
    this_path = Path(__file__).resolve().parent

# Make sure the working directory is the root path
os.chdir(root_path)
SAVED_SELECTIONS_FILE = this_path / "saved_selections.json"
customization_dropdowns_created = False
cur_path = ""

def show_page(page):
    page1.pack_forget()
    page2.pack_forget()
    page3.pack_forget()
    page.pack(fill="both", expand=True)


# ---------------------PAGE 1: SELECT YOUR PATH-------------------------------
# Check the input folder and its parents and subfolders for paths that match TARGET_PATHS
# Then return the matching folder, and the parent folder which contains the Songs folder
def find_folder(path, max_folders=10000):
    path = os.path.abspath(os.path.expanduser(path))

    if not os.path.isdir(path):
        return None

    checked = 0

    # Search the input directory and its parents
    search_roots = []
    current = path

    while True:
        search_roots.append(current)
        parent = os.path.dirname(current)

        if parent == current:
            break

        current = parent

    # Search subfolders of each root
    for root in search_roots:
        for current_dir, dirs, files in os.walk(root):
            checked += 1

            if checked > max_folders:
                print("Search limit reached.")
                return None
            
            for target_path in TARGET_PATHS:
                current = current_dir
                matched = True

                # Follow the required nested folder structure
                for folder in target_path:
                    folder_match = None

                    for d in dirs:
                        if d.lower() == folder.lower():
                            folder_match = d
                            break

                    if folder_match is None:
                        matched = False
                        break

                    current = os.path.join(current, folder_match)

                    dirs = os.listdir(current)

                if matched:
                    matching_folder = current

                    # Find the parent directory containing "Songs"
                    parent = current_dir

                    while True:
                        if os.path.isdir(os.path.join(parent, "Songs")):
                            return parent, matching_folder

                        grandparent = os.path.dirname(parent)

                        if grandparent == parent:
                            break

                        parent = grandparent

    return None


def check_path():
    path = path_entry.get().strip()

    # Check empty input first
    if not path:
        messagebox.showerror("Error", "Please select your GAME FOLDER.")
        result_label.config(text="")
        result_label2.config(text="")
        return

    result = find_folder(path)

    if result:
        parent_path, matching_folder = result

        # Update the dropdown immediately
        update_dropdown(parent_path)

        # Input displays the parent folder containing /Songs/
        path_entry.config(state="normal")
        path_entry.delete(0, tk.END)
        path_entry.insert(0, parent_path)
        path_entry.config(state="readonly")

        # Label displays the exact matching folder
        result_label.config(text="NoteSkins folder found: " + matching_folder)
        page2_pathDisplay.config(text=f"This noteskin will be installed at:\n{matching_folder}")
        global cur_path
        cur_path = matching_folder

        ok_button.config(state="normal")
    else:
        ok_button.config(state="disabled")
        messagebox.showerror("Error", "Unable to locate the GAME FOLDER.")
        result_label.config(text="Unable to locate the GAME FOLDER")
        result_label2.config(text="")


def update_dropdown(parent_path):
    dropdown.set("")

    # Get the name of parent_path itself
    folder_name = os.path.basename(os.path.normpath(parent_path)).lower()

    for option, targets in FOLDER_OPTIONS.items():
        for target in targets:
            if target.lower() in folder_name:
                dropdown.set(option)
                result_label2.config(text="GAME automatically detected.")
                return

    print("No matching folder names found:", folder_name)
    result_label2.config(text="GAME unknown.")

def on_ok():
    parent_path = path_entry.get().strip()
    choice = dropdown.get().strip()
    path_parts = parent_path.lower().replace("\\", "/").split("/")
    choice_parts = choice.lower().replace("\\", "/").split("/")
    answer = True

    if not parent_path:
        messagebox.showerror("Error", "Please select your GAME FOLDER.")
        return

    if not choice:
        messagebox.showerror("Error", "Please select a GAME.")
        return

    if not any(
        choice_part in path_part
        for path_part in path_parts
        for choice_part in choice_parts
        if choice_part
    ):
        answer = messagebox.askyesno(
            "Confirm Settings",
            "The GAME FOLDER and the GAME do not match.\nAre you sure you want to continue with the current settings?"
        )

    if not answer:
        return

    customizations_path = os.path.join(root_path, "Customizations")
    previews_path = os.path.join(root_path, "Previews")

    if not os.path.isdir(customizations_path):
        messagebox.showerror(
            "Error",
            "'Customizations' folder not found:\n" + customizations_path
        )
        return

    global customization_dropdowns_created

    if not customization_dropdowns_created:
        create_customization_dropdowns(
            customizations_path,
            previews_path
        )
        customization_dropdowns_created = True

    show_page(page2)


# ---------------------INITIAL WINDOW-------------------------------
root = tk.Tk()
root.title("DanceGroove Noteskin Workshop: THE PROGRAM")
root.update_idletasks()

icon_path = root_path / "icon.ico"
if icon_path.exists():
    try:
        root.iconbitmap(str(icon_path))
    except tk.TclError:
        pass

width = 640
height = 480

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

x = (screen_width - width) // 2
# Make sure the window doesn't hide behind the taskbar
y = max(0, (screen_height - height) // 2 - 25)

root.geometry("{}x{}+{}+{}".format(width, height, x, y))

root.minsize(640, 480)

page1 = tk.Frame(root)
page2 = tk.Frame(root)
page3 = tk.Frame(root)
page1.pack(fill="both", expand=True)


# --- THE ACTUAL ELEMENTS ON PAGE1 ---
# Image
try:
    image = tk.PhotoImage(file="logo.png")
    image = image.subsample(4, 4)
    image_label = tk.Label(page1, image=image)
    image_label.pack(pady=1)
except tk.TclError:
    image = None
    error_label = tk.Label(page1, text="Error: Could not find or load logo.png")
    error_label.pack()

# String input
tk.Label(
    page1,
    text="Select your GAME FOLDER:"
).pack(padx=10, pady=(10, 0))

path_var = tk.StringVar(value="Click here to select...")
path_entry = tk.Entry(
    page1,
    width=70,
    state="readonly",
    textvariable=path_var,
    fg="gray"
)
path_entry.pack(padx=10, pady=5)

def browse_game_folder(event=None):
    folder = filedialog.askdirectory(
        title="Select your Game Folder",
        mustexist=True
    )

    if folder:
        path_var.set(folder)
        path_entry.config(fg="black")


path_entry.bind("<Button-1>", browse_game_folder)


def on_path_change(*args):
    ok_button.config(state="disabled")


path_var.trace_add("write", on_path_change)

tk.Button(page1, text="Locate", command=check_path).pack(pady=5)

result_label = tk.Label(page1, text="")
result_label.pack()
result_label2 = tk.Label(page1, text="")
result_label2.pack()

# Dropdown menu
tk.Label(page1, text="Select your GAME:").pack(pady=(15, 0))

dropdown = ttk.Combobox(
    page1,
    values=["Stepmania 5/ITGmania/Etterna/OutFox", "NotITG/OpenITG"],
    state="readonly",
    width=70
)
dropdown.set("")
dropdown.pack(pady=5)

# OK button
ok_button = tk.Button(
    page1,
    text="OK",
    command=on_ok,
    state="disabled",
    disabledforeground="gray"
)
ok_button.pack(pady=(35, 10))



# ---------------------PAGE 2: CUSTOMIZE YOUR SKIN-------------------------------

preview_label = None
preview_frames = []
preview_frame_index = 0
preview_after_id = None
preview_photo = None

PREVIEW_CATEGORY_MAP = {
    "Holds": "Holds+Rolls",
    "Rolls": "Holds+Rolls",
    "Holds/Directional": "Holds+Rolls/Directional Holds",
    "Rolls/Directional": "Holds+Rolls/Directional Rolls",
    "Arrow Settings - Arrow Gradient/NotITG/Frame": "Arrow Settings - Arrow Gradient",
    "Arrow Settings - Arrow Gradient/NotITG/Body": "Arrow Settings - Arrow Gradient",
    "Arrow Settings - Arrow Gradient/NotITG/Center": "Arrow Settings - Arrow Gradient",
    "Arrow Settings - Arrow Gradient/NotITG/Shine (RGB-Vivid-CAMidi-Only)": "Arrow Settings - Arrow Gradient"
}
#left, top, right, bottom
PREVIEW_CROP_MAP = {
    "Arrow Settings - Arrow Gradient/NotITG/Frame": (10, 0, 573, 0),
    "Arrow Settings - Arrow Gradient/NotITG/Body": (212, 0, 378, 0),
    "Arrow Settings - Arrow Gradient/NotITG/Center": (407, 0, 212, 0),
    "Arrow Settings - Arrow Gradient/NotITG/Shine (RGB-Vivid-CAMidi-Only)": (572, 0, 10, 0),

    "Holds/ITGstyled": (0, 85, 256, 0),
    "Rolls/ITGstyled": (256, 85, 0, 0),
    "Holds/Directional": (0, 85, 0, 0),
    "Rolls/Directional": (0, 85, 0, 0),

    "Mines/ITG": (0, 177, 512*3, 0),
    "Mines/Note": (512, 177, 512*2, 0),
    "Mines/X": (512*2, 177, 512, 0),
    "Mines/Dot": (512*3, 177, 0, 0),

    "Hold Explosions/Minimal": (471, 0, 997, 0),
    "Hold Explosions/Spark": (968, 0, 500, 0),
    "Hold Explosions/Glow": (1452, 0, 0, 0),

    "Tap Explosions/Minimal": (0, 745, 0, 0),
    "Tap Explosions/Spark": (0, 228, 0, 505),
    "Tap Explosions/Glow": (0, 485, 0, 247),
}
PREVIEW_MAX_HEIGHT = {
    "Hold Explosions": 200,
    "Receptors": 170,
    "Mine Explosions": 170,
    "Mines": 150,
    "Arrow Settings - Arrow Gradient/NotITG/Frame": 150,
    "Arrow Settings - Arrow Gradient/NotITG/Body": 150,
    "Arrow Settings - Arrow Gradient/NotITG/Center": 150,
    "Arrow Settings - Arrow Gradient/NotITG/Shine (RGB-Vivid-CAMidi-Only)": 150,
    "Arrow Settings - Freeze Arrows": 200,
}
PREVIEW_FILENAME_REMOVE_WORDS = []
TREAT_CHILDREN_AS_CATEGORIES = [
    "Arrow Settings - Arrow Gradient",
    "Mine Settings"
]
# remove (default) from this
PATH_HAS_ARBITRARY_IMAGE_NAMES = [
    "Arrow Settings - Arrow Gradient/NotITG"
]
# remove (default) from this
PATH_CHECK_NON_EXACT = [
]
PLAYER_SELECTIONS = {}
PAGE2_DROPDOWNS = {}
FOLDER_ORDER_EXCEPTIONS = {
    "Holds": ["Rolls"],
    "Hold Explosions": ["Tap Explosions"],
}
CATEGORY_DESCRIPTIONS = {
    "Arrow Settings - Arrow Gradient/NotITG/Body": f"Change the scrolling direction of the gradient (or make it not scroll) on the body (middle part) of the arrow.",
    "Arrow Settings - Arrow Gradient/NotITG/Center": f"Change the scrolling direction of the gradient (or make it not scroll) on the center of the arrow.",
    "Arrow Settings - Arrow Gradient/NotITG/Frame": f"Change the scrolling direction of the gradient (or make it not scroll) on the frame of the arrow.",
    "Arrow Settings - Arrow Gradient/NotITG/Shine (RGB-Vivid-CAMidi-Only)": f"Change the scrolling direction of the gradient (or make it not scroll) on the shine of the arrow. The shine is an overlay on top of the original arrow (only available in RGB, Vivid and CA Midi arrow variants).",
    "Arrow Settings - Freeze Arrows": f"Switching this to On will make hold heads and roll heads freeze in one frame and become unanimated. (Freeze Position 1 for CA variants will have the arrow's center part be fully unlit, while Freeze Position 2 will have the center part be fully lit)",
    "Mine Settings/Center Animation": f"Switching this to Off and the center of mines will become unanimated. (will not affect Shock Arrows)",
    "Mine Settings/Rotation": f"Switching this to Off will make the mine not rotate.",
    "Holds": f"Recommended to have Holds and Rolls be both ITGstyled or Directional.\n(NOTE: Up and down Default Directional holds will look a bit weird on downscroll in NotITG)",
    "Rolls": f"Recommended to have Holds and Rolls be both ITGstyled or Directional.\n(NOTE: Up and down Default Directional rolls will look a bit weird on downscroll in NotITG)",
    "Receptor Pulse": f"Enable or disable the receptors flashing to the beat.",
    "Tap Explosions": f"In order: (Blue) Fantastic, White Fantastic, Excellent, Great, Decent, Way Off.\nNOTE: The White Fantastic tap explosion is only used in advanced timing windows in Outfox or ITGmania."
}


def clean_folder_name(name):
    # Remove "(default)" at the end, ignoring capitalization
    return re.sub(r"\s*\(default\)$", "", name, flags=re.IGNORECASE)

def sort_folders(folders):
    folders.sort(key=lambda folder: folder["name"].casefold())

    # Move each exception directly after its designated folder
    for anchor, followers in FOLDER_ORDER_EXCEPTIONS.items():
        anchor_index = next(
            (i for i, folder in enumerate(folders)
             if folder["name"].casefold() == anchor.casefold()),
            None
        )

        if anchor_index is None:
            continue

        for follower in followers:
            follower_index = next(
                (i for i, folder in enumerate(folders)
                 if folder["name"].casefold() == follower.casefold()),
                None
            )

            if follower_index is None:
                continue

            item = folders.pop(follower_index)

            # Find the anchor again, since removing an item shifts indices
            anchor_index = next(
                i for i, folder in enumerate(folders)
                if folder["name"].casefold() == anchor.casefold()
            )

            folders.insert(anchor_index + 1, item)

            # Keep multiple followers in their specified order
            anchor = follower

def scan_folders(folder_path):
    result = []

    try:
        entries = sorted(
            os.scandir(folder_path),
            key=lambda e: e.name.lower()
        )

        # Find NotITG or Outfox-ITGmania-Etterna folders at this level
        special_folders = [
            entry for entry in entries
            if entry.is_dir(follow_symlinks=False)
            and entry.name.lower() in ("notitg", "outfox-itgmania-etterna")
        ]

        # If either exists, skip this level and scan inside it
        if special_folders:
            return scan_folders(special_folders[0].path)

        for entry in entries:
            if not entry.is_dir(follow_symlinks=False):
                continue

            if entry.name.lower() == "dancegroove-custom-3d":
                continue

            result.append({
                "name": entry.name,
                "path": entry.path,
                "children": scan_folders(entry.path)
            })

    except OSError:
        pass

    return result


def get_max_depth(nodes):
    if not nodes:
        return 0

    return 1 + max(get_max_depth(node["children"]) for node in nodes)

# --- FUNCTIONS FOR THE CUSTOMIZATION DROPDOWNS ---
# For updating the lower level customization dropdowns when a dropdown has its option changed
def update_customization_options(
    dropdowns,
    level_options,
    level,
    nodes,
    category_name,
    preview_category,
    previews_path,
    preview_label
):
    # Clear this level and all levels below it.
    for i in range(level, len(dropdowns)):
        level_options[i] = []
        dropdowns[i]["values"] = ()
        dropdowns[i].set("")

    # Stop when there are no more dropdown levels.
    if level >= len(dropdowns):
        return

    level_options[level] = nodes
    dropdown = dropdowns[level]
    dropdown["values"] = [node["name"] for node in nodes]

    if nodes:
        # Select the default folder, or the first folder.
        selected_index = 0

        for i, node in enumerate(nodes):
            if node["name"].lower().endswith("(default)"):
                selected_index = i
                break

        dropdown.current(selected_index)

        # Initialize the next level first.
        update_customization_options(
            dropdowns,
            level_options,
            level + 1,
            nodes[selected_index]["children"],
            category_name,
            preview_category,
            previews_path,
            preview_label
        )

    # Update the preview only after all dropdown levels are initialized.
    if level == 0:
        update_preview(
            previews_path,
            category_name,
            preview_category,
            dropdowns,
            level_options,
            preview_label
        )


def on_customization_selected(
    dropdowns,
    level_options,
    level,
    category_name,
    previews_path,
    preview_label
):
    index = dropdowns[level].current()

    if index < 0 or index >= len(level_options[level]):
        return

    selected_node = level_options[level][index]

    # Map the customization category to its preview folder.
    preview_category = category_name

    for key in sorted(PREVIEW_CATEGORY_MAP, key=len, reverse=True):
        if (
            preview_category == key
            or preview_category.startswith(key + "/")
        ):
            preview_category = PREVIEW_CATEGORY_MAP[key] + preview_category[len(key):]
            break

    # First rebuild all child dropdowns and select their defaults.
    update_customization_options(
        dropdowns,
        level_options,
        level + 1,
        selected_node["children"],
        category_name,
        preview_category,
        previews_path,
        preview_label
    )

    # Then update the preview using the completed selections.
    update_preview(
        previews_path,
        category_name,
        preview_category,
        dropdowns,
        level_options,
        preview_label
    )

def cycle_dropdown(dropdown, direction):
    values = dropdown["values"]

    if not values:
        return

    current = dropdown.current()

    # If nothing is selected, start at the first option
    if current < 0:
        current = 0 if direction > 0 else len(values) - 1
    else:
        current = (current + direction) % len(values)

    dropdown.current(current)

    # Trigger the existing selection handler
    dropdown.event_generate("<<ComboboxSelected>>")

def create_customization_dropdowns(customizations_path, previews_path):
    if not os.path.isdir(customizations_path):
        messagebox.showerror(
            "Error",
            "Customizations folder not found:\n" + customizations_path
        )
        return

    # Remove previously generated widgets
    for widget in customization_dropdown_frame.winfo_children():
        widget.destroy()

    # Find immediate category folders
    try:
        folders = []

        for entry in os.scandir(customizations_path):
            if not entry.is_dir(follow_symlinks=False):
                continue

            if entry.name.lower() == "dancegroove-custom-3d":
                continue

            if entry.name in TREAT_CHILDREN_AS_CATEGORIES:
                children = list(os.scandir(entry.path))

                # Prefer NotITG or Outfox-ITGmania-Etterna as the category root
                preferred = next(
                    (
                        child for target in ("NotITG", "Outfox-ITGmania-Etterna")
                        for child in children
                        if child.is_dir(follow_symlinks=False)
                        and child.name.lower() == target.lower()
                    ),
                    None
                )

                category_root = preferred.path if preferred else entry.path
                category_prefix = (
                    entry.name + "/" + preferred.name
                    if preferred else entry.name
                )

                for child in os.scandir(category_root):
                    if child.is_dir(follow_symlinks=False):
                        folders.append({
                            "name": category_prefix + "/" + child.name,
                            "path": child.path
                        })
            else:
                folders.append({
                    "name": entry.name,
                    "path": entry.path
                })

        sort_folders(folders)

    except OSError as error:
        messagebox.showerror("Error", str(error))
        return

    tk.Label(
        customization_dropdown_frame,
        text='SELECT A SUITE',
        font=("Arial", 11, "bold")
    ).pack(anchor="w")

    tk.Label(
        customization_dropdown_frame,
        text="Don't know what customizations to pick? Pick a SUITE pre-customized just for you!",
    ).pack(anchor="w")

    tk.Button(
        customization_dropdown_frame,
        text="OPEN Suite Select",
        command=lambda:
            show_page(page3)
    ).pack(anchor="w",pady=(0,10))

    for folder in folders:
        category_name = folder["name"]
        category_path = folder["path"]

        # One container per category
        category_frame = tk.Frame(customization_dropdown_frame)
        category_frame.pack(fill="x", expand=True, padx=10, pady=(12, 8))

        # If a category in TREAT_CHILDREN_AS_CATEGORIES has its first child as NotITG, then it won't be included in the displayed name
        tk.Label(
            category_frame,
            text=category_name.replace("/", " - ").replace(" - NotITG", "").replace(" (RGB-Vivid-CAMidi-Only)", " (RGB, Vivid, CA Midi variants only)"),
            font=("Arial", 11, "bold")
        ).pack(anchor="w")

        if category_name in CATEGORY_DESCRIPTIONS:
            labil = tk.Label(
                category_frame,
                text="",
                justify="left",
                anchor="w",
                wraplength=560
            )
            labil.pack(fill="x", expand=True)

            labil.config(text=CATEGORY_DESCRIPTIONS[category_name])

            def update_wrap(event, label=labil):
                width = label.winfo_width()
                if width > 1:
                    label.config(wraplength=width)


            labil.bind("<Configure>", update_wrap)

        # Dedicated dropdown container
        dropdown_frame = tk.Frame(category_frame)
        dropdown_frame.pack(fill="x")

        # Dedicated preview for this category
        preview_label = tk.Label(
            category_frame,
            text="No preview available",
            anchor="w"
        )
        preview_label.pack(anchor="w", pady=(5, 0))

        # Build this category's dropdown hierarchy
        tree = scan_folders(category_path)
        depth = get_max_depth(tree)

        dropdowns = []
        control_frames = []
        level_options = []

        for level in range(depth):
            # Container for < button, dropdown, > button
            control_frame = tk.Frame(dropdown_frame)

            dropdown = ttk.Combobox(
                control_frame,
                state="readonly",
                width=30
            )

            for event in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
                dropdown.bind(event, on_mousewheel)

            previous_button = tk.Button(
                control_frame,
                text="<",
                width=1,
                command=lambda d=dropdown:
                    cycle_dropdown(d, -1)
            )

            next_button = tk.Button(
                control_frame,
                text=">",
                width=1,
                command=lambda d=dropdown:
                    cycle_dropdown(d, 1)
            )

            previous_button.pack(side="left")
            dropdown.pack(side="left", padx=2)
            next_button.pack(side="left")

            # Store the actual dropdown and its layout container separately
            dropdowns.append(dropdown)
            control_frames.append(control_frame)
            level_options.append([])

            dropdown.bind(
                "<<ComboboxSelected>>",
                lambda event,
                       d=dropdowns,
                       o=level_options,
                       i=level,
                       c=category_name,
                       p=previews_path,
                       pl=preview_label:
                    on_customization_selected(
                        d, o, i, c, p, pl
                    )
            )

        # Wrap dropdowns and all the controls within this category's own container
        dropdown_frame.bind(
            "<Configure>",
            lambda event, f=dropdown_frame, d=control_frames:
                wrap_dropdowns(event, f, d)
        )

        # Populate dropdowns and load the initial preview
        preview_category = category_name

        for key in sorted(PREVIEW_CATEGORY_MAP, key=len, reverse=True):
            if (
                preview_category == key
                or preview_category.startswith(key + "/")
            ):
                preview_category = PREVIEW_CATEGORY_MAP[key] + preview_category[len(key):]
                break

        PAGE2_DROPDOWNS[category_name] = dropdowns

        update_customization_options(
            dropdowns,
            level_options,
            0,
            tree,
            category_name,       # Original Customizations category
            preview_category,    # Mapped Previews folder
            previews_path,
            preview_label
        )

def wrap_dropdowns(event, frame, dropdowns, gap=10):
    frame_width = event.width
    x = 0
    y = 0
    row_height = 35

    for dropdown in dropdowns:
        dropdown.update_idletasks()
        widget_width = dropdown.winfo_reqwidth()

        if x > 0 and x + widget_width > frame_width:
            x = 0
            y += row_height

        dropdown.place(x=x, y=y)
        x += widget_width + gap

    # Reserve enough height for every row
    required_height = y + row_height

    if frame.winfo_height() != required_height:
        frame.configure(height=required_height)

    # Prevent the frame from shrinking around placed widgets
    frame.pack_propagate(False)



# ---FUNCTIONS FOR THE PREVIEWS---

def update_preview(
    previews_path,
    category_name,         # Original Customizations category
    preview_category,      # Mapped Previews folder
    dropdowns,
    level_options,
    preview_label
):
    # Identify this update so stale background loads can be ignored.
    preview_label._load_id = getattr(preview_label, "_load_id", 0) + 1
    load_id = preview_label._load_id

    category_path = os.path.join(previews_path, preview_category)
    image_extensions = (".png", ".jpg", ".jpeg", ".bmp", ".gif")

    selected_names_with_default = []
    # Get selected names, removing "(default)".
    selected_names = []

    for level, dropdown in enumerate(dropdowns):
        if level >= len(level_options) or not level_options[level]:
            break

        index = dropdown.current()

        if index < 0 or index >= len(level_options[level]):
            break

        # Use the node corresponding to the current dropdown selection.
        selected_node = level_options[level][index]
        name = selected_node["name"]

        selected_names_with_default.append(name)

        name = re.sub(
            r"\s*\(default\)$",
            "",
            name,
            flags=re.IGNORECASE
        ).strip()

        selected_names.append(name)

    def find_image(folder_path, selected_name=None):
        # Search only inside the selected folder, preferring its named image.
        if not os.path.isdir(folder_path):
            return None

        try:
            entries = sorted(
                os.scandir(folder_path),
                key=lambda entry: entry.name.lower()
            )

            # Prefer an image whose filename matches the final selection.
            if selected_name:
                for entry in entries:
                    if (
                        entry.is_file()
                        and os.path.splitext(entry.name)[0].lower()
                        == selected_name.lower()
                        and entry.name.lower().endswith(image_extensions)
                    ):
                        return entry.path

            # Search child folders, but allow arbitrary images for specified categories
            current_cust_path = os.path.relpath(folder_path, previews_path).replace("\\", "/")

            if any(
                current_cust_path == path
                or current_cust_path.startswith(path + "/")
                for path in PATH_HAS_ARBITRARY_IMAGE_NAMES
            ):
                for entry in entries:
                    if entry.is_file(follow_symlinks=False):
                        if entry.name.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
                            return entry.path

            # Otherwise, do not accept arbitrary images from the current folder
            for entry in entries:
                if entry.is_dir(follow_symlinks=False):
                    result = find_image(entry.path, selected_name)
                    if result:
                        return result

        except OSError:
            pass

        return None

    def candidate_paths(names):
        # Try selected folder names in order, allowing missing levels.
        candidates = []

        for count in range(len(names), -1, -1):
            for subset in combinations(names, count):
                path = os.path.join(category_path, *subset)

                if os.path.isdir(path):
                    candidates.append((count, path))

            if candidates:
                break

        return candidates

    
    image_path = None
    PLAYER_SELECTIONS[category_name] = selected_names_with_default

    # Stop the previous GIF animation if one is playing
    if hasattr(preview_label, "_gif_after_id"):
        try:
            preview_label.after_cancel(preview_label._gif_after_id)
        except Exception:
            pass

    preview_label._gif_after_id = None

    # TO-DO: might need to clean this shit up but god i'm so tired of all this path matching already
    if os.path.isdir(category_path):
        selected_cust_path = "/".join([category_name] + selected_names)

        mapped_path = selected_cust_path

        for key in sorted(PREVIEW_CATEGORY_MAP, key=len, reverse=True):
            if mapped_path == key or mapped_path.startswith(key + "/"):
                mapped_path = (
                    PREVIEW_CATEGORY_MAP[key]
                    + mapped_path[len(key):]
                )
                break

        mapped_parts = mapped_path.split("/")

        category_path = os.path.join(previews_path, mapped_parts[0])
        mapped_selected_names = mapped_parts[1:]

        if any(
            selected_cust_path == path
            or selected_cust_path.startswith(path + "/")
            for path in PATH_HAS_ARBITRARY_IMAGE_NAMES
        ):
            # This category always uses an image from its preview folder,
            # regardless of the selected dropdown options.
            for entry in sorted(
                os.scandir(category_path),
                key=lambda entry: entry.name.lower()
            ):
                if (
                    entry.is_file(follow_symlinks=False)
                    and entry.name.lower().endswith(image_extensions)
                ):
                    image_path = entry.path
                    break

        elif selected_names:
            # Use the mapped path components for preview searching
            search_names = mapped_parts[1:]
            last_selected = search_names[-1]

            # Try the original final dropdown name first.
            filename_candidates = [last_selected]

            # Then try removing configured words from that name.
            fallback_name = last_selected

            for word in PREVIEW_FILENAME_REMOVE_WORDS:
                fallback_name = re.sub(
                    r"\b" + re.escape(word) + r"\b",
                    "",
                    fallback_name,
                    flags=re.IGNORECASE
                )

            fallback_name = re.sub(r"\s+", " ", fallback_name).strip()

            if fallback_name and fallback_name.lower() != last_selected.lower():
                filename_candidates.append(fallback_name)

            # Search the same parent folders as the original code.
            # Check whether this selected path allows partial filename matches
            selected_path = "/".join([category_name] + selected_names)

            allow_partial_match = any(
                selected_path == path or selected_path.startswith(path + "/")
                for path in PATH_CHECK_NON_EXACT
            )

            for count in range(len(search_names) - 1, -1, -1):
                for subset in combinations(search_names[:-1], count):
                    parent_path = os.path.join(category_path, *subset)

                    if not os.path.isdir(parent_path):
                        continue

                    try:
                        entries = sorted(
                            os.scandir(parent_path),
                            key=lambda entry: entry.name.lower()
                        )
                    except OSError:
                        continue

                    for name in filename_candidates:
                        for entry in entries:
                            if not entry.is_file(follow_symlinks=False):
                                continue

                            if not entry.name.lower().endswith(image_extensions):
                                continue

                            filename = os.path.splitext(entry.name)[0].lower()
                            target = name.lower()

                            if (
                                filename == target
                                or (
                                    allow_partial_match
                                    and (
                                        target in filename
                                        or filename in target
                                    )
                                )
                            ):
                                image_path = entry.path
                                break

                        if image_path:
                            break

                    if image_path:
                        break

                if image_path:
                    break

            # If no matching image filename exists, look for a folder
            # matching the final selection, allowing missing levels.
            if image_path is None:
                candidates = candidate_paths(search_names)

                if candidates:
                    _, best_path = candidates[0]

                    if os.path.basename(best_path).lower() == last_selected.lower():
                        image_path = find_image(best_path, last_selected)

    if image_path is None:
        preview_label.configure(
            image="",
            text="No preview available"
        )
        preview_label.image = None
        preview_label._gif_photos = None
        return

    try:
        preview_label._gif_after_id = None

        # Build crop keys from the selected dropdowns.
        crop_keys = [category_name]
        current_key = category_name

        for name in selected_names:
            current_key += "/" + name
            crop_keys.append(current_key)

        # Most-specific crop rule takes priority.
        crop = (0, 0, 0, 0)

        for key in reversed(crop_keys):
            if key in PREVIEW_CROP_MAP:
                crop = PREVIEW_CROP_MAP[key]
                break

        left, top, right, bottom = crop

        max_height = 300

        for key in reversed(crop_keys):
            if key in PREVIEW_MAX_HEIGHT:
                max_height = PREVIEW_MAX_HEIGHT[key]
                break

        def prepare_frame(frame):
            frame = frame.copy().convert("RGBA")
            width, height = frame.size

            if left + right < width and top + bottom < height:
                frame = frame.crop((
                    left,
                    top,
                    width - right,
                    height - bottom
                ))

            frame.thumbnail(
                (550, max_height),
                Image.LANCZOS
            )

            return frame

        # Display the first frame immediately.
        with Image.open(image_path) as image:
            first_frame = prepare_frame(image)

        first_photo = ImageTk.PhotoImage(first_frame)

        preview_label.configure(image=first_photo, text="")
        preview_label.image = first_photo
        preview_label._gif_photos = [first_photo]
        preview_label._gif_index = 0

        results = queue.Queue(maxsize=1)

        # image loading code i totally did not steal
        def load_image():
            try:
                frames = []
                durations = []

                with Image.open(image_path) as image:
                    is_animated = (
                        image.format == "GIF"
                        and getattr(image, "is_animated", False)
                    )

                    if is_animated:
                        for frame in ImageSequence.Iterator(image):
                            # Capture duration before processing the frame.
                            duration = max(
                                20,
                                frame.info.get("duration", 100)
                            )

                            frames.append(prepare_frame(frame))
                            durations.append(duration)

                    else:
                        frames.append(prepare_frame(image))
                        durations.append(100)

                if not frames:
                    raise ValueError("Image contains no frames")

                results.put((
                    frames,
                    durations,
                    is_animated,
                    None
                ))

            except Exception as error:
                results.put((None, None, False, error))

        # Decode, crop and resize away from Tkinter's main thread.
        threading.Thread(
            target=load_image,
            daemon=True
        ).start()

        def check_results():
            # Stop polling if another preview was requested.
            if load_id != preview_label._load_id:
                return

            try:
                frames, durations, is_animated, error = (
                    results.get_nowait()
                )
            except queue.Empty:
                preview_label._gif_after_id = preview_label.after(
                    30, check_results
                )
                return

            preview_label._gif_after_id = None

            if error is not None:
                preview_label.configure(
                    image="",
                    text="Unable to load preview"
                )
                preview_label.image = None
                preview_label._gif_photos = None

                print("Preview error:", image_path, error)
                return

            photos = []

            def create_photos(start=0):
                if load_id != preview_label._load_id:
                    return

                # Create only five Tkinter images per callback.
                end = min(start + 5, len(frames))

                try:
                    for i in range(start, end):
                        photos.append(
                            ImageTk.PhotoImage(frames[i])
                        )
                except Exception as error:
                    preview_label.configure(
                        image="",
                        text="Unable to load preview"
                    )
                    preview_label.image = None
                    preview_label._gif_photos = None

                    print("Preview error:", image_path, error)
                    return

                if end < len(frames):
                    preview_label._gif_after_id = preview_label.after(
                        1,
                        lambda: create_photos(end)
                    )
                    return

                # Keep references so Tkinter does not discard the images.
                preview_label._gif_photos = photos
                preview_label._gif_index = 0

                preview_label.configure(
                    image=photos[0],
                    text=""
                )
                preview_label.image = photos[0]

                if is_animated and len(photos) > 1:
                    animate_gif()

            def animate_gif():
                if load_id != preview_label._load_id:
                    return

                preview_label._gif_index = (
                    preview_label._gif_index + 1
                ) % len(photos)

                index = preview_label._gif_index
                photo = photos[index]

                preview_label.configure(image=photo)
                preview_label.image = photo

                preview_label._gif_after_id = preview_label.after(
                    durations[index],
                    animate_gif
                )

            create_photos()

        # Poll without blocking the GUI.
        check_results()

    except Exception as error:
        preview_label.configure(
            image="",
            text="Unable to load preview"
        )
        preview_label.image = None
        preview_label._gif_photos = None

        print("Preview error:", image_path, error)

def find_custom_3d_folder(category, selections, selected_game, folder_name):
    customizations_path = os.path.join(
            root_path,
            "Customizations"
        )
    current_path = os.path.join(customizations_path, category)

    if not os.path.isdir(current_path):
        return None

    for selection in selections:

        # Handle NotITG/Outfox-ITGmania-Etterna folders wherever they appear
        game_choice_folders = [
            name for name in ("NotITG", "Outfox-ITGmania-Etterna")
            if os.path.isdir(os.path.join(current_path, name))
        ]

        if game_choice_folders:
            if selected_game not in game_choice_folders:
                return None

            current_path = os.path.join(current_path, selected_game)

        # Follow the next selected customization
        current_path = os.path.join(current_path, selection)

        if not os.path.isdir(current_path):
            return None

    # Check the final selected folder
    custom_3d_path = os.path.join(current_path, folder_name)
    if os.path.isdir(custom_3d_path):
        return custom_3d_path

    # Search below the final selected folder for dancegroove-custom-3d
    for root, dirs, files in os.walk(current_path):
        if folder_name in dirs:
            return os.path.join(root, folder_name)

    return None

def read_saved_selections():
    try:
        with open(SAVED_SELECTIONS_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        return {}
    except (json.JSONDecodeError, OSError):
        return {}

def save_named_selection(name):
    name = name.strip()

    if not name:
        return False

    saved = read_saved_selections()
    saved[name] = copy.deepcopy(PLAYER_SELECTIONS)

    with open(SAVED_SELECTIONS_FILE, "w", encoding="utf-8") as file:
        json.dump(saved, file, indent=4)

    return True

def install_skin(CURRENT_PATH):
    if not noteskin_name_entry.get().strip():
        messagebox.showwarning(
            "Error",
            "Please give this noteskin a NAME."
        )
        return
    answer = messagebox.askyesno(
        "Confirm Settings",
        f"About to install noteskin:\n{CURRENT_PATH}\\{noteskin_name_entry.get()}\n\nThis will also OVERWRITE any existing noteskin with the same name. Continue?"
    )
    if not answer:
        return

    directionTypeMismatch = False
    if PLAYER_SELECTIONS["Holds"][0] != PLAYER_SELECTIONS["Rolls"][0]:
        directionTypeMismatch = True
        answer2 = messagebox.askyesno(
            "Confirm Settings",
            f"Hold type ({PLAYER_SELECTIONS["Holds"][0]}) and Roll type ({PLAYER_SELECTIONS["Rolls"][0]}) mismatch.\nTHE PROGRAM will perform some extra actions, but your noteskin may still have some visual caveats.\nContinue?"
        )
        if not answer2:
            return
    
    folder_name = "dancegroove-custom-3d"
    base_path = os.path.join(
        root_path,
        "DanceGroove - BASE"
    )
    GameState = dropdown.get()

    # Choose the desired folder
    if GameState == "Stepmania 5/ITGmania/Etterna/OutFox":
        selected_game = "Outfox-ITGmania-Etterna"
    else:
        selected_game = "NotITG"

    # Source: BASE/NotITG/dancegroove-custom-3d or the other one
    source_mclb = os.path.join(
        base_path,
        selected_game,
        folder_name
    )

    if not os.path.isdir(source_mclb):
        messagebox.showerror("Error", "Failed to find dancegroove-custom-3d inside DanceGroove - BASE.")
        return False

    # any item with [0] as Directional (e.g. PLAYER_SELECTIONS["Holds"][0] = "Directional") will be checked last.
    sorted_selections = sorted(
        (
            (category, selections)
            for category, selections in PLAYER_SELECTIONS.items()
            if not (category == "Lifts" and selected_game == "NotITG")
        ),
        key=lambda item: item[1][0] == "Directional"
    )

    # Create a temporary working copy of source_mclb
    with tempfile.TemporaryDirectory() as temp_dir:
        working_mclb = os.path.join(temp_dir, "dancegroove-custom-3d")

        # Copy the original into the working folder
        shutil.copytree(source_mclb, working_mclb)

        # Merge customizations into the working copy
        for category, selections in sorted_selections:
            source_customizations = find_custom_3d_folder(
                category,
                selections,
                selected_game,
                folder_name
            )

            print('The source:', source_customizations)

            if source_customizations:
                shutil.copytree(
                    source_customizations,
                    working_mclb,
                    dirs_exist_ok=True
                )

        # Destination: CURRENT_PATH/dancegroove-custom-3d or user's chosen name
        destination = os.path.join(CURRENT_PATH, noteskin_name_entry.get())

        # Remove existing destination
        if os.path.exists(destination):
            if os.path.isdir(destination) and not os.path.islink(destination):
                shutil.rmtree(destination)
            else:
                os.remove(destination)

        # Copy the finished working copy to destination
        shutil.copytree(working_mclb, destination)

    if selected_game == "Outfox-ITGmania-Etterna":
        messagebox.showinfo("Notice", "Noteskin installed. Reload theme and textures (F2 or F3+F6+6) in your GAME to apply the changes.")
    else:
        messagebox.showinfo("Notice", "Noteskin installed. Restart the GAME to apply the changes.")
    return True


def validate_name_entry(value):
    return re.fullmatch(r"[A-Za-z0-9+_-]*", value) is not None

vcmd = (root.register(validate_name_entry), "%P")


def save_custom_suite():
    suite_name = noteskin_name_entry.get().strip()

    if not suite_name:
        messagebox.showwarning(
            "Error",
            "Please give this SUITE a NAME."
        )
        return

    saved_suites = read_saved_selections()

    if suite_name in saved_suites:
        overwrite = messagebox.askyesno(
            "Notice",
            f'"{suite_name}" already exists. OVERWRITE it?'
        )

        if not overwrite:
            return

    try:
        save_named_selection(suite_name)
        refresh_saved_selection_names()
        custom_dropdown.set(suite_name)

        messagebox.showinfo(
            "Notice",
            f'"{suite_name}" has been saved as a CUSTOM SUITE.\nYou can select this SUITE any time in Suite Select menu.'
        )

    except OSError as error:
        messagebox.showerror("Save Failed", str(error))


# --- THE ACTUAL ELEMENTS ON PAGE2 ---

page2_pathDisplay = tk.Label(page2, text="")
page2_pathDisplay.pack()

name_entry_frame = tk.Frame(page2)
name_entry_frame.pack(pady=(10, 10))

tk.Label(name_entry_frame, text="My noteskin's NAME is:").pack(side="left", padx=5)

noteskin_name_entry = tk.Entry(
    name_entry_frame,
    width=35,
    validate="key",
    validatecommand=vcmd
)
noteskin_name_entry.pack(side="left", padx=5)
noteskin_name_entry.insert(0, "dancegroove-custom-3d")

button_frame = tk.Frame(page2)
button_frame.pack(pady=(0, 10))

# Back button
back_button = tk.Button(
    button_frame,
    text="BACK to Game Select",
    command=lambda: show_page(page1),
)
back_button.pack(side="left", padx=5)

suite_save_button = tk.Button(
    button_frame,
    text="SAVE as SUITE",
    command=save_custom_suite
)
suite_save_button.pack(side="left", padx=5)

save_button = tk.Button(
    button_frame,
    text="INSTALL Noteskin",
    command=lambda: install_skin(cur_path),
)
save_button.pack(side="left", padx=5)

# Scrollable area on page2
# Container for the scrolling area
scroll_container = tk.Frame(page2)
scroll_container.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=5
)

page2_canvas = tk.Canvas(scroll_container)
page2_scrollbar = ttk.Scrollbar(
    scroll_container,
    orient="vertical",
    command=page2_canvas.yview
)

page2_canvas.configure(
    yscrollcommand=page2_scrollbar.set
)

page2_scrollbar.pack(side="right", fill="y")
page2_canvas.pack(side="left", fill="both", expand=True)

# Frame containing all customization dropdowns
customization_dropdown_frame = tk.Frame(page2_canvas)

page2_window = page2_canvas.create_window(
    (0, 0),
    window=customization_dropdown_frame,
    anchor="nw"
)

# Update scrollable area when content changes
def update_scroll_region(event=None):
    page2_canvas.configure(
        scrollregion=page2_canvas.bbox("all")
    )

customization_dropdown_frame.bind(
    "<Configure>", update_scroll_region
)

# Keep the inner frame the same width as the canvas
def resize_page2_frame(event):
    page2_canvas.itemconfigure(
        page2_window,
        width=event.width
    )

page2_canvas.bind("<Configure>", resize_page2_frame)

def on_mousewheel(event):
    widget = event.widget

    # Find the canvas containing the widget
    while widget is not None:
        if widget in (page2_canvas, page3_canvas):
            break

        if not isinstance(widget, tk.Misc):
            return "break"

        parent = widget.winfo_parent()
        if not parent:
            return "break"

        try:
            widget = widget.nametowidget(parent)
        except (KeyError, tk.TclError):
            return "break"

    if widget not in (page2_canvas, page3_canvas):
        return "break"

    # Scroll direction
    if getattr(event, "num", None) == 4:
        amount = -1
    elif getattr(event, "num", None) == 5:
        amount = 1
    elif event.delta:
        amount = -1 if event.delta > 0 else 1
        if abs(event.delta) >= 120:
            amount = -int(event.delta / 120)
    else:
        return "break"

    widget.yview_scroll(amount, "units")
    return "break"

# Windows / macOS
page2_canvas.bind_all("<MouseWheel>", on_mousewheel)

# Linux (X11)
page2_canvas.bind_all("<Button-4>", on_mousewheel)
page2_canvas.bind_all("<Button-5>", on_mousewheel)


# ---------------------PAGE 3: SELECT A SUITE-------------------------------
SUITE_PREVIEW_WIDTH = 500
SUITE_PREVIEW_HEIGHT = 280

import copy

COMMON_SETTINGS = {
    'Arrow Center Animation': ['On - Default (default)'],
    'Arrows': ['{type} (default)', 'ITG (default)'],
    'Hold Explosions': ['{type}', 'Minimal (default)', 'Default (default)'],
    'Holds': ['{type}', 'ITG (default)', 'Default (default)'],
    'Lifts': ['{type} - Hollowed Spectrum (default)'],
    'Mine Settings/Center Animation': ['On (default)'],
    'Mine Settings/Rotation': ['On - ITG (default)'],
    'Mine Settings/Size': ['Normal (default)'],
    'Mines': ['ITG (default)', 'Unquantized (default)', 'Default P1 (default)'],
    'Receptor Animation': ['On - Default (default)'],
    'Receptors': ['{type} - Traditional (default)', 'Gray (default)'],
    'Rolls': ['ITG (default)', 'Default (default)'],
    'Tap Explosions': ['{type}', 'Glow (default)', 'ITG (default)']
}


def create_suite(type, overrides=None):
    suite = {
        category: [option.format(type=type) for option in options]
        for category, options in COMMON_SETTINGS.items()
    }

    if type == 'Vividable':
        suite['Arrow Center Animation'] = ['On - Vividable']

    if overrides:
        for category, options in overrides.items():
            suite[category] = copy.deepcopy(options)

    return suite

BASE_SUITE_CONFIG = {
    'Default Suite': {
            "Arrow Settings - Arrow Gradient/NotITG/Body": ["Normal Scroll (default)"],
            "Arrow Settings - Arrow Gradient/NotITG/Center": ["Normal Scroll (default)"],
            "Arrow Settings - Arrow Gradient/NotITG/Frame": ["Normal Scroll (default)"],
            "Arrow Settings - Arrow Gradient/NotITG/Shine (RGB-Vivid-CAMidi-Only)": ["Normal Scroll (default)"],
            "Arrow Settings - Freeze Arrows": ["Off (default)"],
            "Arrows": ["ITG (default)"],
            "Hold Explosions": ["Minimal (default)","White (default)"],
            "Holds": ["ITGstyled (default)","DDR Hold (default)"],
            "Mine Explosions": ["Default (default)"],
            "Mine Settings/Center Animation": ["On (default)"],
            "Mine Settings/Rotation": ["On (default)"],
            "Mines": ["ITG (Default)","Red (default)"],
            "Receptor Pulse": ["On (default)"],
            "Receptors": ["Center Glow (default)","Gray (default)"],
            "Rolls": ["ITGstyled (default)","Note Roll (default)"],
            "Tap Explosions": ["Spark (default)","ITG (default)"]
        }
}
TEST_SUITE_CONFIG = {
    'Cel Suite': {
            "Arrow Settings - Arrow Gradient/NotITG/Body": ["Normal Scroll (default)"],
            "Arrow Settings - Arrow Gradient/NotITG/Center": ["Normal Scroll (default)"],
            "Arrow Settings - Arrow Gradient/NotITG/Frame": ["Normal Scroll (default)"],
            "Arrow Settings - Arrow Gradient/NotITG/Shine (RGB-Vivid-CAMidi-Only)": ["Normal Scroll (default)"],
            "Arrow Settings - Freeze Arrows": ["Off (default)"],
            "Arrows": ["Lucid Cel Basic"],
            "Hold Explosions": ["Glow","Halloween"],
            "Holds": ["ITGstyled (default)","Gold"],
            "Mine Explosions": ["Spiral Burst","Ocean"],
            "Mine Settings/Center Animation": ["On (default)"],
            "Mine Settings/Rotation": ["On (default)"],
            "Mines": ["ITG (Default)","Ocean"],
            "Receptor Pulse": ["On (default)"],
            "Receptors": ["Center Glow (default)","Christmas"],
            "Rolls": ["ITGstyled (default)","Vapor Shadow"],
            "Tap Explosions": ["Glow","ITG"]
        },
    'Contrast Suite': {
            "Arrow Settings - Arrow Gradient/NotITG/Body": ["Normal Scroll (default)"],
            "Arrow Settings - Arrow Gradient/NotITG/Center": ["Normal Scroll (default)"],
            "Arrow Settings - Arrow Gradient/NotITG/Frame": ["Normal Scroll (default)"],
            "Arrow Settings - Arrow Gradient/NotITG/Shine (RGB-Vivid-CAMidi-Only)": ["Normal Scroll (default)"],
            "Arrow Settings - Freeze Arrows": ["Off (default)"],
            "Arrows": ["ITG Dark"],
            "Hold Explosions": ["Minimal (default)","Orange"],
            "Holds": ["ITGstyled (default)","Ocean Shadow"],
            "Mine Explosions": ["Spiral Burst","Fire"],
            "Mine Settings/Center Animation": ["On (default)"],
            "Mine Settings/Rotation": ["On (default)"],
            "Mines": ["Note","Halloween"],
            "Receptor Pulse": ["On (default)"],
            "Receptors": ["Classic","D A N K"],
            "Rolls": ["ITGstyled (default)","Gold Shadow"],
            "Tap Explosions": ["Minimal","ITG"]
        },
    'Dev Suite': {
            "Arrow Settings - Arrow Gradient/NotITG/Body": ["Normal Scroll (default)"],
            "Arrow Settings - Arrow Gradient/NotITG/Center": ["Normal Scroll (default)"],
            "Arrow Settings - Arrow Gradient/NotITG/Frame": ["Normal Scroll (default)"],
            "Arrow Settings - Arrow Gradient/NotITG/Shine (RGB-Vivid-CAMidi-Only)": ["Normal Scroll (default)"],
            "Arrow Settings - Freeze Arrows": ["Off (default)"],
            "Arrows": ["Dev Modernized Alt"],
            "Hold Explosions": ["Minimal (default)","White (default)"],
            "Holds": ["ITGstyled (default)","White"],
            "Mine Explosions": ["Default (default)"],
            "Mine Settings/Center Animation": ["Off"],
            "Mine Settings/Rotation": ["On (default)"],
            "Mines": ["Note","Gray"],
            "Receptor Pulse": ["On (default)"],
            "Receptors": ["Classic","Gray"],
            "Rolls": ["ITGstyled (default)","Gray Shadow"],
            "Tap Explosions": ["Minimal","ITG"]
        },
    'Gold Suite': {
            "Arrow Settings - Arrow Gradient/NotITG/Body": ["Normal Scroll (default)"],
            "Arrow Settings - Arrow Gradient/NotITG/Center": ["Normal Scroll (default)"],
            "Arrow Settings - Arrow Gradient/NotITG/Frame": ["Normal Scroll (default)"],
            "Arrow Settings - Arrow Gradient/NotITG/Shine (RGB-Vivid-CAMidi-Only)": ["Normal Scroll (default)"],
            "Arrow Settings - Freeze Arrows": ["Off (default)"],
            "Arrows": ["Bright Gold"],
            "Hold Explosions": ["Minimal (default)","Yellow"],
            "Holds": ["ITGstyled (default)","Gold"],
            "Mine Explosions": ["Realistic","Gas Leak"],
            "Mine Settings/Center Animation": ["On (default)"],
            "Mine Settings/Rotation": ["On (default)"],
            "Mines": ["X","Gold"],
            "Receptor Pulse": ["On (default)"],
            "Receptors": ["Center Glow (default)","Gold"],
            "Rolls": ["ITGstyled (default)","Fire Shadow"],
            "Tap Explosions": ["Glow","Nowhere"]
        },
    'Midi Suite': {
            "Arrow Settings - Arrow Gradient/NotITG/Body": ["Static"],
            "Arrow Settings - Arrow Gradient/NotITG/Center": ["Static"],
            "Arrow Settings - Arrow Gradient/NotITG/Frame": ["Normal Scroll (default)"],
            "Arrow Settings - Arrow Gradient/NotITG/Shine (RGB-Vivid-CAMidi-Only)": ["Normal Scroll (default)"],
            "Arrow Settings - Freeze Arrows": ["On - Freeze Position 2"],
            "Arrows": ["Note 2 ITG CA Midi"],
            "Hold Explosions": ["Spark","Ocean"],
            "Holds": ["ITGstyled (default)","Green"],
            "Mine Explosions": ["Default (default)"],
            "Mine Settings/Center Animation": ["On (default)"],
            "Mine Settings/Rotation": ["On (default)"],
            "Mines": ["X","Falspawn"],
            "Receptor Pulse": ["On (default)"],
            "Receptors": ["Classic","Blue"],
            "Rolls": ["ITGstyled (default)","Pink"],
            "Tap Explosions": ["Minimal","ITG"]
        },
    'Note Suite': {
            "Arrow Settings - Arrow Gradient/NotITG/Body": ["Normal Scroll (default)"],
            "Arrow Settings - Arrow Gradient/NotITG/Center": ["Normal Scroll (default)"],
            "Arrow Settings - Arrow Gradient/NotITG/Frame": ["Normal Scroll (default)"],
            "Arrow Settings - Arrow Gradient/NotITG/Shine (RGB-Vivid-CAMidi-Only)": ["Normal Scroll (default)"],
            "Arrow Settings - Freeze Arrows": ["On - Freeze Position 1"],
            "Arrows": ["Yuisin ITG CA Alt"],
            "Hold Explosions": ["Minimal (default)","DDR Hold"],
            "Holds": ["ITGstyled (default)","DDR Hold (default)"],
            "Mine Explosions": ["Shock Arrow","Default"],
            "Mine Settings/Center Animation": ["On (default)"],
            "Mine Settings/Rotation": ["Off"],
            "Mines": ["Shock Arrow","Default"],
            "Receptor Pulse": ["On (default)"],
            "Receptors": ["Center Glow (default)","Note Roll"],
            "Rolls": ["ITGstyled (default)","Purple Shadow"],
            "Tap Explosions": ["Spark (default)","ITG (default)"]
        },
    'Rainbow Suite': {
            "Arrow Settings - Arrow Gradient/NotITG/Body": ["Normal Scroll (default)"],
            "Arrow Settings - Arrow Gradient/NotITG/Center": ["Normal Scroll (default)"],
            "Arrow Settings - Arrow Gradient/NotITG/Frame": ["Normal Scroll (default)"],
            "Arrow Settings - Arrow Gradient/NotITG/Shine (RGB-Vivid-CAMidi-Only)": ["Normal Scroll (default)"],
            "Arrow Settings - Freeze Arrows": ["On - Freeze Position 1"],
            "Arrows": ["Lemma DDRainbow CA"],
            "Hold Explosions": ["Minimal (default)","RGB"],
            "Holds": ["ITGstyled (default)","Orange"],
            "Mine Explosions": ["Shock Arrow","RGB"],
            "Mine Settings/Center Animation": ["On (default)"],
            "Mine Settings/Rotation": ["Off"],
            "Mines": ["Shock Arrow","RGB"],
            "Receptor Pulse": ["On (default)"],
            "Receptors": ["Classic","Halloween"],
            "Rolls": ["ITGstyled (default)","Lemma Roll"],
            "Tap Explosions": ["Minimal","ITG"]
        },
    'Shadow Suite': {
            "Arrow Settings - Arrow Gradient/NotITG/Body": ["Normal Scroll (default)"],
            "Arrow Settings - Arrow Gradient/NotITG/Center": ["Normal Scroll (default)"],
            "Arrow Settings - Arrow Gradient/NotITG/Frame": ["Normal Scroll (default)"],
            "Arrow Settings - Arrow Gradient/NotITG/Shine (RGB-Vivid-CAMidi-Only)": ["Normal Scroll (default)"],
            "Arrow Settings - Freeze Arrows": ["Off (default)"],
            "Arrows": ["ITG Shadow"],
            "Hold Explosions": ["Minimal (default)","Fire"],
            "Holds": ["ITGstyled (default)","Lemma Roll Shadow"],
            "Mine Explosions": ["Default (default)"],
            "Mine Settings/Center Animation": ["On (default)"],
            "Mine Settings/Rotation": ["On (default)"],
            "Mines": ["ITG (Default)","Fire"],
            "Receptor Pulse": ["On (default)"],
            "Receptors": ["Classic","Falspawn"],
            "Rolls": ["ITGstyled (default)","Red Shadow"],
            "Tap Explosions": ["Minimal","ITG"]
        },
    'Universe Suite': {
            "Arrow Settings - Arrow Gradient/NotITG/Body": ["Reverse Scroll"],
            "Arrow Settings - Arrow Gradient/NotITG/Center": ["Normal Scroll (default)"],
            "Arrow Settings - Arrow Gradient/NotITG/Frame": ["Normal Scroll (default)"],
            "Arrow Settings - Arrow Gradient/NotITG/Shine (RGB-Vivid-CAMidi-Only)": ["Normal Scroll (default)"],
            "Arrow Settings - Freeze Arrows": ["On - Freeze Position 2"],
            "Arrows": ["DDR Order CA Alt"],
            "Hold Explosions": ["Glow","Gold"],
            "Holds": ["ITGstyled (default)","Blue"],
            "Mine Explosions": ["Spiral Burst","Default"],
            "Mine Settings/Center Animation": ["On (default)"],
            "Mine Settings/Rotation": ["On (default)"],
            "Mines": ["Note","Falspawn"],
            "Receptor Pulse": ["On (default)"],
            "Receptors": ["Classic","Vapor"],
            "Rolls": ["ITGstyled (default)","Fire"],
            "Tap Explosions": ["Spark (default)","Nowhere"]
        }
}

def batch_update_page2_dropdowns():
    for category, selections in PLAYER_SELECTIONS.items():
        dropdowns = PAGE2_DROPDOWNS.get(category, [])

        for dropdown, selection in zip(dropdowns, selections):
            dropdown.set(selection)
            dropdown.event_generate("<<ComboboxSelected>>")

def randomize_page2_dropdowns():
    for category, dropdowns in PAGE2_DROPDOWNS.items():
        for dropdown in dropdowns:
            options = dropdown["values"]

            if options:
                dropdown.set(random.choice(options))
                dropdown.event_generate("<<ComboboxSelected>>")

def update_suite_preview(
    previews_path,
    suite_name,
    the_preview_label
):
    # Cancel previous animation
    if hasattr(the_preview_label, "_gif_after_id"):
        if the_preview_label._gif_after_id is not None:
            the_preview_label.after_cancel(the_preview_label._gif_after_id)

    the_preview_label._gif_after_id = None

    category_path = os.path.join(previews_path, "TEST SUITES")
    image_extensions = (".png", ".jpg", ".jpeg", ".bmp", ".gif")
    
    # category_path\suite_name .png/.gif/etc. or None
    image_path = next(
        (
            os.path.join(category_path, f"{suite_name}{ext}")
            for ext in image_extensions
            if os.path.isfile(os.path.join(category_path, f"{suite_name}{ext}"))
        ),
        None
    )

    if image_path is None:
        the_preview_label.configure(
            image="",
            text="No preview available"
        )
        the_preview_label.image = None
        return

    # Unique ID so an older load cannot overwrite a newer selection
    the_preview_label._load_id = getattr(the_preview_label, "_load_id", 0) + 1
    load_id = the_preview_label._load_id

    # Immediately display the first frame while the rest loads.
    try:
        with Image.open(image_path) as image:
            first_frame = image.copy()
            first_frame.thumbnail(
                (SUITE_PREVIEW_WIDTH, SUITE_PREVIEW_HEIGHT)
            )

        first_photo = ImageTk.PhotoImage(first_frame)

        the_preview_label.configure(image=first_photo, text="")
        the_preview_label.image = first_photo
        the_preview_label._gif_photos = [first_photo]
        the_preview_label._gif_index = 0

    except Exception as error:
        the_preview_label.configure(image="", text="Unable to load preview")
        the_preview_label.image = None
        print("Preview error:", image_path, error)
        return

    results = queue.Queue()

    def load_image():
        try:
            frames = []
            durations = []

            with Image.open(image_path) as image:
                for frame in ImageSequence.Iterator(image):
                    frame = frame.copy()
                    frame.thumbnail((SUITE_PREVIEW_WIDTH, SUITE_PREVIEW_HEIGHT))

                    frames.append(frame)
                    durations.append(
                        max(20, frame.info.get("duration", 100))
                    )

            results.put((load_id, frames, durations, None))

        except Exception as error:
            results.put((load_id, None, None, error))

    # Start background loading
    threading.Thread(target=load_image, daemon=True).start()

    def check_results():
        try:
            result_id, frames, durations, error = results.get_nowait()
        except queue.Empty:
            the_preview_label.after(50, check_results)
            return

        # Ignore results from an outdated selection
        if result_id != the_preview_label._load_id:
            return

        if error:
            the_preview_label.configure(image="", text="Unable to load preview")
            the_preview_label.image = None
            print("Preview error:", image_path, error)
            return

        photos = []

        # Create PhotoImages in small batches on Tkinter's main thread
        def create_photos(start=0):
            if load_id != the_preview_label._load_id:
                return

            end = min(start + 5, len(frames))

            for i in range(start, end):
                photos.append(ImageTk.PhotoImage(frames[i]))

            if end < len(frames):
                the_preview_label.after(1, lambda: create_photos(end))
            else:
                the_preview_label._gif_photos = photos
                the_preview_label._gif_durations = durations
                the_preview_label._gif_index = 0

                the_preview_label.configure(image=photos[0], text="")
                the_preview_label.image = photos[0]

                if len(photos) > 1:
                    animate_gif()

        def animate_gif():
            if load_id != the_preview_label._load_id:
                return

            the_preview_label._gif_index = (
                the_preview_label._gif_index + 1
            ) % len(photos)

            index = the_preview_label._gif_index
            the_preview_label.configure(image=photos[index])
            the_preview_label.image = photos[index]

            the_preview_label._gif_after_id = the_preview_label.after(
                durations[index], animate_gif
            )

        if frames:
            create_photos()
        else:
            the_preview_label.configure(image="", text="No preview available")
            the_preview_label.image = None

    check_results()


# ---ACTUAL ELEMENTS ON PAGE3---

# Back button
tk.Button(
    page3,
    text="BACK to Noteskin Customization",
    command=lambda: show_page(page2),
).pack(anchor="w", pady=10)

# Scrollable container
page3_scroll_area = tk.Frame(page3)
page3_scroll_area.pack(fill="both", expand=True)

page3_canvas = tk.Canvas(page3_scroll_area)
page3_scrollbar = tk.Scrollbar(
    page3_scroll_area,
    orient="vertical",
    command=page3_canvas.yview
)

page3_canvas.configure(yscrollcommand=page3_scrollbar.set)

page3_scrollbar.pack(side="right", fill="y")
page3_canvas.pack(side="left", fill="both", expand=True)

# Container for all scrollable widgets
page3_container = tk.Frame(page3_canvas)

page3_canvas_window = page3_canvas.create_window(
    (0, 0),
    window=page3_container,
    anchor="nw"
)

# Update the scrollable area when widgets are added or resized
page3_container.bind(
    "<Configure>",
    lambda event: page3_canvas.configure(
        scrollregion=page3_canvas.bbox("all")
    )
)

# Keep the inner frame the same width as the canvas
page3_canvas.bind(
    "<Configure>",
    lambda event: page3_canvas.itemconfigure(
        page3_canvas_window,
        width=event.width
    )
)

# Windows / macOS
page3_canvas.bind_all("<MouseWheel>", on_mousewheel)

# Linux (X11)
page3_canvas.bind_all("<Button-4>", on_mousewheel)
page3_canvas.bind_all("<Button-5>", on_mousewheel)

# --- BASE SUITES
base_suite_frame = tk.Frame(page3_container)
base_suite_frame.pack(fill="x", padx=10, pady=(5, 8))

tk.Label(
    base_suite_frame,
    text='BASE SUITES',
    font=("Arial", 11, "bold")
).pack(anchor="w",pady=(0,5))

base_dropdown = ttk.Combobox(
    base_suite_frame,
    width=30,
    state="readonly",
    values=list(BASE_SUITE_CONFIG.keys())
)
for event in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
    base_dropdown.bind(event, on_mousewheel)
base_dropdown.bind(
    "<<ComboboxSelected>>",
    lambda event: update_suite_preview(
        os.path.join(root_path, "Previews"),
        base_dropdown.get(),
        base_preview_label
    )
)

base_previous_button = tk.Button(
    base_suite_frame,
    text="<",
    width=1,
    command=lambda d=base_dropdown:
        cycle_dropdown(d, -1)
)

base_next_button = tk.Button(
    base_suite_frame,
    text=">",
    width=1,
    command=lambda d=base_dropdown:
        cycle_dropdown(d, 1)
)

def load_base_suite():
    answer = messagebox.askyesno(
        "Confirm Settings",
        "This will OVERWRITE all current customizations with those of this SUITE.\nContinue?"
    )

    if not answer:
        return
    
    global PLAYER_SELECTIONS

    PLAYER_SELECTIONS = copy.deepcopy(
        BASE_SUITE_CONFIG[base_dropdown.get()]
    )
    batch_update_page2_dropdowns()

base_set = tk.Button(
    base_suite_frame,
    text="Use this SUITE",
    command=load_base_suite
)

base_previous_button.pack(side="left")
base_dropdown.pack(side="left", padx=2)
base_next_button.pack(side="left")
base_set.pack(side="left", padx=10)

base_preview_label = tk.Label(
    page3_container,
    text="No preview available",
    anchor="w"
)
base_preview_label.pack(anchor="w", pady=(5, 10))

base_dropdown.current(0)
update_suite_preview(
    os.path.join(root_path, "Previews"),
    base_dropdown.get(),
    base_preview_label
)


# --- TEST SUITES
test_suite_frame = tk.Frame(page3_container)
test_suite_frame.pack(fill="x", padx=10, pady=(5, 8))

tk.Label(
    test_suite_frame,
    text='TEST SUITES',
    font=("Arial", 11, "bold")
).pack(anchor="w",pady=(0,5))

test_dropdown = ttk.Combobox(
    test_suite_frame,
    width=30,
    state="readonly",
    values=list(TEST_SUITE_CONFIG.keys())
)
for event in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
    test_dropdown.bind(event, on_mousewheel)
test_dropdown.bind(
    "<<ComboboxSelected>>",
    lambda event: update_suite_preview(
        os.path.join(root_path, "Previews"),
        test_dropdown.get(),
        test_preview_label
    )
)

test_previous_button = tk.Button(
    test_suite_frame,
    text="<",
    width=1,
    command=lambda d=test_dropdown:
        cycle_dropdown(d, -1)
)

test_next_button = tk.Button(
    test_suite_frame,
    text=">",
    width=1,
    command=lambda d=test_dropdown:
        cycle_dropdown(d, 1)
)

def load_test_suite():
    answer = messagebox.askyesno(
        "Confirm Settings",
        "This will OVERWRITE all current customizations with those of this SUITE.\nContinue?"
    )

    if not answer:
        return
    
    global PLAYER_SELECTIONS

    PLAYER_SELECTIONS = copy.deepcopy(
        TEST_SUITE_CONFIG[test_dropdown.get()]
    )
    batch_update_page2_dropdowns()

test_set = tk.Button(
    test_suite_frame,
    text="Use this SUITE",
    command=load_test_suite
)

test_previous_button.pack(side="left")
test_dropdown.pack(side="left", padx=2)
test_next_button.pack(side="left")
test_set.pack(side="left", padx=10)

test_preview_label = tk.Label(
    page3_container,
    text="No preview available",
    anchor="w"
)
test_preview_label.pack(anchor="w", pady=(5, 10))

test_dropdown.current(0)
update_suite_preview(
    os.path.join(root_path, "Previews"),
    test_dropdown.get(),
    test_preview_label
)


# --- CUSTOM SUITES
custom_suite_frame = tk.Frame(page3_container)
custom_suite_frame.pack(fill="x", padx=10, pady=(5, 8))

tk.Label(
    custom_suite_frame,
    text='CUSTOM SUITES',
    font=("Arial", 11, "bold")
).pack(anchor="w",pady=(0,5))

custom_dropdown = ttk.Combobox(
    custom_suite_frame,
    width=30,
    state="readonly"
)
for event in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
    custom_dropdown.bind(event, on_mousewheel)

def refresh_saved_selection_names():
    names = list(read_saved_selections().keys())
    custom_dropdown["values"] = names

    if names:
        if custom_dropdown.get() not in names:
            custom_dropdown.current(0)
    else:
        custom_dropdown.set("")

custom_previous_button = tk.Button(
    custom_suite_frame,
    text="<",
    width=1,
    command=lambda d=custom_dropdown:
        cycle_dropdown(d, -1)
)

custom_next_button = tk.Button(
    custom_suite_frame,
    text=">",
    width=1,
    command=lambda d=custom_dropdown:
        cycle_dropdown(d, 1)
)

def load_custom_suite():
    suite_name = custom_dropdown.get()

    if not suite_name:
        messagebox.showwarning(
            "Warning",
            "There are no custom SUITES to load."
        )
        return

    answer = messagebox.askyesno(
        "Confirm Settings",
        "This will OVERWRITE all current customizations with those of this SUITE.\nContinue?"
    )

    if not answer:
        return

    global PLAYER_SELECTIONS

    saved_suites = read_saved_selections()

    if suite_name not in saved_suites:
        messagebox.showerror(
            "Error",
            "This SUITE no longer exists. Refreshing the list."
        )
        refresh_saved_selection_names()
        return

    PLAYER_SELECTIONS = copy.deepcopy(saved_suites[suite_name])
    batch_update_page2_dropdowns()

custom_set = tk.Button(
    custom_suite_frame,
    text="Use this SUITE",
    command=load_custom_suite
)

custom_previous_button.pack(side="left")
custom_dropdown.pack(side="left", padx=2)
custom_next_button.pack(side="left")
custom_set.pack(side="left", padx=10)

tk.Label(
    page3_container,
    text="No preview available",
    anchor="w"
).pack(anchor="w", pady=(5, 0))

refresh_saved_selection_names()


# --- THE NEFARIOUS RANDOMIZER
random_suite_frame = tk.Frame(page3_container)
random_suite_frame.pack(fill="x", padx=10, pady=(5, 8))

tk.Label(
    random_suite_frame,
    text='THE NEFARIOUS RANDOMIZER',
    font=("Arial", 11, "bold")
).pack(anchor="w",pady=(0,5))

def load_random_suite():

    answer = messagebox.askyesno(
        "Confirm Settings",
        "This will OVERWRITE all current customizations with those of this SUITE.\nContinue?"
    )

    if not answer:
        return

    randomize_page2_dropdowns()

random_set = tk.Button(
    random_suite_frame,
    text="Generate and Use a RANDOM SUITE",
    command=load_random_suite
)

random_set.pack(side="left", padx=10)

tk.Label(
    page3_container,
    text="No preview available",
    anchor="w"
).pack(anchor="w", pady=(5, 15))


root.mainloop()