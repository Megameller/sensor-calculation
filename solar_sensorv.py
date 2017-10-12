"""
Прогрмма для расчета окон солнечного датчика.
Необходимо сделать верхнее меню(для чего пока не понятно)
Добавить вывод лога расчетов, возможно в отдельный фаил
Добавить отрисовку графиков
Потом подцеплять сами библиотеки для отрисовки графиков, если их нет
!!!! Изменения:
теперь поля ввода формируются автоматически
Использовал ttk для поддержки текущщих настроки винды(кнопка красивая теперь)
Создал класс лога, позже допишу туда функцию принта, пока выводит в консоль
!!! Changes: 24.08 (I haven't russian keyboard)
Fix bug with one DataField.
Add simple log. Now you need use self.print() instead print()
Now get_param return singl data array
!!! Изменения: 12.09
Код приведен в частичное соотвествие с PEP8.
Добавленно описание функций
DataField теперь DataDigitalField и возвращает число вместо строк.
Добавленна функциия run --  производит обработку данных, либо выдает сообщение об ошибке
!!! Изменения 19.09
Добавлено построение графика. Правильность построения проверю позже.
!!! Изменения 2.10
Программа обладает полным функцианалом.
Возможно построение графиков реализовать проще и правильнее.
Требуется дороботка внешнего вида интерфейса и расширение функционала под другие задачи.
"""

import collections
import glob
import os
from tkinter import Tk, Text, Toplevel
from tkinter.ttk import Label, Entry, Frame, Button
from tkinter.messagebox import askyesno, showinfo
from tkinter.filedialog import *
import threading
from math import*

# Импортируем один из пакетов Matplotlib
import pylab
# Импортируем пакет со вспомогательными функциями
from matplotlib import mlab
# TODO добавить метод insert DataDigitalField
# TODO необходимо сделать нормальый вывод данных в лог
# TODO add graphic plot
# TODO I have a very good idea with this
FIELDS = {'azimut': ('Угловые поля фотодатчика по азимуту:', 'A1=', 'A2='),
          'zenit': ('Угловые поля фотодатчика по зениту:', 'F1=', 'F2='),
          'coords': ('Координаты фотодатчика:', 'X=', 'Y=', 'Z='),
          'radius': ('Радиус:', 'R=')}

appname = 'Solar sensor 0.02'


class MainWindow(Tk):
    """
    Класс базового окна, наследует все возможности Tk и переназначает метод закрятия для выдачи окна предупреждения
    """
    def __init__(self):
        Tk.__init__(self)

    def destroy(self):
        if askyesno('!!!', 'Выйти из программы?'):
            Tk.quit(self)


class DataLog(Frame):
    def __init__(self, name):
        Frame.__init__(self)
        Label(text=name, justify='left').pack(fill='x')
        self.log = Text(height=10, width=50,)
        self.log.pack(fill='x')

    def insert(self, *data):
        for part in data:
            self.log.insert('end', part)
            self.log.insert('end', '\n')


class DataDigitalField(Frame):
    """
    Класс генерирует стандартное окно полей ввода и позволяет получаеть  из него данные.
    """

    def __init__(self, name, *args):    # перемнное количество аргументов
        Frame.__init__(self)
        self.field_list = list()
        Label(text=name).pack(side='top')

        field = Frame(self)
        field.pack()

        for name in args:
            # помещаем виджет на master-field
            Label(master=field, text=name).pack(side='left')
            # добавляем элементы из полей
            self.field_list.append(Entry(master=field))
            # (длина строки-1 в списке)
            self.field_list[len(self.field_list)-1].pack(side='left')

    def get(self):
        """
        Получает данные из поля и пытается преобразовать в число.
        """
        data = list()

        for field in self.field_list:
            num = self.to_digit(field.get())
            if num:
                data.append(num)
            else:
                return False

        return data

    def insert(self, data):
        """
        Ожидает на вход список переменных, которые заносит в ячейки данных
        """
        for field in self.field_list:
            if data:
                field.insert(0, data.pop(0))

    def clear(self):
        for field in self.field_list:
            field.delete(0)

    @staticmethod
    def to_digit(data):
        """
        Работает только для преобразования строки в число. Иначе негарантируемое поведение.
        Проверяет можно ли преобразовать в целочисленное. Если да,возвращает число.
        В противном случае пробует преобразовать в вещественное.
        При ошибке возвращает False.
        """

        try:
            data = int(data)
        except ValueError:
            try:
                data = float(data)

            except ValueError:
                return False

        except Exception:
            return False

        return data


class SolarMain(MainWindow):

    def __init__(self):

        MainWindow.__init__(self)
        self.title(appname)

        # список размещенных на форме полей ввода
        data_fields = self.make_fields()

        # Размещение окна журнала операция
        self.data_log = DataLog('Результаты расчета:')
        self.data_log.pack()

        Button(text='Расчитать', command=lambda: self.run(data_fields)).pack(side=BOTTOM)
        Button(text='По умолчанию', command=lambda: self.default(data_fields)).pack(side=BOTTOM)
        Button(text='График', command=lambda: self.create_window(data_fields)).pack(side=BOTTOM)


    def make_fields(self):
        """
        Генерация полей ввода данных и размещение их в окне программы
        :return: кортеж из созданных полей
        """

        azimut = DataDigitalField('Угловые поля фотодатчика по азимуту:', 'A1=', 'A2=')
        azimut.pack()
        zenit = DataDigitalField('Угловые поля фотодатчика по зениту:', 'F1=', 'F2=')
        zenit.pack()
        coord = DataDigitalField('Координаты фотодатчика:', 'X=', 'Y=', 'Z=')
        coord.pack()
        radius = DataDigitalField('Радиус:', 'R=')
        radius.pack()

        return azimut, zenit, coord, radius

    @staticmethod
    def default(fields):
        #  F1=  26.7 F2=  94.3 A1=  -4.3 A2=  20.7 R=  39 x1= 9 y1= 2 z1= 8
        initial_data = ([-4.3, 20.7], [26.7, 94.3], [9, 2, 8], [39])

        for f in fields:
            d = initial_data[fields.index(f)]
            f.insert(d)

    @staticmethod
    def get_param(fields):
        """
        Извлекает данные их полей ввода и  преобразует в единый список.
        :params обобщеный список данных из полей ввода
        """
        params = list()
        # Return True if arg1 in itarable
        if isinstance(fields, collections.Iterable):
            for field in fields:
                data = field.get()

                if isinstance(data, collections.Iterable):
                    for num in data:
                        params.append(num)

                else:
                    params.append(data)

        else:
            num = fields.get()
            if num:
                params.append(num)

        return params

    def print(self, *data):
        self.data_log.insert(data)

    def run(self, list_of_params):
        """
        Запрашивает данные из списка параметров. 
        Проверяет корректность введенных данных.
        В случае неверных занчений выдает окно об ошибке.
        Если ввод корректен, вызывает расчет.
        Если в процессе расчета есть выводятся математические ошибки, выводится сообще.
        """

        data = self.get_param(list_of_params)
        if False in data:
            showinfo(title='Error', message=u'Некорректно введеные данные:')
        else:
            try:
                self.calculate(data)
            except Exception:
                showinfo(title='Error', message=u'Некорректно введеные данные:')

    def calculate(self, data):

        A1, A2, F1, F2, x1, y1, z1, R = data

        stepF = 34
        stepA = A2-A1
            # TODO Возможно тут стоит использовать целочисленное деление вместо округляения?
        Fit = round((F2-F1)/stepF)
        Ait = round((A2-A1)/stepA)

        Dict = dict()
        Dict["x1"] = []
        Dict["y1"] = []
        Dict["x2"] = []
        Dict["y2"] = []

        result =[]
        for k in range(Ait+1):
            for i in range(Fit+1):
                F = F1+stepF*i
                A = A1+stepA*k
                #print('F1= ', F1, 'F2= ', F2, 'A1= ', A1, 'A2= ', A2, 'R= ', R)
                
                # Его направляющие косинусы в сферических координатах (1):
                lK = cos(radians(F)) 
                mK = sin(radians(F))*cos(radians(A))
                nK = sin(radians(F))*sin(radians(A))
                a = pow((mK/lK),2)+1
                b = -2*(pow((mK/lK),2)*x1-(mK/lK)*y1)
                c = pow(((mK/lK)*x1-y1),2)-pow(R,2)
                                
                if F > 90:
                        X = (-0.5*b-sqrt(pow(0.5*b, 2)-a*c))/a
                elif F < 90:
                        X = (-0.5*b+sqrt(pow(0.5*b, 2)-a*c))/a
                Xc = X
                Yc = mK*(Xc-x1)/lK+y1
                Zc = (Xc-x1)*nK/lK+z1
                #print('F= ', F, 'A= ', A, 'R= ', R,'Xc= ', Xc, 'Yc= ', Yc, 'Zc= ', Zc)
                                # print('Xc= ', Xc, 'Yc= ', Yc, 'Zc= ', Zc)
                                # 2-ой Переход от цилиндра к плоскости
                                # Развернем цилиндр в плоскость, паралельную ZOY, при этом Yc сохраняется, те
                Yр = Zc
                L = atan(Xc/Yc)
                L = degrees(L)
                                # Координаты вдоль развертки окружности цилиндра
                Xp = 2*pi*R*L/360
                                # Yр, Xp - координаты точки на рзвертке цилиндра
                print('F= ', F, 'A= ', A, 'R= ', R, 'Xp= ', Xp, 'Yр= ', Yр)    
                self.print('F= ', F, 'A= ', A, 'R= ', R,'Xc= ', Xc, 'Yc= ', Yc, 'Zc= ', Zc, 'Xp= ', Xp, 'Yр= ', Yр)

                if k / 2 == 0:
                    
                    Dict["x1"].append(Xp)
                    Dict["y1"].append(Yр)

                else:
                    
                    Dict["x2"].append(Xp)
                    Dict["y2"].append(Yр)
            "я хочу получить два набора координат x,y-для одного i и для другого, чтобы потом получить две прямые и потом выделить из них крайние точки и соединить их"
        return (Dict)

    def create_window(self,list_of_params):
        data = self.get_param(list_of_params)
        Dict = self.calculate(data)
        for key, val in Dict.items():
            print(key, val)

            # Нарисуем одномерный график

        pylab.plot(Dict.get('x1'), Dict.get('y1'))
        pylab.plot(Dict.get('x2'), Dict.get('y2'))

        lx = [min(Dict.get('x1'))]+ [min(Dict.get('x2'))]
        print("lx=",lx)
        ly = [min(Dict.get('y1'))]+ [max(Dict.get('y2'))]

        pylab.plot(lx, ly)

        rx = [max(Dict.get('x1'))]+ [max(Dict.get('x2'))]

        ry = [max(Dict.get('y1'))]+ [min(Dict.get('y2'))]

        pylab.plot(rx, ry)
            # Покажем окно с нарисованным графиком
        pylab.show()

# если запушен как основной процесс, то будет выполняться следующие
if __name__ == '__main__':
    solar = SolarMain()
    solar.mainloop()
