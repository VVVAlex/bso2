#!/usr/bin/env python
import time
import array
import csv
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from collections import deque
from fild import Fild
from head import Head
from stbar import Footer
from upravl import Uprav
from tools import Tools
from common import ViewDataUpr, load_image
from common import config, write_config, family, font_size     # read_config
from portthread import PortThread, port_exc
from pathlib import Path
from simpleedit import SimpleEditor
from title import TitleTop
from top_widget import CTkTop
from form import ToplevelHelp


show = config.getboolean('Verbose', 'visible')
scheme = config.get('Font', 'scheme')

one_port = 1

Width = config.getint('Size', 'width')
Height = config.getint('Size', 'height')

trace = print if show else lambda *x: None

# ctk.set_appearance_mode("System")    # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme(scheme)  # Themes: "blue" (standard), "green", "dark-blue"


class RF(ctk.CTkFrame):
    """Правый фрейм"""

    def __init__(self, root):
        super().__init__(root, corner_radius=0, border_width=2, border_color="grey75")
        self.root = root
        self.tools = Tools(self)    # настройки + метки
        self.tools.grid(row=0, column=0, pady=(2, 0), padx=2, sticky="we")
        self.tools.grid_columnconfigure(0, weight=1)
        self.tools.grid_columnconfigure(1, weight=1)

        self.u_panel = Uprav(self)  # панель управления
        self.u_panel.grid(row=1, column=0, pady=(0, 0), padx=2, sticky="nsew")


class App(ctk.CTk):
    """Корневой класс приложения"""

    WIDTH = 1340
    HEIGHT = 750
    theme_mode = None       # 1-'dark', 0-'light'

    def __init__(self):

        super().__init__()
        self.title("")
        self.xk1 = False                                            # XK_01 разрешить БГ (False)
        self.geometry(f'{Width}x{Height}+100+0')
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.minsize(1080, 680)
        self._wm_state = True                                       # во весь экран True
        self.theme_mode = 0
        self.s = ttk.Style()                                        # for TSizegrip
        self.s.theme_use("clam")                    # !
        appearance_mode = config.getint('Font', 'app_mode')
        # value, self.theme_mode = ("Dark", 1) if appearance_mode else ("Light", 0)
        value = "Dark" if appearance_mode else "Light"
        ctk.set_appearance_mode(value)
        TitleTop(self, "БСО-2")
        self._change_appearance_mode(value)
        # ctk.set_appearance_mode('Light')

        self.im_korabl = load_image('korab.png', im_2=None, size=(48, 24))
        self.font = ctk.CTkFont(family=f"{family}", size=font_size)

        self.crashes = 0                                # число сбоев для ППУ Неисправен
        self.crashes_gps = 5                            # число сбоев gps
        self.enable = True
        self.id_timeout = None
        self.vz = 1500

        self._vz = config.getint('System', 'vz')      # скорость звука
        self._zg = config.getfloat('System', 'zagl')
        self.zona = config.getfloat('System', 'vzona')

        # для запрета постановки всех меток
        self.loop = tk.BooleanVar(value=False)
        
        self.win = None                                 # нет окна заглубления
        self.choose_gals = False                        # признак выбора галса

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.r_frame = RF(self)
        self.r_frame.grid(row=0, column=1, rowspan=2, sticky="ns", padx=2)
        self.r_frame.rowconfigure(0, weight=1)
        self.r_frame.rowconfigure(1, weight=100)
        self.r_frame.columnconfigure(0, weight=0)

        self.u_panel = self.r_frame.u_panel
        self.tools = self.r_frame.tools

        self.head = Head(self)
        self.head.grid(row=0, column=0, padx=(2, 0), sticky="we")
        self.head.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        w_scr = self.winfo_screenwidth() - 296
        self.data_deq = deque(maxlen=w_scr)

        self.enable = True
        height = App.HEIGHT + 230
        self.board = Fild(self, App.WIDTH + 400, height)                    # экран эхограммы
        self.board.grid(row=1, column=0, sticky="nsew", padx=(2, 0), pady=1)
        self.board.grid_rowconfigure((0, 1), weight=1)  # minsize=80
        self.board.grid_columnconfigure(0, weight=1)

        self.st_bar = Footer(self)                                          # строка состояния
        self.st_bar.grid(row=2, column=0, columnspan=2, sticky="we", pady=(0, 6))
        self.st_bar.grid_columnconfigure(0, weight=1)

        self.g_ser = PortThread(self.gps_read_data)
        self.ser = PortThread(self.on_receive_func)
        msg = self._open_ports(self.ser, self.g_ser)
        self.depth = 'L'
        self.data_upr = ViewDataUpr()                                        # данные для панели управления
        self.u_panel.update_upr(self.data_upr)
        self.records = False                                                # флаг записи галса в файл

        self._check_project(self.st_bar)
        self.st_bar.set_device(msg)
        self.st_bar.set_info_gals('')

        self.init_fild()

        self.gps_manager = GpsManager(self.g_ser, self)
        self.gps_receive = 0                                                # прием данных с НСП
        self.set_flag = False
        self.win_help = None
        self.update()

    def blink(self, arg=None) -> None:
        """Мигнуть телеком"""
        self.st_bar.blink()

    def gps_read_data(self, data: bytes) -> None:
        """Чтение порта GPS"""
        self.gps_manager.gps_read_data(data)

    def set_local_time(self) -> None:
        """Установка машинного времени в head"""
        t = time.strftime('%d.%m.%y %H:%M:%S')
        arg = ('', '', '', '', t, False)
        self.head.set_(*arg)

    @staticmethod
    def _open_ports(ser: PortThread, g_ser: PortThread) -> str:
        """Открытие портов"""
        port_pui = config.get('Port', 'port_pui')
        baudrate_pui = config.getint('Port', 'baudrate_pui')
        port_gps = config.get('Port', 'port_gps')
        baudrate_gps = config.getint('Port', 'baudrate_gps')
        timeout = config.getfloat('Port', 'timeout')
        timeout_gps = config.getfloat('Port', 'timeout_gps')
        error_p, error_g = '', ''
        try:
            ser.open_port(port_pui)
            ser.tty.baudrate = baudrate_pui
            ser.tty.timeout = timeout
            ser.start()
        except port_exc:
            error_p = 'не'
        if g_ser:
            try:
                g_ser.open_port(port_gps)
                g_ser.tty.baudrate = baudrate_gps
                g_ser.tty.timeout = timeout_gps
                g_ser.start()
            except port_exc:
                error_g = 'не'
        else:
            error_g = 'не'
        msg_1 = (f'Порты:  ППУ  <{port_pui}> {error_p} открыт,'
                 f'   НСП  <{port_gps}> {error_g} открыт.')
        return msg_1

    def init_fild(self) -> None:
        """Создание нового полотна и очередей"""
        self.board.create_fild()
        self.update_idletasks()
        self.bind_()

    def bind_(self) -> None:
        """Привязки событий"""
        self.bind("<Up>", self.board.up)
        self.bind("<Down>", self.board.down)
        self.bind("<Home>", self.board.home)
        self.bind("<End>", self.board.en)
        self.bind("<Alt-F4>", self._on_closing)
        self.bind("<Return>", lambda arg=None: None)
        self.bind("<Control-p>", self.board.all_one_echo)
        self.bind("<Control-l>", self.board.show_duration_echo)
        self.bind("<Control-b>", self.board.fon_color_ch)
        self.bind("<Control-m>", self.board.off_scale)
        self.bind("<Control-t>", self.board.time_metka_on)
        self.bind("<Control-w>", self.board.hide_metki)
        self.bind("<Control-h>", self.create_toplevel_help)
        self.bind("<Control-o>", self.change_app_mode)
        # self.bind("<Control-v>", self.get_version)
        # self.bind("<Control-n>", self.get_noise)
        self.bind("<Control-e>", self.edit_config)
        # self.bind("<Control-z>", self._full_scr)
        # self.bind("<Escape>", self._clr)

    # def _full_scr(self, arg=None):
    #     """Развернуть на весь экран"""
    #     self.state('zoomed') if self._wm_state else self.state('normal')
    #     self.attributes("-fullscreen", self._wm_state)
    #     self._wm_state = not self._wm_state
    #     self._change_appearance_mode('Light')
    #     self._change_appearance_mode('Dark')

    def _clr_board_tag_all(self,  tag: tuple) -> None:
        """Очистить на холстах элементы с тегами"""
        self.board.clr_item(tag)

    def _clr(self, arg=None) -> None:
        """Обработчик клавиши ESC"""
        self._clr_board_tag_all(('version', 'noise', 'not_data'))

    def on_receive_func(self, data: bytes) -> None:
        """Чтение линии 12bytes + !or? + # + 91bytes = 105"""
        self.update()
        if len(data) == 105 and data[-2:] == b'\r\n':
            if data[0] == 36 or data[0] == 37:                               # $ or %
                self.crashes = 0
                self.loop.set(True)
            else:
                trace('not $ or %')
                return
            trace(f':: {data}')
            self._work(data[:-2])
            self.blink()                                     # мигнуть
        else:
            trace(f'* {len(data)}')
        self.update()

    def _work(self, data: bytes) -> None:
        """Режим работа"""
        # self.t = time.perf_counter()
        # self.answer = True
        self.board = self.board
        self.vz = int.from_bytes(data[6: 8], 'big')        # скорость звука
        self.tools.set_sv(self.vz)
        # rej = 'Авто' if data[2] == 0x53 else 'Ручной'               # режим
        # self.data_upr.rej = rej
        self.data_upr.rej = chr(data[2])
        freq = '25кГц' if data[0] == 0x25 else '50кГц'              # частота
        if data[0] == 0x40:
            freq = '96кГц'
        self.data_upr.freq = freq
        # self._parce_data(data[15:], vz)
        data_point, data_ampl, data_len = self._parce_data(data[15:])
        self._update_data_deque(data_point, data_ampl, data_len)
        self.board.show(data_point, data_ampl, data_len)                # отобразить на холсте
        if self.records:
            f_gals = self.tools.file_gals
            self._write_gals(f_gals, data_point, data_ampl, data_len)   # если надо, то пишем в файл
        # print(time.perf_counter() - self.t)

    def _update_data_deque(self, data_p: array.array, data_a: array.array, data_l: array.array) -> None:
        """Очередь для хранения данных всего экрана"""
        shot = ([n / 10 for n in data_p],
                data_a, data_l, self.board.mark_type)
        self.data_deq.appendleft(shot)

    def _parce_data(self, data: bytes) -> tuple[array.array, ...]:
        """
        Разбор данных, глубин и амплитуд
        (b'depth,ku,m,cnt,not,g0h,g0l,a0h,a0l,d0h,d0l,
         g1h,g1l,a1h,a1l,c1,l1, ... gnh,gnl,anh,anl,cn,ln')
        """
        zg = int(self._zg * 10)                                           # заглубление
        depth = chr(data[0])                # L, M, H, B
        self.depth = depth
        # ku = chr(data[1])
        ku = int(chr(data[1]), 16)  # порог
        # ku = data[1]
        m_cnt = data[2]
        cnt = data[3]
        distance = int.from_bytes(data[4:6], 'big')
        distance = distance + zg if distance else 0
        ampl = data[6]
        len_ = data[7]
        self.data_upr.depth = depth
        self.data_upr.ku = ku
        self.data_upr.cnt = cnt
        self.data_upr.m = m_cnt
        self.data_upr.ampl = ampl
        self.data_upr.len = len_
        self.data_upr.distance = distance

        self.u_panel.update_upr(self.data_upr)                  # данные для панели управления
        self.board.view_glub(distance)                          # вывод глубины
        data_point = array.array('H')                           # 'H' 2 bytes 'B' 1 bytes
        data_ampl = array.array('B')
        data_len = array.array('B')
        data_point.append(distance)
        data_ampl.append(ampl)
        data_len.append(len_)
        dat = data[8:]
        cnt = 20 if cnt > 20 else cnt
        for i in range(0, cnt * 4, 4):
            distance = int.from_bytes(dat[i:i+2], 'big') + zg
            ampl = dat[i+2]
            len_ = dat[i+3]
            data_point.append(distance)
            data_ampl.append(ampl)
            data_len.append(len_)
        return data_point, data_ampl, data_len

    def cal_len(self, cod) -> float:
        if self.depth == 'L':
            n = 0.4
        elif self.depth == 'M':
            n = 1.6
        elif self.depth == 'H':
            n = 12.8
        elif self.depth == 'B':
            n = 12.8  # !
        else:
            return 0.0
        if n > 12 and cod > 126:
            cod = 126
        return round(cod * n * self.vz / 10000, 2)

    def _write_gals(self, filename: Path, data_p: array.array, data_a: array.array,
                    data_l: array.array) -> None:
        """Пишем в файл"""
        data = self.prepare_data_gals(data_p, data_a, data_l)
        # print(data)
        with open(filename, 'a', newline='') as f:
            f_csv = csv.writer(f)
            f_csv.writerow(data)

    def prepare_data_gals(self, data_p: array.array, data_a: array.array, data_l: array.array) -> list:
        """Подготовить данные для записи галса
          (формат, глубина, амплитуда, длительность, объект дата время,
           широта, долгота, скорость, курс, скорость звука, осадка, порог,
           диап. глубин, режим, частота, число стопов, число кор. стопов,
           ручн. метка, цвет ручн. метки , авто метка.)
        """
        format_ = config.get('System', 'fmt')
        # vz = config.getint('System', 'vz')
        vz = self._vz
        zg = self._zg
        dt = self.data_upr
        # send_data = self.send_data
        freq = '200'
        depth, ku, cnt, m, ampl, lenth, glub = dt.depth, dt.ku, dt.cnt, dt.m, dt.ampl, dt.len, dt.distance
        # ku += 1           #
        rej = self.data_upr.rej
        try:
            # gps_t, gps_s, gps_d, gps_v, gps_k = self.gps_manager.get_data_gps()
            raise TypeError
        except TypeError:
            gps_t, gps_s, gps_d, gps_v, gps_k = '', '', '', '', ''
        if not gps_t:
            gps_t = time.strftime('%d.%m.%y %H:%M:%S')
        mark_ = self.data_deq[0][-1]
        m_man, m_avto, color_mm = '', '', ''
        if mark_[0]:
            if mark_[1] == 'M':
                m_man = mark_[0]
                color_mm = 'red'
            if mark_[1] == 'A':
                m_avto = mark_[0]
        file_list = [format_, glub, ampl, self.cal_len(lenth), gps_t, gps_s, gps_d, gps_v, gps_k,
                     vz, zg, ku, depth, rej, freq, cnt, m,
                     m_man, color_mm, m_avto]
        for gd, ad, ld in zip(data_p[1:], data_a[1:], data_l[1:]):
            file_list.extend([gd, ad, self.cal_len(ld)])
        return file_list

    def pref_form(self, d: str, z: float, zona: float) -> None:
        """Возврат результата из формы 'DBT'.., z(заглубл.) если есть изменения и
           переписать config.ini"""
        self.zona = zona
        self._zg = z                                 # изменение заглубл.
        self.tools.update_(f'{z}', d)
        self.head.set_utc()
        config.set('System', 'zagl', f'{z}')
        config.set('System', 'fmt', f'{d}')
        write_config()

    def change_app_mode(self, arg=None) -> None:
        self._change_appearance_mode('Light') if self.theme_mode else self. _change_appearance_mode('Dark')
        self.close_help()
        geometry_str = self.geometry()
        tmp = geometry_str.split('x')
        width = tmp[0]
        tmp2 = tmp[-1].split('+')
        height = tmp2[0]
        x = tmp2[1]
        y = str(int(tmp2[2]) + 1)
        self.geometry(f"{width}x{height}+{x}+{y}")      # дергаем окно

    def _change_appearance_mode(self, new_appearance_mode) -> None:
        """Сменить тему"""
        if new_appearance_mode == 'Dark':
            self.s.configure('TSizegrip', background='grey19')
            self.theme_mode = 1
            # self.app_mode.set(0)
        else:
            self.s.configure('TSizegrip', background='grey82')
            self.theme_mode = 0
            # self.app_mode.set(1)
        ctk.set_appearance_mode(new_appearance_mode)
        config.set('Font', 'app_mode', f'{self.theme_mode}')
        write_config()

    @staticmethod
    def _check_project(st_bar: Footer) -> None:
        """Проверка существования поекта"""
        if not Path(config.get('Dir', 'dirprj')).exists():
            config.set('Dir', 'dirprj', '')
            write_config()
            st_bar.set_info_project('')

    def edit_config(self, arg=None):
        """Редактировать файл config.ini"""
        # window_ = ctk.CTkToplevel(self)
        window_ = CTkTop(title="Config.ini", icon="config", font=self.font,
                         border_width=2, width=1100, height=800)    # btn_close=False,
        frame = ctk.CTkFrame(window_.w_get)
        frame.grid(sticky="nsew")

        SimpleEditor(window_, frame)
        # window_.bind("<Escape>", lambda x: window_.destroy())
        # self.after(300, lambda: self.close_help())
        self.after(300, lambda: self.top.close_help())

    def create_toplevel_help(self, arg=None) -> None:
        """Окно подсказок для привязок"""
        self.top = ToplevelHelp(self)

    def close_help(self, arg=None) -> None:
        """Убрать окно"""
        self.top.close_help()

    def _on_closing(self, arg=None) -> None:
        """Выход"""
        # if self.btn_start.cget('text') == self.STOP:
        #     self.btn_start_()        # Перейти в ожидание если излучение
        self.ser.stop()
        self.g_ser.stop()
        # sys.stdout.flush()
        raise SystemExit()


class GpsManager:
    """Класс работы с НСП(GPS)"""

    def __init__(self, g_ser: PortThread, root):
        self.g_ser = g_ser
        self.root = root
        self.head = self.root.head
        self.crashes_gps = 5
        self.data_gps = None
        self.zona = config.getfloat('System', 'vzona')

    def gps_read_data(self, data: bytes) -> None:
        """Приём из НСП в потоке
        '$GPRMC,123519.xxx,A,4807.038x,N,01131.000x,E,x22.4,084.4,230394,003.1,W*6A\n'
        123419 – UTC время 12:34:19, А – статус, 4807.038,N – Широта, 01131.000,Е – Долгота,
        022.4 – Скорость, 084.4 – Направление движения, 230394 – Дата, 003.1,W – Магнитные вариации
        """
        # print(f'<< {data}')
        self.root.gps_receive = 2
        if data:
            self.crashes_gps = 0
            data = data.decode('latin-1').split(',')[1:10]      # list[str...]
            if len(data) == 9:
                self._parse_data_gps(data)
            else:
                self.crashes_gps += 1
        else:
            self.crashes_gps += 1
        if self.crashes_gps > 3:
            self.crashes_gps = 3
            self.root.set_local_time()

    def _parse_data_gps(self, data: list) -> None:
        """Разбор данных gps"""
        # print('+')
        try:
            s_ = data[2].split('.')
            d_ = data[4].split('.')
            sh = f"{s_[0][:-2]} {s_[0][-2:]}.{s_[1][:3]} {data[3]}"  # {0xB0:c} °
            d = f"{d_[0][:-2]} {d_[0][-2:]}.{d_[1][:3]} {data[5]}"
        except IndexError as er:
            # print(f'e > {er}')
            sh = d = ''
        try:
            str_struct = time.strptime(data[0].split('.')[0] + data[8], "%H%M%S%d%m%y")
            t_sec = time.mktime(str_struct)
            t_sec += self.zona * 3600
            str_struct = time.localtime(t_sec)
            t = time.strftime("%d.%m.%y %H:%M:%S", str_struct)
        except (IndexError, ValueError) as er:
            # print(f't > {er}')
            t = ''
        try:
            vs = f"{float(data[6]):=04.1f}"          # ! 05.1f
            k = f"{float(data[7]):=05.1f}"
        except (IndexError, ValueError) as er:
            # print(f'v > {er}')
            vs = k = ''
        self.head.set_(sh, d, vs, k, t, True)       # только если излучение
        self.data_gps = (t, sh, d, vs, k)

    def get_data_gps(self) -> tuple:
        """Вернуть данные GPS"""
        return self.data_gps


if __name__ == "__main__":
    app = App()
    # app.attributes("-fullscreen", True)       # во весь экран без кнопок
    # app.state('zoomed')                       # развернутое окно
    app.mainloop()
