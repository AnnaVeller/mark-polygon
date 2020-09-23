from PIL import Image, ImageTk
import json
import io
import copy
import os.path
from tkinter.ttk import Frame, Label, Combobox
from tkinter import filedialog as fd
from tkinter import Tk, Button, Label, Entry, Canvas, NW, scrolledtext, INSERT, WORD, ALL, SE, messagebox, N, S, E, W

# Please not less than 480x480
CANVAS_WIDTH = 480
CANVAS_HEIGHT = 480


class Poly:

    def __init__(self):
        super().__init__()
        self.color = "black"
        self.cords = []
        self.cords_percent = []
        self.name = "NULL"
        self.end = False    #дорисован ли полигон

    def to_rel_cords(self):     # переводит координаты канваса в относительные
        self.cords_percent.clear()
        for i in range(len(self.cords)):
            x = self.cords[i][0] / CANVAS_WIDTH
            y = self.cords[i][1] / CANVAS_HEIGHT
            x = round(x, 5)
            y = round(y, 5)
            self.cords_percent.append([x, y])

    def to_real_cords(self):  # переводит относительные координаты в координаты канваса
        self.cords.clear()
        for c in self.cords_percent:
            x = c[0] * CANVAS_WIDTH
            y = c[1] * CANVAS_HEIGHT
            self.cords.append([x, y])


class Mark(Frame):

    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.master.title("Разметка текста")
        self.master.resizable(True, True)
        self.file = None
        self.file_initial = None
        self.path_to_file = 'NULL'
        self.tmp_path = 'NULL'
        self.start_x = None
        self.start_y = None
        self.prev_x = None
        self.prev_y = None
        self.list_poly = []  # список полигонов
        self.fst_point = [0, 0]
        self.sec_point = [0, 0]

        self.c = Canvas(width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg="white")
        self.c.grid(column=0, row=2, columnspan=4, rowspan=4, sticky=N + S + W + E)

        self.lbl = Label(text="Polygons:")
        self.lbl.grid(column=4, row=1, columnspan=2, sticky=S)
        self.lbl2 = Label(text="Image")
        self.lbl2.grid(column=0, row=1, columnspan=6, sticky=W)
        self.txt_cords = scrolledtext.ScrolledText(width=55, height=25, wrap=WORD, bg="mintcream")
        self.txt_cords.grid(column=4, row=2, columnspan=2, sticky=N)
        self.txt_input = Entry(bg="mintcream")
        self.txt_input.grid(column=1, row=0, columnspan=2, sticky=N + S + W + E)
        self.txt_input.focus()

        self.combo = Combobox()
        self.combo['values'] = ('black', 'white', 'red', 'yellow', 'green', 'blue', 'gray', 'purple', 'cyan', 'lime')
        self.combo.current(0)  # установить вариант по умолчанию
        self.combo.grid(column=4, row=5, sticky=N)
        self.lbl3 = Label(text="Set color of polygon")
        self.lbl3.grid(column=4, row=4, sticky=S)
        self.lbl4 = Label(text="ATTENTION!\n"
                               "You must set color before draw polygon"
                               "\nOtherwise the color will remain the same")
        self.lbl4.grid(column=5, row=5, sticky=N+W)
        self.box = Combobox(width=15)
        self.box.grid(column=2, row=7, sticky=E)
        self.lbl5 = Label(text="Choose poly dor delete")
        self.lbl5.grid(column=2, row=6, sticky=S+E)

        self.ui()

    def open_image(self):
        format = os.path.splitext(self.tmp_path)[1]
        format = format.lower()
        if format == '.jpg' or format == '.png':
            self.path_to_file = self.tmp_path
            self.lbl2.configure(text=self.path_to_file)
            self.list_poly.clear()
            self.output_poly_cords()
            self.lbl2.configure(text=self.path_to_file)
            file = Image.open(self.path_to_file)
            self.file_initial = ImageTk.PhotoImage(file)
            file = file.resize((CANVAS_WIDTH, CANVAS_HEIGHT))
            self.file = ImageTk.PhotoImage(file)
            self.c.create_image(0, 0, image=self.file, anchor=NW)
        else:
            messagebox.showwarning(title='Предупреждение',
                                   message='Этот формат не поддерживается. Откройте jpg- или png-файл')

    def coordinates(self):
        cords = []
        colors = []
        rel_cords = []
        lst = self.list_poly
        for i in range(len(lst)):
            cords.append(lst[i].cords)
            colors.append(lst[i].color)
            rel_cords.append(lst[i].cords_percent)
        return colors, cords, rel_cords

    def check_point(self, x, y, poly):
        if len(poly.cords) != 0:
            i = 0  # проверяем только с первой точкой
            if (x - poly.cords[i][0])**2 + (y - poly.cords[i][1])**2 < 200:
                return poly.cords[i]
        return False

    def check_near_point(self, x, y, x1, y1):
        if (x-x1)**2 + (y-y1)**2 < 150:
            return True
        return False

    def output_poly_cords(self):
        lst = self.list_poly
        stroka = ''

        for i in range(len(lst)):
            lst[i].to_rel_cords()
            stroka = stroka + '%d %s ' % (i+1, lst[i].color) + str(lst[i].cords_percent) + 2 * '\n'
        self.txt_cords.delete("1.0", "end")
        self.txt_cords.insert(INSERT, stroka)

        tmp = []
        for k in range(len(self.list_poly)):
            tmp.append(k + 1)
        self.box['values'] = tuple(tmp)

    def find_point(self, x, y):
        lst = self.list_poly
        for i in range(len(lst)):
            for j in range(len(lst[i].cords)):
                if (x - lst[i].cords[j][0]) ** 2 + (y - lst[i].cords[j][1]) ** 2 < 100:
                    return i+1, j     # возвращает номер полигона в котором нашел близкую точку, номер точки
        return False, False

    def load(self, name):
        self.tmp_path = name
        format = os.path.splitext(name)[1]
        if format == '.json':
            self.list_poly.clear()
            with open(name) as f:
                cords = json.load(f)
            for i in range(len(cords["relative coordinates"])):
                poly = Poly()
                poly.name = i
                poly.cords_percent = cords["relative coordinates"][i]
                poly.to_real_cords()
                poly.color = cords['color'][i]
                poly.end = True
                self.list_poly.append(copy.copy(poly))
                del poly
            self.poly_draw()
            self.output_poly_cords()
        else:
            messagebox.showwarning(title='Предупреждение', message='Этот формат не поддерживается. Откройте json-файл')

    def poly_draw(self):

        lst = self.list_poly
        k_poly = len(lst)    # кол-во полигонов
        for i in range(k_poly):
            if lst[i].cords:
                self.point(lst[i].cords[0][0], lst[i].cords[0][1])
                self.c.create_text(lst[i].cords[0][0], lst[i].cords[0][1], text=i+1, font=36, anchor=SE, fill="red")
            k_line = len(lst[i].cords)
            color = lst[i].color
            for j in range(1, k_line):
                self.point(lst[i].cords[j - 1][0], lst[i].cords[j - 1][1])
                self.point(lst[i].cords[j][0], lst[i].cords[j][1])
                self.c.create_line(lst[i].cords[j - 1][0], lst[i].cords[j - 1][1], lst[i].cords[j][0], lst[i].cords[j][1], width=2,
                                   fill=lst[i].color)
            if lst[i].end:      #чтобы незаконченые фигуры не дорисовывались к первой точке
                self.c.create_line(lst[i].cords[k_line - 1][0], lst[i].cords[k_line - 1][1], lst[i].cords[0][0], lst[i].cords[0][1],
                               width=2, fill=lst[i].color)
                self.point(lst[i].cords[k_line - 1][0], lst[i].cords[k_line - 1][1])
                self.point(lst[i].cords[0][0], lst[i].cords[0][1])

    def point(self, x, y):
        r = 2
        self.c.create_oval(x - r, y - r, x + r, y + r, width=1, outline='black',  fill='black')
        self.c.create_oval(x - r, y - r, x + r, y + r, width=1, outline='black',  fill='black')

    def button_open(self):
        def clicked():
            self.tmp_path = os.path.abspath(self.txt_input.get())
            if os.path.exists(self.tmp_path):
                self.open_image()
            else:
                messagebox.showwarning(title='Предупреждение',
                                       message='Изображение с именем %s не нашлось' % self.tmp_path)
        btn = Button(width=15, text="Open", bg="lightcyan", command=clicked)
        btn.grid(column=3, row=0, sticky=W, padx=5)

    def button_choose(self):
        def clicked():
            name = fd.askopenfilename()
            self.tmp_path = os.path.abspath(name)
            self.open_image()
        btn = Button(width=15, text="Choose..", bg="lightcyan", command=clicked)
        btn.grid(column=0, row=0)

    def save_jpg(self):

        ps = self.c.postscript(colormode='color')
        # на этом месте скачать https://www.ghostscript.com/download/gsdnld.html
        # добавить путь+bin\ в переменную окружения и перезагрузить пк
        img = Image.open(io.BytesIO(ps.encode('utf-8')))
        name = os.path.splitext(self.path_to_file)[0] + '_mark.jpg'
        answer = False
        if os.path.exists(name):
            answer = messagebox.askyesno(title="Вопрос", message="У вас уже есть такое размеченное изображение.\n"
                                                         "Хотите его перезаписать?")
            if answer:
                img.save(name)
        else:
            img.save(name)

    def button_save_jpg(self):
        def clicked():
            self.save_jpg()
        btn = Button(width=15, text="Save jpg", bg="lightcyan", command=clicked)
        btn.grid(column=0, row=8)

    def save_json(self):
        cords = []
        colors = []
        rel_cords = []
        lst = self.list_poly
        for i in range(len(lst)):
            cords.append(lst[i].cords)
            colors.append(lst[i].color)
            rel_cords.append(lst[i].cords_percent)

        to_json = {'picture': self.path_to_file, 'color': colors, 'coordinates': cords,
                   'relative coordinates': rel_cords}
        name = os.path.splitext(self.path_to_file)[0] + '.json'

        if os.path.exists(name):
            answer = messagebox.askyesno(title="Вопрос", message="У вас уже есть такой файл разметки json.\n"
                                                         "Хотите его перезаписать?")
            if answer:
                with open(name, 'w') as f:  # w - перезаписать. a - дозаписать
                    json.dump(to_json, f)
        else:
            with open(name, 'w') as f:  # w - перезаписать. a - дозаписать
                json.dump(to_json, f)

    def button_save_json(self):
        def clicked():
            self.save_json()
        btn = Button(width=15, text="Save json", bg="lightcyan", command=clicked)
        btn.grid(column=0, row=7)

    def button_delete(self):
        def clicked():
            self.c.delete(ALL)
            self.list_poly.clear()
            self.c.create_image(0, 0, image=self.file, anchor=NW)
            self.output_poly_cords()
            self.prev_x = None
            self.prev_y = None

        btn = Button(width=15, text="Delete ALL", bg="tomato", command=clicked)
        btn.grid(column=3, row=8, sticky=W)

    def button_poly_draw(self):
        def clicked():
            name = fd.askopenfilename()
            self.load(name)
        btn = Button(width=15, text="Load from json", bg="lightcyan", command=clicked)
        btn.grid(column=1, row=7)

    def button_help(self):
        def clicked():
            stroka = 'ФАЙЛЫ ДЛЯ ЗАГРУЗКИ ДОЛЖНЫ ЛЕЖАТЬ В ТОМ ЖЕ МЕСТЕ ГДЕ И КОД\n\n' \
                     'Начало осей координат расположено в левом верхнем углу. ' \
                     'Шкала [0, 1]\n\n' \
                     '"Choose.." - выбрать фото из галереи \n\n' \
                     '"Open" - открыть фото по указанному пути\n\n' \
                     'Левая кнопка - поставить координату\n\n' \
                     'Чтобы выбрать цвет полигона - тыкай на цвет перед началом рисования полигона\n\n'\
                     'Чтобы завершить полигон жмякай на начальную точку.\n\n' \
                     'Для изменения местоположения точки - ' \
                     'зажимай правую кнопку мыши и тяни до необходимого места\n\n' \
                     'Двойной щелчок по правой кнопке мыши в месте нежелательной точки - и её нет\n\n' \
                     'Для удаления полигона - тыкай номер полигона и жмякай "Delete poly"\n' \
                     'Для удаления ПРЯМ ВСЕХ полигонов - "Delete ALL"\n\n' \
                     'Чтобы сохранить новое изображение - "Save jpg"\n' \
                     'Для сохранения файла разметки - жмякай "Save json"\n' \
                     'Чтобы сохранить сразу всё - жми "Save jpg&json"\n\n' \
                     'Чтобы нарисовать по имеющемуся файлу json-файл - тыкай на "Load from json"\n\n' \
                     'Если у тебя есть картинка и json с одинаковым названием ' \
                     'загружай что-нибудь из этого в кнопку "Load mark image"\n\n'

            messagebox.showinfo('HELP', stroka)
        btn = Button(width=15, text="HELP", bg="tomato", command=clicked, fg='white')
        btn.grid(column=5, row=0, sticky=E)

    def button_del_poly(self):
        def clicked():
            j = int(self.box.get()) - 1
            if len(self.list_poly) == ' ':
                self.prev_x = None
                self.prev_y = None
            else:
                if j >= 0 and j < len(self.list_poly):
                    self.list_poly.pop(j)
                    self.c.delete(ALL)
                    self.c.create_image(0, 0, image=self.file, anchor=NW)
                    self.poly_draw()
                    self.output_poly_cords()
        btn = Button(width=15, text="Delete poly", bg="tomato", command=clicked)
        btn.grid(column=3, row=7, sticky=W)

    def button_load_mark_pic(self):
        def clicked():
            name = fd.askopenfilename()
            format = os.path.splitext(name)[1]
            if format == '.json':
                pic_name_jpg = os.path.splitext(name)[0] + '.jpg'
                pic_name_png = os.path.splitext(name)[0] + '.png'
                if os.path.exists(pic_name_jpg):
                    self.tmp_path = pic_name_jpg
                    self.open_image()
                    self.load(name)
                else:
                    if os.path.exists(pic_name_png):
                        self.tmp_path = pic_name_png
                        self.open_image()
                        self.load(name)
                    else:
                        messagebox.showwarning(title='Предупреждение',
                                               message='Изображения с именем %s или %s не нашлись'
                                                       %(pic_name_jpg,pic_name_png))
            else:
                if format == '.jpg' or format == '.png':
                    json_name = os.path.splitext(name)[0] + '.json'
                    if os.path.exists(json_name):
                        self.tmp_path = name
                        self.open_image()
                        self.load(json_name)
                    else:
                        messagebox.showwarning(title='Предупреждение',
                                               message='Файл разметки %s не нашелся' % json_name)
                else:
                    messagebox.showwarning(title='Предупреждение',
                                           message='Этот формат не поддерживается. '
                                                   'Откройте jpg-, png-файл или json-файл.\n'
                                                   'Обратите внимание чтобы картинка разметилась '
                                                   'файлы должны иметь одинаковые имена')

        btn = Button(width=15, text="Load mark image", bg="lightcyan", command=clicked)
        btn.grid(column=1, row=8)

    def button_save_all(self):
        def clicked():
            self.save_jpg()
            self.save_json()
        btn = Button(width=15, text="Save jpg&json", bg="lightcyan", command=clicked)
        btn.grid(column=0, row=9)

    def click_poly(self, event):
        x = event.x
        y = event.y
        tmp = False
        if not self.prev_x:     # если у нас первая точка
            object_poly = Poly()
            self.list_poly.append(object_poly)
            object_poly.name = len(self.list_poly)
            object_poly.color = self.combo.get()
            object_poly.cords.append([x, y])
            self.c.create_text(x, y, text=object_poly.name, font=36, anchor=SE, fill="red")
            self.point(x, y)
            self.prev_x = x
            self.prev_y = y
        else:
            if self.check_near_point(x, y, self.prev_x, self.prev_y):
                pass     # если две точки рядом, не рисуем их
            else:
                object_poly = self.list_poly[-1]
                if len(object_poly.cords) > 2:
                    tmp = self.check_point(x, y, object_poly)  # проверка что нет точки рядом

        if tmp:
            # замыкаем фигуру
            self.prev_x = None
            self.prev_y = None
            object_poly.end = True
            #news_cords = '%d %s ' % (object_poly.name, object_poly.color) + str(object_poly.cords) + 2*'\n'
            self.output_poly_cords()

        else:
            if self.check_near_point(x, y, self.prev_x, self.prev_y):
                pass     # если две точки рядом, не рисуем их
            else:
                object_poly.cords.append([x, y])
                if len(object_poly.cords) != 1:
                    self.point(x, y)
                    self.prev_x = x
                    self.prev_y = y

    def move(self, event):
        x = event.x
        y = event.y
        r = 2
        self.c.delete(ALL)
        self.c.create_image(0, 0, image=self.file, anchor=NW)
        self.poly_draw()
        self.c.create_oval(x - r, y - r, x + r, y + r, width=2, fill="black")
        s = "Движение мышью {}x{}".format(x, y)
        self.master.title(s)

    def change(self, event):

        def output_cords(event):
            self.output_poly_cords()
            x1 = event.x
            y1 = event.y
            i_poly, j = self.find_point(x, y)
            if i_poly:
                i_poly -= 1
                poly = self.list_poly[i_poly]
            else:
                poly = False
            if poly:
                del poly.cords[j]
                poly.cords.insert(j, [x1, y1])
                self.poly_draw()

        x = event.x
        y = event.y
        r = 4
        i_poly, j = self.find_point(x, y)
        if i_poly:
            i_poly -=1
            poly = self.list_poly[i_poly]
        else:
            poly = False

        if poly:
            del poly.cords[j]
            poly.cords.insert(j, [x, y])
            self.poly_draw()
            self.c.bind('<ButtonRelease-3>', output_cords)

        poly.to_rel_cords()

    def del_point(self, event):
        x = event.x
        y = event.y
        i_poly, j = self.find_point(x, y)
        if i_poly:
            i_poly -= 1
            poly = self.list_poly[i_poly]
        else:
            poly = False
        if poly:
            if len(poly.cords) <= 3:
                poly.end = False
                poly.cords.clear()
                self.list_poly.pop(i_poly)
                self.prev_x = None
                self.prev_y = None
            else:
                del poly.cords[j]
            self.output_poly_cords()

    def ui(self):
        self.button_open()
        self.button_choose()
        self.button_save_jpg()
        self.button_save_json()
        self.button_delete()
        self.button_poly_draw()
        self.button_help()
        self.button_del_poly()
        self.button_load_mark_pic()
        self.button_save_all()
        self.c.bind('<Button-1>', self.click_poly)
        self.c.bind('<Motion>', self.move)
        self.c.bind('<B3-Motion>', self.change)
        self.c.bind('<Double-Button-3>', self.del_point)


def main():
    root = Tk()
    root.state('zoomed')
    frame = Mark(root)
    frame.grid()
    root.mainloop()


if __name__ == "__main__":
    main()
