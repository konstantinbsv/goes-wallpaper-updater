# requests is used to download web page
import requests
# for time zone conversion
from datetime import datetime, tzinfo
import pytz
import time
# for directories
import os
# use BeautifulSoup to parse page
from bs4 import BeautifulSoup
# regex for extracting date and time from image name
import re
# for setting wallpaper and getting screen resolution
import ctypes
# for cropping image and watermarking
from PIL import Image, ImageDraw, ImageFont

# url to directory with full disk, false colour images
URL = 'http://192.168.1.109/GOES_IMAGES/goes17/fd/fc/'
# regex for extracting time and date
TS_REGEX = r'_(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})'
# from timezone list from: https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568
HOME_TIMEZONE = pytz.timezone('America/Vancouver')
UTC_TIMEZONE = pytz.timezone('UTC')
# format of time and date, e.g.: '%Y-%m-%d %H:%M'
TIME_FORMAT = '%H:%M'
# set wallpaper SPI, more: https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-systemparametersinfow
SPI_SETDESKWALLPAPER = 0x0014
# path to newest full size image
IMG_PATH = os.getcwd() + os.path.sep + 'newest_image.jpg'
# path to newest cropped image (absolute path must be used with ctypes)
CROPPED_IMG_PATH = os.getcwd() + os.path.sep + 'newest_cropped_image.jpg'
# watermark definitions
FONT = ImageFont.truetype(font="arialbd.ttf", size=50)
FONT_FILL = (75, 75, 75)
# monitor width and height. Used to calculate aspect ratio and crop image
WIDTH = ctypes.windll.user32.GetSystemMetrics(0)
HEIGHT = ctypes.windll.user32.GetSystemMetrics(1)


def save_image(url):
    img_data = requests.get(url).content
    with open('newest_image.jpg', 'wb') as handler:
        handler.write(img_data)


def get_timestamp(filename):
    img_ts = re.search(TS_REGEX, filename)
    utc_time = datetime(
        int(img_ts[1]), int(img_ts[2]), int(img_ts[3]),
        int(img_ts[4]), int(img_ts[5]), int(img_ts[6]))
    localized_utc_timestamp = UTC_TIMEZONE.localize(utc_time)
    localized_home_timestamp = localized_utc_timestamp.astimezone(HOME_TIMEZONE)
    return localized_home_timestamp.strftime(TIME_FORMAT)


def create_info_file(image_name):
    local_time = datetime.now().strftime('%H:%M:%S')
    with open('info.txt', 'w') as handler:
        handler.write('Downloaded: ' + image_name + " at local time: " + local_time)


def watermark_image(image_path, watermark_string):
    img = Image.open(image_path)
    drawing = ImageDraw.Draw(img)  # make drawable
    drawing.text((img.width - 155, 2830), watermark_string, fill=FONT_FILL, font=FONT)
    img.save(CROPPED_IMG_PATH, quality=100)


def set_wallpaper():
    ctypes.windll.user32.SystemParametersInfoW(
        SPI_SETDESKWALLPAPER,
        0,
        CROPPED_IMG_PATH,
        3)


def create_cropped_image():
    full_img = Image.open(IMG_PATH)
    crop_area = (0, 0, full_img.width, full_img.height * (HEIGHT / WIDTH))
    cropped_img = full_img.crop(crop_area)
    cropped_img.save(CROPPED_IMG_PATH, quality=100)


# set this process to be DPI aware for proper scaling of wallpaper
ctypes.windll.shcore.SetProcessDpiAwareness(2)

# get newest folder
response = requests.get(URL)
soup = BeautifulSoup(response.text, 'lxml')
# newestFolder = soup.find_all('a', href=True)[5]
newestFolder = soup.find('a', href=re.compile(r'^\d+'))

# get newest image
directoryURL = URL + newestFolder['href']
response = requests.get(directoryURL)
soup = BeautifulSoup(response.text, 'lxml')
# newestImage = soup.find_all('a', href=True)[5]
newestImage = soup.find('a', href=re.compile(r'GOES17'))

# save timestamp info and download newest image
imageURL = directoryURL + newestImage['href']
print(newestImage.text)
save_image(imageURL)
create_info_file(newestImage.text)

# crop image and set wallpaper
create_cropped_image()
watermark_image(CROPPED_IMG_PATH, get_timestamp(newestImage.text))
set_wallpaper()
