# izone-tkinter-new

note: DO NOT SHARE WITH ANYONE ELSE OTHER THAN 6 OF US, even if they are your good friends, please dont share this
disclaimer: due to lack of testing data, this code may or may not work, please prepare for manual slot selection in case of an error occured

setup steps:
1. download zip file and open with vs code
2. enter the command `pip install -r requirements.txt` to install all dependencies
3. In `store_pw.py`, replace `your_username_here` and `your_password_here` with your izone credentials and run the code once.
4. If you wish to delete your credentials when you no longer need it, you can simply uncomment the code under `Remove Credentials` and run it once. (Just make sure the credentials are still there when you need to execute the program with `testing=False`)
5. open `main.py` and only modify the my_subjects list (if necessary) and there is no need to modify anything else. enter the subjects' names in lowercase to reduce time wasted for computer to convert the case. Note it is not required to enter the entire name, you can just enter a subpart of the name, as long as the substring is unique among all subjects. (Example 'information systems analysis & design' can be written as 'information systems' since it is the only information systems subject)
6. Currently the `testing` variable is set to `True` for testing the code. It needs to be changed to `False` during the actual scraping and selection.
7. 

execute program steps
1. run `main.py`
2. 2 windows will pop up, which are 'Class Schedule Viewer' and an empty Google Chrome window.
3. Ignore the 'Group 1: Information Systems' slot, that is just a placeholder (The code will break without it)
4. Adjust the 2 windows to your desired size (Take note the last time slot is 1830-1900, if the window width is too small, it will hide some slots)
5. Click the `Refresh Slots` button for the scraper to scrape the time slots either from the testing HTML or from the actual website
6. Then, switch between different combinations of time slots, you may also apply filters for your desired slots.
7. If you wish to select that particular slot, click `Select Slot`
8. If the slots you wish to select is full, don't worry, just click `Refresh Slots` again for the updated choices.
9. To exit the program, simply close the `Class Schedule Viewer` window

# In case of an error occured during selection, you can select the slots manually directly from the chrome driver window, no need to log in again.
