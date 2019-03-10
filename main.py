i = 0
import termios, fcntl, sys, os
selected_word = None
sys.path.append("../Shared")
selected_sentence = None
from tinysegmenter import TinySegmenter
isRunning = True
# filename = 'MurderOnTheOrientExpress.srt'
filename = 'OnePunchMan12.srt'
# while isRunning:
    # print(str(i/1024)+'KB / KB downloaded!', end='\r')
sub_array = {}
current_line = ''
ignore_next = False
ts = TinySegmenter()
import pickle

with open(filename, 'r') as _sub_file:
    for line in _sub_file:
        if '-->' in line:
            current_line = line[:8].replace(':', '')
            sub_array[current_line] = { 'end_time': line[-13: -5].replace(':', ''), 'description': ''}
            ignore_next = False
        elif line != '' and current_line != '' and ignore_next == False:
            sub_array[current_line]['description'] += line.strip()
        ignore_next = not bool(line.strip())
max_time = sub_array[max(sub_array, key=lambda k: int(sub_array[k]['end_time']))]['end_time']


def key_to_seconds(key):
    return int(key[0:2]) * 60 * 60 + int(key[2:4]) * 60 + int(key[4:])
max_time_seconds = key_to_seconds(max_time)
import math
import time

from selenium import webdriver
browser = webdriver.Chrome()
def quit_program():
    global isRunning
    print('Closing...')
    browser.quit()
    isRunning = False

cookie_path = '/tmp/cookie'
def save_cookie():
    with open(cookie_path, 'wb') as filehandler:
        pickle.dump(browser.get_cookies(), filehandler)

def load_cookie():
    global browser
    if os.path.exists(cookie_path):
        with open(cookie_path, 'rb') as cookiesfile:
            cookies = pickle.load(cookiesfile)
            for cookie in cookies:
                browser.add_cookie(cookie)

print('Please input a url:')
url = input()
browser.get(url)
is_paused = False
load_cookie()
browser.get(url)
pause_time = 0

fd = sys.stdin.fileno()
oldterm = termios.tcgetattr(fd)
newattr = termios.tcgetattr(fd)
newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
termios.tcsetattr(fd, termios.TCSANOW, newattr)
oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)

def pause_program():
    global is_paused, translation, selected_word, selected_sentence, pause_time, start_time
    is_paused = not is_paused
    if not is_paused:
        translation = None
        start_time = time.time() - pause_time
        selected_word = selected_sentence = None
        browser.execute_script('document.getElementsByTagName("video")[0].play();')
    else:
        selected_word = 0
        selected_sentence = ts.tokenize(sentence)
        get_translation()
        browser.execute_script('document.getElementsByTagName("video")[0].pause();')

    pause_time = t

from search import search, Results
translation = None
def get_translation():
    global translation
    if len(selected_sentence) > selected_word:
        translation = search(selected_sentence[selected_word])

def next_word():

    global selected_word
    if selected_word is not None:
        if selected_word < len(selected_sentence) - 1:
            selected_word += 1
            while not selected_sentence[selected_word].strip():
                selected_word += 1
            get_translation()

def prev_word():
    global selected_word
    if selected_word is not None:
        if selected_word > 0:
            selected_word -= 1
            while not selected_sentence[selected_word].strip():
                selected_word -= 1
            get_translation()

def sync_time():
    global start_time
    browser_time = None
    while True:
        try:
            browser_time = browser.execute_script('return document.getElementsByTagName("video")[0].currentTime;')
        except: 
            browser_time = None
        if browser_time is None:
            time.sleep(1)
        else:
            break
    start_time = time.time() - browser_time

def jump_next_sentence():
    global start_time, sentence, time_key, pause_time, selected_word, selected_sentence
    old_time_key = get_time_key()
    time_key_arr = [k for k in sub_array if k > old_time_key]
    if len(time_key_arr) > 0 and is_paused:
        time_key = time_key_arr[0]
        pause_time = key_to_seconds(time_key)
        start_time = time.time() - pause_time
        selected_word = 0
        sentence = get_sentence_at_time(time_key)
        selected_sentence = ts.tokenize(sentence)
        get_translation()

def jump_prev_sentence():
    global start_time, sentence, time_key, paused_time, selected_word, selected_sentence
    old_time_key = get_time_key()
    time_key_arr = [k for k in sub_array if k < old_time_key]
    if len(time_key_arr) > 0 and is_paused:
        time_key = time_key_arr[-1]
        pause_time = key_to_seconds(time_key)
        start_time = time.time() - pause_time
        selected_word = 0
        sentence = get_sentence_at_time(time_key)
        selected_sentence = ts.tokenize(sentence)
        get_translation()
import curses
action_dict = {
            109: jump_prev_sentence, # m
            110: jump_next_sentence, # n
            104: prev_word, # h
            108: next_word, # l 
            112: pause_program, # p
            27: quit_program, # ESC
            115: save_cookie # s
            
        }
def get_time_key():
    hours_key = math.floor(t / 3600)
    minutes_key = math.floor(t / 60)
    seconds_key = t % 60
    return f'{hours_key:02}{minutes_key:02}{seconds_key:02}'

def get_sentence_at_time(time_key):
    to_show = [sub_array[k] for k in sub_array if time_key >= k and time_key <= sub_array[k]['end_time']]
    return ' '.join([ts['description'] for ts in to_show]);

import sys,os

t = 0
def draw_menu(stdscr):
    global t, selected_word, selected_sentence, time_key, sentence, start_time

    sync_time()
    last_sync = time.time()
    # Clear and refresh the screen for a blank canvas
    stdscr.clear()
    stdscr.refresh()
    # Start colors in curses
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    height, width = stdscr.getmaxyx()
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)
    display_selection = ['---', '', '']
    start_time = time.time()
    while t < max_time_seconds and isRunning:
        stdscr.erase()
        t = int(time.time() - start_time)

        if time.time() - last_sync > 2:
            sync_time()
            last_sync = time.time()

        if not is_paused:
            time_key = get_time_key()
            sentence = get_sentence_at_time(time_key)
            to_display = "---" if sentence == "" else sentence
            stdscr.addstr(int(height//2 + 1), int(width//2 - len(to_display) // 2 - len(to_display) % 2), to_display)
        else:
            if not selected_word is None and len(selected_sentence) > selected_word:
                if sentence.strip():
                    display_selection = [''.join(selected_sentence[:selected_word]),
                         selected_sentence[selected_word],
                        ''.join(selected_sentence[selected_word+1:])]
            to_display = display_selection[0]
            total_length = len(''.join(display_selection))
            stdscr.addstr(int(height//2 + 1), int(width//2 - total_length // 2 - total_length % 2), to_display)
            stdscr.addstr(display_selection[1], curses.color_pair(1))
            stdscr.addstr(display_selection[2])

        if translation is not None:
            defs = ','.join(translation.definitions)[:width - 150]
            reads = ', '.join(translation.readings)[:width - 150]
            types = ', '.join(translation.types)[:width - 150]
            try:
                stdscr.addstr(int(height//2 + 2), int(width//2 - len(defs) // 2 - len(defs) % 2), defs)
                stdscr.addstr(int(height//2 + 3), int(width//2 - len(reads) // 2 - len(reads) % 2), reads)
                stdscr.addstr(int(height//2 + 4), int(width//2 - len(types) // 2 - len(types) % 2), types)
            except:
                pass
        statusbarstr = f"Press 'ESC' to exit | STATUS BAR | {time_key[:2]}:{time_key[2:4]}:{time_key[4:]}"

        start_y = int((height // 2) - 2)

        # Render status bar
        stdscr.attron(curses.color_pair(3))
        stdscr.addstr(height-1, 0, statusbarstr)
        stdscr.addstr(height-1, len(statusbarstr), " " * (width - len(statusbarstr) - 1))
        stdscr.attroff(curses.color_pair(3))

        # Refresh the screen
        c = stdscr.getch()
        if c in action_dict:
            action_dict[c]()
        height, width = stdscr.getmaxyx()

def main():
    curses.wrapper(draw_menu)

if __name__ == "__main__":
    main()

