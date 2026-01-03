import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from PIL import Image
import PySimpleGUI as sg
import schedule
import time
import json
from datetime import datetime

DATA_FILE = 'image_data.json'

def scrape_website(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    images = soup.find_all('img')
    image_urls = []
    for img in images:
        src = img.get('src')
        if src and not src.startswith('data:'):
            parsed_url = urlparse(url)
            if not src.startswith('http'):
                src = f"{parsed_url.scheme}://{parsed_url.netloc}/{src.lstrip('/')}"
            image_urls.append(src)
    return image_urls

def download_image(url, convert_to_bw=False):
    response = requests.get(url)
    filename = url.split('/')[-1]
    with open(filename, 'wb') as f:
        f.write(response.content)
    if convert_to_bw:
        image = Image.open(filename).convert('L')
        image.save(filename)
    return filename

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    else:
        return []

def perform_scrape(url, convert_to_bw=False):
    image_urls = scrape_website(url)
    data = []
    for image_url in image_urls:
        filename = download_image(image_url, convert_to_bw)
        data.append(filename)
    save_data(data)

# Create GUI layouts for each tool
scraping_layout = [
    [sg.Text('Website URL:'), sg.Input(key='-URL-')],
    [sg.Button('Scrape Website')],
    [sg.Listbox([], size=(80, 10), key='-IMAGES-', enable_events=True)],
    [sg.Image(key='-IMAGE-')],
    [sg.Checkbox('Convert to Black and White', key='-BW-')]
]

date_layout = [
    [sg.Text(size=(20, 1), key='-DATE-', justification='center')]
]

conversion_layout = [
    [sg.Text('Select an image to convert:')],
    [sg.Listbox([], size=(80, 10), key='-CONVERT_IMAGES-', enable_events=True)],
    [sg.Image(key='-CONVERTED_IMAGE-')]
]

# Create the main layout with a Tab element
main_layout = [
    [sg.TabGroup([
        [
            sg.Tab('Scraping', scraping_layout),
            sg.Tab('Date', date_layout),
            sg.Tab('Image Conversion', conversion_layout)
        ]
    ])]
]

# Create the window
window = sg.Window('Website Image Scraper', main_layout)

# Load existing data
existing_data = load_data()

# Event loop
while True:
    event, values = window.read()
    if event == sg.WINDOW_CLOSED:
        break
    if event == 'Scrape Website':
        url = values['-URL-']
        image_urls = scrape_website(url)
        window['-IMAGES-'].update(image_urls)
    if event == '-IMAGES-' and values['-IMAGES-']:
        image_url = values['-IMAGES-'][0]
        convert_to_bw = values['-BW-']
        filename = download_image(image_url, convert_to_bw)
        window['-IMAGE-'].update(filename)

    if event == '-CONVERT_IMAGES-' and values['-CONVERT_IMAGES-']:
        image_url = values['-CONVERT_IMAGES-'][0]
        filename = download_image(image_url, convert_to_bw=True)
        window['-CONVERTED_IMAGE-'].update(filename)

    # Update the date in the GUI
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    window['-DATE-'].update(current_date)

    # Schedule the scrape to occur once per hour
    schedule.every().hour.do(perform_scrape, values['-URL-'], values['-BW-'])
    schedule.run_pending()
    time.sleep(1)

# Save data before closing the window
save_data(existing_data)

window.close()

