# Stock Watch Ticker App

A Wall St. inspired ticker display board, right on your desktop. Color coded, live prices, and percentage changes using Yahoo Finance data.

## Features

- Color coded price changes (green for gains, red for losses)
- Scrolls across the bottom of your screen
- Updates prices every 30 seconds
- Settings button to manage ticker list

## Requirements

- Python 3.x
- `tkinter`
- `yfinance`

## Startup on Computer Start (WindowsOS only)

1. Copy absolute file path to ```main.py```
2. Create a new shortcut on desktop
3. Find Python interpreter file location
4. Format as "C:\Path\To\Python\python.exe" "C:\Path\To\Your\Project\main.py", and save it to the shortcut
5. ⊞ Win + R
6. Type "shell:startup"
7. Copy that shortcut or drag it into the startup folder

## Personalization

1. To change ticker colors, edit the *color_map* dictionary before the class in ```main.py```
2. To change the scroll speed, locate the class *StockTickerApp* in ```main.py``` and on line 16, change the float in **self.scroll_speed**.
