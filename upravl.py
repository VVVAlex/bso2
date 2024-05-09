#!/usr/bin/env python
import customtkinter as ctk
from common import get_color, family, font_size


class Uprav(ctk.CTkFrame):
    """Управление режимами"""

    def __init__(self, master):
        super().__init__(master, corner_radius=0)
        self.root = master.root
        font = ctk.CTkFont(family=f"{family}", size=font_size)
        row = 0

        self.lb_dist = ctk.CTkLabel(master=self, text="Глубина",
                                    width=100, font=font,
                                    padx=10, pady=2, anchor='w')
        self.lb_dist.grid(row=row, column=0, sticky="w",
                          padx=10, pady=2)
        self.lb_glub = ctk.CTkLabel(master=self, text="",
                                    width=120, font=font,
                                    padx=2, pady=2, anchor='e')
        self.lb_glub.grid(row=row, column=1, sticky="ew",
                          padx=10, pady=1)
        row += 1
        self.lb_ut = ctk.CTkLabel(master=self, text="Уровень",
                                  width=100, font=font,
                                  padx=10, pady=2, anchor='w')
        self.lb_ut.grid(row=row, column=0, sticky="w",
                        padx=10, pady=2)
        self.lb_uv = ctk.CTkLabel(master=self, text="",
                                  width=100, font=font,
                                  padx=10, pady=2, anchor='e')
        self.lb_uv.grid(row=row, column=1, sticky="e",
                        padx=3, pady=1)
        row += 1
        self.lb_lt = ctk.CTkLabel(master=self, text="Длит.",
                                  width=100, font=font, padx=10, pady=2, anchor='w')
        self.lb_lt.grid(row=row, column=0, sticky="w",
                        padx=10, pady=2)
        self.lb_lv = ctk.CTkLabel(master=self, text="",
                                  width=100, font=font, padx=10, pady=2, anchor='e')
        self.lb_lv.grid(row=row, column=1, sticky="e",
                        padx=3, pady=1)
        row += 1
        self.lb_et = ctk.CTkLabel(master=self, text="Эхо",
                                  width=100, font=font, padx=10, pady=2, anchor='w')
        self.lb_et.grid(row=row, column=0, sticky="w",
                        padx=10, pady=2)
        self.lb_ev = ctk.CTkLabel(master=self, text="",
                                  width=100, font=font, padx=10, pady=2, anchor='e')
        self.lb_ev.grid(row=row, column=1, sticky="ew",
                        padx=3, pady=2)

        self.lb_rgb_l = ctk.CTkLabel(master=self, text="Цвет",
                                     width=100, font=font, padx=10, pady=2, anchor='w')
        row += 1
        self.lb_rgb_l.grid(row=row, column=0, sticky="w",
                           padx=10, pady=2)
        self.lb_rgb = ctk.CTkLabel(master=self, width=45,
                                   corner_radius=8, height=15, text='',
                                   padx=0, pady=0, anchor='e')
        self.lb_rgb.grid(row=row, column=1, sticky="e",
                         padx=10, pady=2)
        row += 1
        self.lb_upr = ctk.CTkLabel(master=self, text='Порог', width=100,
                                   anchor='w', font=font, padx=10, pady=1)
        row += 1
        self.lb_upr.grid(row=row, column=0, sticky="w",
                         padx=10, pady=2)
        self.lb_uprg = ctk.CTkLabel(master=self, text='',
                                    width=100, font=font,
                                    padx=0, pady=0, anchor='e')
        self.lb_uprg.grid(row=row, column=1, sticky="e",
                          padx=10, pady=2)

        self.lb_depth = ctk.CTkLabel(master=self, text='Диапазон', width=100,
                                     anchor='w', font=font, padx=10, pady=1)
        row += 1
        self.lb_depth.grid(row=row, column=0, sticky="w",
                           padx=10, pady=2)
        self.lb_depthq = ctk.CTkLabel(master=self, text='',
                                      width=100, font=font,
                                      padx=0, pady=0, anchor='e')
        self.lb_depthq.grid(row=row, column=1, sticky="e",
                            padx=10, pady=2)
        self.lb_rej = ctk.CTkLabel(master=self, text='Режим', width=100,
                                   anchor='w', font=font, padx=10, pady=1)
        row += 1
        self.lb_rej.grid(row=row, column=0, sticky="w",
                         padx=10, pady=2)
        self.lb_rejq = ctk.CTkLabel(master=self, text='',
                                    width=100, font=font,
                                    padx=0, pady=0, anchor='e')
        self.lb_rejq.grid(row=row, column=1, sticky="e",
                          padx=10, pady=2)
        self.lb_frec = ctk.CTkLabel(master=self, text='Частота', width=100,
                                    anchor='w', font=font, padx=10, pady=1)
        row += 1
        self.lb_frec.grid(row=row, column=0, sticky="w",
                          padx=10, pady=2)
        self.lb_frecq = ctk.CTkLabel(master=self, text='',
                                     width=100, font=font,
                                     padx=0, pady=0, anchor='e')
        self.lb_frecq.grid(row=row, column=1, sticky="e",
                           padx=10, pady=2)

    @staticmethod
    def cal_ampl(cod: int) -> float:
        """Вычислить амплитуды эхо в мв."""
        return round(1000 * cod * 2.5 * 8 / 2048, 2)

    def update_upr(self, dat_upr) -> None:
        """Обновить виджета по dat_upr=NamedTuple(depth: int, ku: int,
         cnt: int, m: int, ampl: int, len: int, distance: int, freq: str, rej: str)
            вызывается из root"""
        # print(dat_upr)
        dct = {'L': "МГ", 'M': "СГ", 'H': "БГ", 'S': "Авто", 'R': "Ручн."}
        self.lb_uprg.configure(text=f"{dat_upr.ku}") if dat_upr.ku else self.lb_uprg.configure(text="")
        self.lb_ev.configure(text=f"{dat_upr.cnt} / {dat_upr.m}")
        ampl = self.cal_ampl(dat_upr.ampl)
        self.lb_uv.configure(text=f"{ampl:4.0f} мВ") if ampl else self.lb_uv.configure(text="")
        len_ = self.root.cal_len(dat_upr.len)
        self.lb_lv.configure(text=f"{len_:0.2f} м") if len_ else self.lb_lv.configure(text="")
        color = get_color(dat_upr.ampl)
        self.lb_rgb.configure(fg_color=color)
        self.lb_glub.configure(text=f"{dat_upr.distance / 10:4.1f} м") if dat_upr.distance else\
            self.lb_glub.configure(text="")
        self.lb_frecq.configure(text=f"{dat_upr.freq}")
        self.lb_rejq.configure(text=f"{dct.get(dat_upr.rej, '')}")
        self.lb_depthq.configure(text=f"{dct.get(dat_upr.depth, '')}")
