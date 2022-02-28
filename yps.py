import datetime
import os
import random
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
from scrapy.crawler import CrawlerRunner
from webdriver_manager.chrome import ChromeDriverManager
from scrapy.exceptions import CloseSpider
from scrapy.spiderloader import SpiderLoader
from scrapy.utils import project
from scrapy.utils.log import configure_logging
from twisted.internet import reactor
import threading

class PrintLogger(object):  # create file like object
    def __init__(self, textbox):  # pass reference to text widget
        self.textbox = textbox  # keep ref

    def write(self, text):  # make field editable
        self.textbox.insert(tk.END, text)  # write text to textbox

    def flush(self):  # needed for file like object
        pass
def user_agents():
    ua_list= [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36',

    ]
    return  random.choice(ua_list)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Yellow Pages Scraper')
        self.geometry('400x200')
        self.resizable(0, 0)
        self.location = tk.StringVar(self)
        self.distance_update = tk.StringVar(self, value=0)
        self.distance_val = tk.StringVar(self, value=50000)

        self.keyword_text = tk.StringVar(self, 'restuarants')
        self.location_text = tk.StringVar(self)
        self.ouput = tk.StringVar(self)
        self.folder_path_text = tk.StringVar(
            self, value=os.path.join(os.path.join(os.path.expanduser('~'), 'Desktop')))
        self.chosen_spider = tk.StringVar(self)
        self.chosen_spider.set('Select')
        self.execute_thread = None
        self.feed_options = ['json', 'csv']
        self.feed_text = tk.StringVar(self, value=self.feed_options[1])

        self.columnconfigure(0, weight=4)
        self.columnconfigure(1, weight=1)
        self.__create_widgets()

    def __create_widgets(self):
        input_frame = ttk.Frame(self)
        input_frame.columnconfigure(0, weight=1)
        input_frame.columnconfigure(1, weight=3)
        ttk.Label(input_frame, text='Find:').grid(column=0, row=0, sticky=tk.W)
        keyword = ttk.Entry(input_frame, width=30, textvariable=self.keyword_text)
        keyword.focus()
        keyword.grid(column=1, row=0, sticky=tk.W)
        ttk.Label(input_frame, text='Location:').grid(column=0, row=1, sticky=tk.W)
        location = ttk.Entry(input_frame, width=30, textvariable=self.location_text)
        location.grid(column=1, row=1, sticky=tk.W)
        #
        # ttk.Label(input_frame, text='Distance:').grid(column=0, row=2, sticky=tk.W)
        # self.distance = ttk.Entry(input_frame, width=30, textvariable=self.distance_val)
        # self.distance.grid(column=1, row=2, sticky=tk.W)

        lbl_frame = ttk.LabelFrame(input_frame, text='Feed Type:')
        lbl_frame.grid(column=0, row=4, sticky='W')

        ttk.Combobox(lbl_frame, textvariable=self.feed_text, values=self.feed_options, width=10).grid(column=0, row=0,
                                                                                                      sticky=tk.W)
        input_frame.grid(column=0, row=0)
        for widget in input_frame.winfo_children():
            widget.grid(padx=0, pady=5)

        button_frame = ttk.Frame(self)
        button_frame.columnconfigure(0, weight=1)

        spiders = [s for s in self.get_spiders()]

        ttk.Combobox(button_frame, textvariable=self.chosen_spider, values=spiders, width=10).grid(column=0, row=0,
                                                                                                   sticky=tk.W)
        ttk.Button(button_frame, text='Start', command=lambda: self.execute_threading(None)).grid(column=0, row=1)
        ttk.Button(button_frame, text='Save To', command=self.browse_btn).grid(column=0, row=2)
        ttk.Label(button_frame, text='save_path', textvariable=self.folder_path_text, wraplength=50).grid(column=0,
                                                                                                          row=3)
        button_frame.grid(column=1, row=0, sticky='NW')
        for widget in button_frame.winfo_children():
            widget.grid(padx=0, pady=5)
        for widget in self.winfo_children():
            widget.grid(padx=0, pady=3)

    # def update_distance(self,event):
    #         self.distance_update.set(f'{round(self.distance.get())} Km')
    #         self.distance_val.set(round()
    def browse_btn(self):
        folder_path = filedialog.askdirectory()
        self.folder_path_text.set(folder_path)

    def choose_feed(self, value):
        self.feed_text.set(value)

    def get_spiders(self):
        return [s for s in SpiderLoader.from_settings(project.get_project_settings()).list()]

    def execute_spider(self):
        # custom_feeds = ['title', 'author', 'date', 'article', 'link']
        if self.keyword_text.get() == '':
            messagebox.showerror(
                'Error', 'Keyword should not be None')
            self.execute_thread = None
            return

        if self.feed_text.get() not in self.feed_options:
            messagebox.showerror(
                'Error', 'Please choose an output Feed')
            self.execute_thread = None
            return

        ran = datetime.datetime.timestamp(datetime.datetime.now())
        try:
            output_url = f'file:///{self.folder_path_text.get()}/YP_file{str(ran).replace(".", "")}.{self.feed_text.get()}'

            setting = project.get_project_settings()

            setting.set('FEEDS', {output_url: {'format': self.feed_text.get()}})
            # setting.set('FEED_EXPORT_FIELDS', custom_feeds)

            if self.chosen_spider.get().startswith('yp'):
                custom_settings = {
                    'SELENIUM_DRIVER_NAME': 'chrome',
                    'SELENIUM_DRIVER_EXECUTABLE_PATH': ChromeDriverManager().install(),
                    'SELENIUM_DRIVER_ARGUMENTS': ['--incognito',f'user-agent={user_agents()}',"start-maximized"],
                    'DOWNLOADER_MIDDLEWARES': {

                        'scrapyselenium.SeleniumMiddleware': 800

                    },

                }
                setting.update(custom_settings)
            runner = CrawlerRunner(setting)

            configure_logging()

            d = runner.crawl(self.chosen_spider.get(), kword=self.keyword_text.get(), location=self.location_text.get())
            #
            d.addBoth(lambda _: reactor.stop())
            reactor.run(installSignalHandlers=False)
            messagebox.showinfo('success', 'The data has been scraped.')

        except CloseSpider as err:
            messagebox.showerror('Stopped', err.reason)
            self.execute_btn['state'] = 'enable'

    def execute_threading(self, event):
        self.execute_thread = threading.Thread(
            target=self.execute_spider, daemon=True)
        if self.execute_thread is not None:
            try:
                if not self.execute_thread.is_alive():
                    self.execute_thread.start()
                    self.after(10, self.check_thread)
            except AttributeError:
                pass

    def check_thread(self):
        if self.execute_thread.is_alive():
            self.after(10, self.check_thread)


if __name__ == '__main__':
    root = App()
    root.attributes('-topmost', 1)
    root.mainloop()
