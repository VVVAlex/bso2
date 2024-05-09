#!/usr/bin/env python

import tkinter
import customtkinter as ctk
import time
from customtkinter import CTkLabel
from customtkinter import CTkFrame
from customtkinter import CTkToplevel
from customtkinter import CTkButton
from customtkinter import ThemeManager
from common import load_image, family, font_size

# list_images_1 = ('ask1', 'err1', 'inf1', 'info1', 'warn1')  # light
# list_images_2 = ('ask2', 'err2', 'inf2', 'info2', 'warn2')  # dark


class CTkInputDialog:
    """Класс для создания диалогов showerror, showinfo, showwarning, askyesno"""

    def __init__(self,
                 master=None,
                 title="CTkDialog",
                 text="CTkDialog",
                 tip_dlg="info",
                 # fg_color=None,
                 # hover_color=None,           # "default_theme",
                 # border_color=None
                 ):
        # super().__init__(fg_color=fg_color)             #
        self.master = master
        self.tip_dlg = tip_dlg
        self.but_cancel = False

        # img = create_images(list_images_1, list_images_2, 50)
        # if self.tip_dlg == 'info':
        #     self.image = img.info
        # if self.tip_dlg == 'error':
        #     self.image = img.error
        # if self.tip_dlg == 'warn':
        #     self.image = img.warn
        # if self.tip_dlg == 'ask':
        #     self.image = img.ask
        #     self.but_cancel = True
        # TODO:  mach case
        if self.tip_dlg == 'info':
            self.image = load_image('info2.png', 'info1.png', (50, 50))
        elif self.tip_dlg == 'error':
            self.image = load_image('err2.png', 'err1.png', (50, 50))
        elif self.tip_dlg == 'warn':
            self.image = load_image('warn2.png', 'warn1.png', (50, 50))
        elif self.tip_dlg == 'ask':
            self.image = load_image('ask2.png', 'ask1.png', (50, 50))
            self.but_cancel = True

        self.running = False
        self.user_input = None
        self.height = len(text.split("\n"))*20 + 140
        self.text = text

        self.window_bg_color = ThemeManager.theme["CTkToplevel"]["fg_color"]
        self.fg_color = ThemeManager.theme["CTkButton"]["fg_color"]
        self.hover_color = ThemeManager.theme["CTkButton"]["hover_color"]
        self.border_color = ThemeManager.theme["CTkButton"]["hover_color"]

        self.top = CTkToplevel()
        self.top.geometry(f"{310}x{self.height}")
        self.top.minsize(310, self.height)
        self.top.maxsize(310, self.height)
        # self.top.resizable(False, False)
        self.top.overrideredirect(True)     # убрать заголовок окна
        # self.top.overrideredirect(0)      # MAC OS
        # self.top.title(title)
        self.top.lift()
        self.top.focus_force()
        self.top.grab_set()
        self.__position()
        self.top.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.top.after(10, self.create_widgets)

    def create_widgets(self) -> None:
        font = ctk.CTkFont(family=f"{family}", size=font_size)
        label_frame = CTkFrame(master=self.top, corner_radius=0,
                               height=self.height - 100, fg_color=self.window_bg_color)
        label_frame.pack(expand=True, fill='both')
        button_frame = CTkFrame(master=self.top, corner_radius=0, fg_color=self.window_bg_color,
                                width=300, height=40)
        button_frame.pack()

        CTkLabel(master=label_frame, text='', image=self.image, width=85,
                 height=self.height-100, anchor='center').pack(side='left', padx=(20, 5))

        CTkLabel(master=label_frame, text=self.text, font=font,
                 height=self.height-100, anchor='w', justify='left').pack(
            side='left', expand=True, fill='x')

        ok_button = CTkButton(master=button_frame, text='Ok',
                              # text_color=('gray10', 'gray90'),
                              font=font, border_width=2,
                              width=100, command=self.ok_event, fg_color=self.fg_color,
                              hover_color=self.hover_color, border_color=self.border_color)

        cancel_button = CTkButton(master=button_frame, text='Нет',
                                  # text_color=('gray10', 'gray90'),
                                  font=font, border_width=2,
                                  width=100, command=self.cancel_event, fg_color=self.fg_color,
                                  hover_color=self.hover_color, border_color=self.border_color)

        if not self.but_cancel:
            ok_button.place(relx=0.5, rely=0.5, anchor=tkinter.CENTER)
        else:
            ok_button.place(relx=0.28, rely=0.5, anchor=tkinter.CENTER)
            cancel_button.place(relx=0.72, rely=0.5, anchor=tkinter.CENTER)

    def ok_event(self, event=None) -> None:
        """Принять"""
        # self.var.set(1)
        self.user_input = True
        self.running = False
        # self.running = True
        # self.top.destroy()

    def cancel_event(self, event=None) -> None:
        """Отклонить"""
        # self.var.set(0)
        self.running = False
        self.top.destroy()

    def on_closing(self) -> None:
        """Закрыть окно X"""
        self.user_input = False
        self.running = False
        # self.top.destroy()

    def get_input(self) -> bool:
        """Вернуть выбор True False"""
        self.running = True
        while self.running:
            try:
                self.top.update()
            except Exception:
                return self.user_input
            finally:
                time.sleep(0.01)
        time.sleep(0.05)
        self.top.destroy()
        return self.user_input

    def __position(self) -> None:
        """Переместить окно"""
        # x = (self.top.winfo_screenwidth() - self.top.winfo_width())//2
        # y = (self.top.winfo_screenheight() - self.top.winfo_height())//2
        # self.top.geometry(f"{self.top.winfo_width()}x{self.top.winfo_height()}+{x}+{y}")
        self.top.geometry(f"{self.top.winfo_width()}x{self.top.winfo_height()}+300+300")
        self.top.update()

# self.var = tkinter.StringVar()
# self.top.wait_variable(self.var)      # stop do  wait_variable(self.var)


def showinfo(title=None, text=None,  tp="info", **options) -> bool:
    """Max длина текста в одной строке 25 символов"""
    return CTkInputDialog(title=title, text=text,  tip_dlg=tp, **options).get_input()


def showerror(title=None, text=None,  tp='error', **options) -> bool:
    return CTkInputDialog(title=title, text=text, tip_dlg=tp, **options).get_input()


def showwarning(title=None, text=None,  tp='warn', **options) -> bool:
    s = CTkInputDialog(title=title, text=text, tip_dlg=tp, **options)
    return s.get_input()


def askyesno(title=None, text=None,  tp='ask', **options) -> bool:
    s = CTkInputDialog(title=title, text=text, tip_dlg=tp, **options)
    return s.get_input()
