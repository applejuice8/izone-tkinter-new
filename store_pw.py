import keyring

# Set credentials
keyring.set_password('izone', 'username', '')
keyring.set_password('izone', 'password', '')

# Get credentials
# username = keyring.get_password('izone', 'username')
# password = keyring.get_password('izone', 'password')