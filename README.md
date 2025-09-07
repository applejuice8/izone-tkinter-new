# izone-tkinter-new

⚠️ **Note:** DO NOT SHARE this project with anyone outside our group of 6. Even if they are your good friends, please keep it private. 😡

⚠️ **Disclaimer:** Due to limited testing data, this code may or may not work perfectly. Please be prepared to do **manual slot selection** in case any errors occur. 🫠

---

## Setup Steps

1. Download the zip file and open it with VS Code.
2. Run:
   ```bash
   pip install -r requirements.txt
   ```
   to install all dependencies.
3. In `store_pw.py`, replace:
   ```python
   keyring.set_password('izone', 'username', 'your_username_here')
   keyring.set_password('izone', 'password', 'your_password_here')
   ```
   with your **izone** credentials and run the code **once**.
4. If you want to delete your credentials later, uncomment the code under **Remove Credentials** in `store_pw.py` and run it once.  
   👉 Just don’t delete them if you still need to run the program with `testing=False`.
5. Open `main.py` and only modify the `my_subjects` list (if needed).  
   - Use lowercase subject names to save processing time.  
   - You don’t need to write the full name, just a unique substring is enough.  
     Example: `'information systems analysis & design'` → `'information systems'` (since it’s the only one with that substring).
6. The `testing` variable is set to `True` by default. Change it to `False` when doing the actual scraping and selection.

---

## Running the Program

1. Run `main.py`.
2. Two windows will appear:  
   - **Class Schedule Viewer** (Tkinter UI)  
   - An **empty Google Chrome** window
3. Ignore the slot `Group 1: Information Systems` → that’s just a placeholder (program won’t work without it).
4. Adjust the window sizes.  
   - The last slot is `1830–1900`.  
   - If your window width is too small, some slots may be hidden.
5. Click **Refresh Slots** to scrape the time slots (from test HTML if `testing=True`, or from izone if `testing=False`).
6. Switch between different slot combinations. You can also apply filters.
7. If you want to select a slot, click **Select Slot**.
8. If your chosen slot is full, don’t panic → just click **Refresh Slots** again to see updated choices.
9. To exit, just close the **Class Schedule Viewer** window.

---

## Manual Backup Plan

If the program throws an error during selection:  
👉 You can still select the slots **manually** directly in the Chrome driver window. No need to log in again. (Though this may fail too 🫠)
