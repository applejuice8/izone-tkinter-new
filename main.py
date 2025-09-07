from collections import defaultdict
from itertools import product
import tkinter as tk
import pandas as pd
from pathlib import Path
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium import webdriver

# Can Modify
# --------------------------------------------------------
my_subjects = [
    'web fundamentals',
    'operating system fundamentals',
    'information systems analysis & design'
]
# --------------------------------------------------------


# Set up driver
headless = False
def init_driver(headless):
    print('Setting up webdriver...')

    options = Options()
    if headless:
        options.add_argument('--headless')

    # Use Service with WebDriver Manager
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)
driver = init_driver(headless=headless)

# Get the directory where choose_timetable.py is located
script_dir = Path(__file__).resolve().parent

# Modify the CSV loading section to use the correct path
try:
    csv_path = script_dir / "scraped_files" / "slots.csv"
    df = pd.read_csv(csv_path)
    df["subject"] = df["Subject"].apply(lambda x: x.split(" - ")[1])
    df["Time"] = df["Start Time"].str.strip() + " - " + df["End Time"].str.strip()
except FileNotFoundError:
    # Create empty DataFrame with required columns if file doesn't exist
    df = pd.DataFrame(columns=["Subject", "Class Type", "Group Number", "Teacher", "Day", "Time"])
    df["subject"] = ""

# Split lectures, practicals, and workshops
lectures = df[df["Class Type"] == "Lecture"]
practicals = df[df["Class Type"] == "Practical"]
workshops = df[df["Class Type"] == "Workshop"]

lecture_groups = lectures.groupby("subject")
practical_groups = practicals.groupby("subject")
workshop_groups = workshops.groupby("subject")

# Create subject-wise triplets (lecture, practical, workshop)
subject_combinations = {}
for subject in lectures["subject"].unique():
    lec = lecture_groups.get_group(subject).to_dict("records") if subject in lecture_groups.groups else [{}]
    prac = practical_groups.get_group(subject).to_dict("records") if subject in practical_groups.groups else [{}]
    work = workshop_groups.get_group(subject).to_dict("records") if subject in workshop_groups.groups else [{}]
    subject_combinations[subject] = list(product(lec, prac, work))

# Assign fixed colors to subjects
subject_colors = {}
fixed_colors = ["#990012", "#6A0DAD", "#0020C2", "#3A5F0B", "#873600"]
#                  Red,      Purple,     Blue,     Green 

for i, subject in enumerate(df["subject"].unique()):
    subject_colors[subject] = fixed_colors[i % len(fixed_colors)]

# Helper functions
def time_to_tuple(cls):
    h1, m1 = map(int, cls["Start Time"].split(":"))
    h2, m2 = map(int, cls["End Time"].split(":"))
    return h1 * 60 + m1, h2 * 60 + m2

def has_overlap(classes):
    schedule = defaultdict(list)
    for cls in classes:
        if not cls: continue
        day = cls["Day"]
        start, end = time_to_tuple(cls)
        for s, e in schedule[day]:
            if start < e and end > s:
                return True
        schedule[day].append((start, end))
    return False

def score_schedule(classes):
    daily = defaultdict(list)
    for cls in classes:
        if not cls: continue
        daily[cls["Day"]].append(time_to_tuple(cls))

    total_gap = 0
    single_days = 0
    school_days = 0
    long_gap_penalty = 0

    for times in daily.values():
        times.sort()
        if len(times) == 1:
            single_days += 1
        school_days += 1
        gaps = [times[i+1][0] - times[i][1] for i in range(len(times)-1)]
        total_gap += sum(gaps)
        long_gap_penalty += sum(1 for g in gaps if g >= 240) * 100

    days_off_bonus = (5 - school_days) * 20
    return total_gap + (40 * single_days) + long_gap_penalty - days_off_bonus

def filter_schedules(schedules, f1, f2, f3, f4, f5, f6):
    def count_school_days(classes):
        return len(set(cls["Day"] for cls in classes if cls))

    def has_large_gap(classes):
        daily = defaultdict(list)
        for cls in classes:
            if not cls: continue
            daily[cls["Day"]].append(time_to_tuple(cls))
        for times in daily.values():
            times.sort()
            for i in range(len(times) - 1):
                if times[i+1][0] - times[i][1] >= 240:
                    return True
        return False

    def count_large_gap_days(classes):
        daily = defaultdict(list)
        for cls in classes:
            if not cls: continue
            daily[cls["Day"]].append(time_to_tuple(cls))
        count = 0
        for times in daily.values():
            times.sort()
            for i in range(len(times) - 1):
                if times[i+1][0] - times[i][1] >= 240:
                    count += 1
                    break
        return count

    def has_single_class_day(classes):
        daily = defaultdict(list)
        for cls in classes:
            if not cls: continue
            daily[cls["Day"]].append(cls)
        return any(len(day) == 1 for day in daily.values())

    filtered = []
    for score, combo in schedules:
        days = count_school_days(combo)
        if f1 and days != 4:
            continue
        if f2 and days != 3:
            continue
        if f3 and days != 2:
            continue
        if f4 and has_large_gap(combo):
            continue
        if f5 and count_large_gap_days(combo) > 1:
            continue
        if f6 and has_single_class_day(combo):
            continue
        filtered.append((score, combo))
    return filtered

def get_earliest_time(combos):
    earliest = float('inf')
    for _, combo in combos:
        for cls in combo:
            if not cls: continue
            start, _ = time_to_tuple(cls)
            earliest = min(earliest, start)
    return earliest

def build_dynamic_slots(valid_schedules, earliest_start):
    # Find latest ending time across all schedules
    latest_end = 0
    for _, combo in valid_schedules:
        for cls in combo:
            if not cls:
                continue
            _, end = time_to_tuple(cls)
            latest_end = max(latest_end, end)

    # Build full range of 30-min slots
    return list(range(earliest_start, latest_end + 30, 30))


# GUI
class TimetableGUI:
    def __init__(self, master, combos):
        self.master = master
        master.title("Class Schedule Viewer")
        master.configure(bg="black")
        master.geometry("1200x800")

        self.main_frame = tk.Frame(master, bg="black")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.label = tk.Label(self.main_frame, text="", bg="black", fg="white", font=("Helvetica", 20))
        self.label.pack()

        # Add refresh button at the top
        self.refresh_button = tk.Button(self.main_frame, text="Refresh Slots", command=self.refresh_slots,
                                      width=12, font=("Helvetica", 18), bg="#444444", fg="black")
        self.refresh_button.pack(pady=(0, 10))

        self.canvas_border = tk.Frame(self.main_frame, bg="white", bd=2, relief=tk.SOLID)
        self.canvas_border.pack()
        self.canvas = tk.Canvas(self.canvas_border, bg="black", highlightthickness=0)
        self.canvas.pack(padx=1, pady=1)

        self.filter_frame = tk.Frame(self.main_frame, bg="black")
        self.filter_frame.pack()

        self.var_f1 = tk.BooleanVar()
        self.var_f2 = tk.BooleanVar()
        self.var_f3 = tk.BooleanVar()
        self.var_f4 = tk.BooleanVar()
        self.var_f5 = tk.BooleanVar()
        self.var_f6 = tk.BooleanVar()

        for i, (text, var) in enumerate([
            ("1 day off", self.var_f1), ("2 days off", self.var_f2), ("3 days off", self.var_f3),
            ("No ≥4h gaps", self.var_f4), ("≤1 day ≥4h gap", self.var_f5), ("No 1-class days", self.var_f6)
        ]):
            tk.Checkbutton(self.filter_frame, text=text, variable=var, bg="black", fg="white",
                           font=("Helvetica", 15), command=self.apply_filters).grid(row=i//3, column=i%3, sticky="w", padx=20, pady=2)

        self.nav_frame = tk.Frame(self.main_frame, bg="black")
        self.nav_frame.pack(pady=(0, 25))

        self.prev_button = tk.Button(self.nav_frame, text="Previous", command=self.show_prev, width=12, font=("Helvetica", 18))
        self.prev_button.pack(side=tk.LEFT, padx=10)

        self.next_button = tk.Button(self.nav_frame, text="Next", command=self.show_next, width=12, font=("Helvetica", 18))
        self.next_button.pack(side=tk.RIGHT, padx=10)

        self.select_slot_button = tk.Button(self.nav_frame, text="Select Slot", command=self.run_select_slot, 
                                          width=12, font=("Helvetica", 18))
        self.select_slot_button.pack(side=tk.RIGHT, padx=10)

        self.summary_container = tk.Frame(self.main_frame, bg="white", bd=2, relief=tk.SOLID)
        self.summary_container.pack(pady=(0, 0), fill=tk.BOTH, expand=True)

        # === Scrollable summary frame ===
        self.summary_canvas = tk.Canvas(self.summary_container, bg="black", highlightthickness=0)
        self.summary_scrollbar = tk.Scrollbar(self.summary_container, orient="vertical", command=self.summary_canvas.yview)
        self.summary_scrollbar.pack(side="right", fill="y")
        self.summary_canvas.pack(side="left", fill="both", expand=True)
        self.summary_canvas.configure(yscrollcommand=self.summary_scrollbar.set)

        self.summary_frame = tk.Frame(self.summary_canvas, bg="black")
        self.summary_window = self.summary_canvas.create_window((0, 0), window=self.summary_frame, anchor="nw")

        self.summary_frame.bind("<Configure>", lambda e: self.summary_canvas.configure(scrollregion=self.summary_canvas.bbox("all")))

        self.summary_canvas.bind("<Configure>", lambda e: self.summary_canvas.itemconfig(self.summary_window, width=e.width))
        # === End scrollable section ===

        self.all_combos = combos
        self.filtered_combos = combos
        self.index = 0
        earliest_start = get_earliest_time(valid_schedules)
        self.time_slots = build_dynamic_slots(combos, earliest_start)
        self.earliest_start = earliest_start
        self.days = ["MON", "TUE", "WED", "THU", "FRI"]
        self.show_schedule()

    def run_select_slot(self):
        if not self.filtered_combos:
            return

        popup, label = self.show_popup("Selecting slots...")

        def log(msg):
            if label.winfo_exists():
                label.config(text=label.cget("text") + "\n" + msg)
                self.master.update()

        try:
            combo = self.filtered_combos[self.index][1]
            subjects, l_groups, p_groups, w_groups = [], [], [], []

            subject_set = set(cls["subject"] for cls in combo if cls)
            for subject in subject_set:
                l_group = p_group = w_group = ''
                for cls in combo:
                    if not cls or cls["subject"] != subject:
                        continue
                    if cls["Class Type"] == "Lecture":
                        l_group = cls["Group Number"]
                    elif cls["Class Type"] == "Practical":
                        p_group = cls["Group Number"]
                    elif cls["Class Type"] == "Workshop":
                        w_group = cls["Group Number"]
                subjects.append(subject.lower())
                l_groups.append(f' {l_group.split(' ')[-1]} ')
                p_groups.append(f' {p_group.split(' ')[-1]} ')
                w_groups.append(f' {w_group.split(' ')[-1]} ')

            # Patch the print to call log
            import builtins
            original_print = builtins.print

            def patched_print(*args, **kwargs):
                msg = " ".join(str(a) for a in args)
                log(msg)

            builtins.print = patched_print

            try:
                # from select_slot import select_slot
                from slot_selector import select_slot
                select_slot(driver=driver, testing=True, headless=False,
                            subjects=subjects, l_groups=l_groups,
                            p_groups=p_groups, w_groups=w_groups)
                log("Done!")
                popup.after(2000, popup.destroy)
            finally:
                builtins.print = original_print

        except Exception as e:
            log(f"[ERROR] {e}")
            popup.after(4000, popup.destroy)

    def apply_filters(self):
        self.filtered_combos = filter_schedules(
            self.all_combos,
            self.var_f1.get(), self.var_f2.get(), self.var_f3.get(),
            self.var_f4.get(), self.var_f5.get(), self.var_f6.get()
        )
        self.index = 0
        self.show_schedule()

    def show_prev(self):
        if self.index > 0:
            self.index -= 1
            self.show_schedule()

    def show_next(self):
        if self.index < len(self.filtered_combos) - 1:
            self.index += 1
            self.show_schedule()
    
    def show_popup(self, message, width=600, height=450, font_size=20):
        popup = tk.Toplevel(self.master)
        popup.title("Status")
        popup.geometry(f"{width}x{height}")
        popup.configure(bg="black")

        label = tk.Label(
            popup,
            text=message,
            fg="white",
            bg="black",
            font=("Helvetica", font_size),
            justify="left",
            anchor="nw"
        )
        label.pack(expand=True, fill="both", padx=20, pady=20)
        
        self.master.update()
        return popup, label

    def refresh_slots(self):
        popup, label = self.show_popup("Refreshing slots...")

        def log(msg):
            if label.winfo_exists():
                label.config(text=label.cget("text") + "\n" + msg)
                self.master.update()

        import builtins
        original_print = builtins.print

        def patched_print(*args, **kwargs):
            msg = " ".join(str(a) for a in args)
            log(msg)

        # Print on GUI instead of terminal
        builtins.print = patched_print

        try:
            # from scrape_slots import scrape_slots
            # scrape_slots(testing=True, headless=True)
            from slot_scraper import start_scrape
            start_scrape(testing=True, driver=driver, headless=True, my_subjects=my_subjects)

            # Reload and reprocess the data
            global df, lectures, practicals, workshops, practical_groups, workshop_groups, subject_combinations
            global all_combos, valid_schedules

            csv_path = script_dir / "scraped_files" / "slots.csv"
            df = pd.read_csv(csv_path)
            df["subject"] = df["Subject"].apply(lambda x: x.split(" - ")[1])

            # Re-assign subject colors
            subject_colors.clear()
            for i, subject in enumerate(df["subject"].unique()):
                subject_colors[subject] = fixed_colors[i % len(fixed_colors)]

            # Re-process the data
            lectures = df[df["Class Type"] == "Lecture"]
            practicals = df[df["Class Type"] == "Practical"]
            workshops = df[df["Class Type"] == "Workshop"]

            practical_groups = practicals.groupby("subject")
            workshop_groups = workshops.groupby("subject")

            # Regenerate subject combinations
            subject_combinations = {}
            for subject in lectures["subject"].unique():
                lec = lectures[lectures["subject"] == subject].to_dict("records")
                prac = practical_groups.get_group(subject).to_dict("records") if subject in practical_groups.groups else [{}]
                work = workshop_groups.get_group(subject).to_dict("records") if subject in workshop_groups.groups else [{}]
                subject_combinations[subject] = list(product(lec, prac, work))

            # Regenerate all valid schedules
            all_combos = list(product(*subject_combinations.values()))
            valid_schedules = []
            for combo in all_combos:
                flat = [c for triple in combo for c in triple if c]
                if not has_overlap(flat):
                    score = score_schedule(flat)
                    valid_schedules.append((score, flat))

            valid_schedules.sort(key=lambda x: x[0])

            # Update GUI
            self.all_combos = valid_schedules
            self.filtered_combos = valid_schedules
            self.index = 0
            self.earliest_start = get_earliest_time(valid_schedules)
            self.time_slots = build_dynamic_slots(valid_schedules, self.earliest_start)
            self.show_schedule()

            log("Done!")
            popup.after(2000, popup.destroy)

        except Exception as e:
            log(f"[ERROR] {e}")
            popup.after(4000, popup.destroy)

        finally:
            builtins.print = original_print

    def show_schedule(self):
        self.canvas.delete("all")
        for widget in self.summary_frame.winfo_children():
            widget.destroy()

        slot_width = 60
        row_height = 60
        day_col_width = 80

        if not self.filtered_combos:
            self.label.config(text="No matching schedules.")
            return

        combo = self.filtered_combos[self.index][1]
        self.label.config(text=f"Schedule {self.index + 1} of {len(self.filtered_combos)} (Score: {self.filtered_combos[self.index][0]})")

        total_width = day_col_width + len(self.time_slots) * slot_width
        total_height = (len(self.days) + 1) * row_height
        self.canvas.config(width=total_width, height=total_height)

        for i, t in enumerate(self.time_slots):
            x0 = day_col_width + i * slot_width
            start_time = f"{t//60:02d}:{t%60:02d}"
            end_time   = f"{(t+30)//60:02d}:{(t+30)%60:02d}"
            self.canvas.create_rectangle(x0, 0, x0 + slot_width, row_height, fill="#444444", outline="white")
            self.canvas.create_text(x0 + slot_width//2, row_height//2 - 10, text=start_time, fill="white", font=("Helvetica", 18))
            self.canvas.create_text(x0 + slot_width//2, row_height//2 + 10, text=end_time, fill="white", font=("Helvetica", 18))

        for r, day in enumerate(self.days):
            y0 = (r+1) * row_height
            self.canvas.create_rectangle(0, y0, day_col_width, y0 + row_height, fill="#333333", outline="white")
            self.canvas.create_text(day_col_width//2, y0 + row_height//2, text=day, fill="white", font=("Helvetica", 20, "bold"))
            for i in range(len(self.time_slots)):
                x0 = day_col_width + i * slot_width
                self.canvas.create_rectangle(x0, y0, x0 + slot_width, y0 + row_height, fill="#222222", outline="gray")

        for cls in combo:
            if not cls: continue
            day_idx = self.days.index(cls["Day"])
            start_min, end_min = time_to_tuple(cls)
            start_slot = next(i for i, t in enumerate(self.time_slots) if t == start_min)
            col_span = max(1, (end_min - start_min) // 30)
            x0 = day_col_width + start_slot * slot_width
            y0 = (day_idx + 1) * row_height
            x1 = x0 + col_span * slot_width
            y1 = y0 + row_height
            color = subject_colors.get(cls["subject"], "#666666")
            self.canvas.create_rectangle(x0+2, y0+2, x1-2, y1-2, fill=color, outline="white")
            suffix = "(L)" if cls["Class Type"] == "Lecture" else "(P)" if cls["Class Type"] == "Practical" else "(W)"
            self.canvas.create_text((x0+x1)//2, (y0+y1)//2, 
                                    text=f"{cls['Group Number']} {suffix}\n{cls['subject'][:30]}", 
                                    fill="white", font=("Helvetica", 15), justify="center")

        subject_groups = defaultdict(dict)
        for cls in combo:
            if cls:
                subject_groups[cls["subject"]][cls["Class Type"]] = cls

        for subject, types in subject_groups.items():
            color = subject_colors.get(subject, "#222222")
            header = tk.Label(self.summary_frame, text=subject, fg="white", bg=color,
                            font=("Helvetica", 20, "bold"), padx=5, pady=2)
            header.pack(anchor="center", padx=50, pady=(5,0))

            for typ in ["Lecture", "Practical", "Workshop"]:
                if typ in types:
                    cls = types[typ]
                    suffix = "(L)" if cls["Class Type"] == "Lecture" else "(P)" if cls["Class Type"] == "Practical" else "(W)"
                    text = f"{cls['Group Number']} {suffix}"
                    label = tk.Label(self.summary_frame, text=text, fg="white", bg="black",
                                    font=("Helvetica", 18), padx=10)
                    label.pack(anchor="center")

# Generate all valid schedules
all_combos = list(product(*subject_combinations.values()))
valid_schedules = []
for combo in all_combos:
    flat = [c for triple in combo for c in triple if c]
    if not has_overlap(flat):
        score = score_schedule(flat)
        valid_schedules.append((score, flat))

valid_schedules.sort(key=lambda x: x[0])

if __name__ == "__main__":
    root = tk.Tk()
    gui = TimetableGUI(root, valid_schedules)
    root.mainloop()
