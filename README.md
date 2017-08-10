# Asus Wifimanager
I have slow internet so this app allows me to easily see whos connected and taking up too much bandwidth.
Supports kicking all clients except for devices with permission of parent.
Users are already connected to the app by default.

# Setup
- clone repo
- cd into repo
- create virtual env and activate
- <code>> pip install -r requirements.txt</code>
- config details
    - set db connection data in django settings
    - set env variables for asus login credentials: ASUS_API_USERNAME, ASUS_API_PASSWORD
- get django running
    - <code>> python manage.py makemigrations</code>
    - <code>> python manage.py migrate</code>
    - <code>> python manage.py create superuser</code>
    - <code>> python manage.py runserver 0:8000</code>
- run the connection collector script
    - <code>> cd scripts</code>
    - <code>> python collect_connection_samples</code>
