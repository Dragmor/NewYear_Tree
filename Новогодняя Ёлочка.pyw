import tkinter
import tkinter as tk
import time
import os
import winsound
import threading
import random
import multiprocessing

#==============================================================================#
timer_hide = True # True - не отображать таймер до НГ при запуске. False - 
# при запуске скрипта будет показано время в секундах до НГ.
sounds = True # при запуске включать воспроизведение рандомной мелодии
script_speed = 100 # общая скорость скрипта (0-100) Если работает медленно,
# увеличивай значение
festoon_speed = 10 # скорость мигания гирлянды (0-100)
snow_limit = 100 # сколько максимум снежинок может падать одновременно
snows_spawn_persent = 20 # процент интенсивности выпадения снежинок (0-100)
snows_h_speed = 10 # скоррость горизонтальных колебаний (0-максимальная скорость)
snows_flutter = 3 # амплитуда дрожания снега при падении (0 - без колебаний)
snows_angle = 0.3 # угол падения снега (0 - под прямым углом). Рандом в диапазоне
snow_falling_speed = 2 # скорость падения снега (1-минимальная) (чем выше, 
# тем быстрее, но тем сильнее рывки при движении)
alpha = 0.91 # прозрачность. 0.5 - полупрозрачные элементы. 1 - непрозрачные
#==============================================================================#

def start_play(loop=False, fname='', *args):
        '''в цикле воспроизводит музыку с названием fname'''
        while loop: #если нужно играть в цикле
            winsound.PlaySound(fname, winsound.SND_ALIAS) #запуск воспроизведения
        winsound.PlaySound(fname, winsound.SND_ALIAS)

class GUI:
    """
    класс графического интерфейса
    """

    def __init__(self):
        """
        конструктор класса. Содержит настройки графического окна
        """

        self.window_title = "Dragmor_NewYearTree" # имя приложения
        self.sound_process = multiprocessing.Process()
        self.window_width = 0  # ширина окна
        self.window_height = 0 # высота окна
        self.window_x = None      # положение главного окна по X
        self.window_y = None      # положение главного окна по Y
        self.tree_images = [] # список изображений для анимации ёлочки
        self.sounds = [] # список музыки
        self.is_moved = False
        if sounds == True:
            self.mute = False # включена ли музыка
        else:
            self.mute = True
        self.alpha_col = 'gray' # цвет, который будет прозрачным

        self.dragging_flag = None # флаг для перетаскивания гл. окна мышью
        self.clicked_x = 0        # переменные для перемещения
        self.clicked_y = 0        # окна мышью

        self.window = None # переменная для записи в неё окна (tkinter.Tk())
        self.festoon_anim = self.load_festoon_anim()
        self.create_window()  # задаю окну параметры и отрисовываю его
        
    def load_festoon_anim(self):
        '''
        метод загружает поведение гирлянды. Возвращает список очерёдности
        кадров гирлянды.
        '''
        try:
            file = open('source/festoon', 'r')
            alg = file.read()
            file.close()
            alg = alg.split('-')
            processed_anim_frames = []
            for _ in alg:
                processed_anim_frames.append(int(_))
            return processed_anim_frames
        except:
            print('Error: не удалось загрузить анимацию гирлянды!')
            return False


    def create_window(self):
        """
        метод отрисовки графического окна приложения
        """
        self.window = tkinter.Tk()

        self.configure_main_window() # конфигурирую гл. окно (положение и т.д.)
        self.load_images()
        self.load_sounds()
        self.create_ui_elements()    # расставляю управляющие элементы
        self.binding_elements()      # бинд элементов управления
        self.snow = SnowGenerator(self.window, self.canvas, self.window_width,
            self.window_height)
        self.tree_animation = SpruceTreeAnimation(len(self.festoon_anim)-1,
            self.festoon_anim)
        if self.festoon_anim == False:
            self.tree_animation.animated = False
        self.animation_thread()      # поток действий 
        self.timer = NewYearTimer(self.canvas, self.window_width,
            self.window) # таймер до НГ
        if self.mute == False:
            self.next_sound()
        self.window.mainloop()       # зацикливаю обработку событий

    def configure_main_window(self):
        '''метод для настройки главного окна'''
        # выставляю при запуске главное окно на середину экрана
        self.window_x = 0
        self.window_y = 0

        self.window_width = self.window.winfo_screenwidth()
        self.window_height = self.window.winfo_screenheight()
        # отключаю стандартные элементы окна
        self.window.overrideredirect(True)
        self.window.wm_attributes('-topmost', True) # поверх всех окон
        self.window.wm_attributes("-toolwindow", False) # в виде панели инструментов
        self.window.configure(background='blue') #цвет окна
        self.window.wm_attributes('-transparentcolor', self.alpha_col) # делаю белый цвет прозрачным 
        self.window.wm_attributes('-alpha', alpha) # половина прозрачности
        self.window.focus_force() # принудятельно перевожу фокус на окно
        # задаю размеры и положение окна
        self.window.geometry("=%sx%s+%s+%s" 
            %(self.window_width, self.window_height, 
             self.window_x, self.window_y))
        # создаю холст
        self.canvas = tkinter.Canvas(self.window, 
            bg="white", highlightthickness=0, 
            takefocus=1, width=self.window_width,  
            height=self.window_height, background=self.alpha_col)

    def load_images(self):
        '''
        метод загружает в списки изображения
        '''
        # открываю папку с изображениями, заполняю списки картинок
        for f in os.listdir('img'):
            if 'tree_main' in f:
                self.main_tree_image = tk.PhotoImage(file='img/%s' %f)
            elif 'tree' in f:
                self.tree_images.append(tk.PhotoImage(file='img/%s' %f))

    def load_sounds(self):
        for s in os.listdir('sounds'):
            if '.wav' in s:
                self.sounds.append('sounds/%s' %s)

    def create_ui_elements(self):
        """
        метод расставляет пользовательские элементы 
        """
        # создаю главное изображение
        self.canvas.create_image(self.window_width-self.tree_images[0].width()//2, 
            self.window_height-self.tree_images[0].height()//2,
            image=self.tree_images[0], tag='main')
        # расстановка элементов
        self.canvas.pack(side='right', anchor='n')

    def binding_elements(self):
        """
        метод биндит элементы управления
        """
        self.canvas.tag_bind('main', "<Button-1>", self.mouse_event)
        self.canvas.tag_bind('main', "<ButtonRelease-1>", self.mouse_event)
        self.canvas.tag_bind('main', "<Button-2>", self.on_off_sound)
        self.canvas.tag_bind('main', "<Button-3>", self.on_off_festoon)
        self.window.bind("<MouseWheel>", self.next_sound)
        self.canvas.tag_bind('main', "<ButtonRelease-1>", self.mouse_event)
        self.canvas.tag_bind('main', "<Motion>", self.drag_object)

        
        self.dragging_flag = False  # флаг перетаскивания ёлочки

    def on_off_sound(self, *args):
        if self.mute == True:
            self.mute = False
            self.next_sound()
        else:
            self.mute = True
            if self.sound_process.is_alive():
                self.sound_process.terminate()


    def next_sound(self, *args):
        if self.mute == True:
            return
        if self.sound_process.is_alive():
            self.sound_process.terminate()
        fname = self.sounds[random.randint(0, len(self.sounds)-1)]
        self.sound_process = multiprocessing.Process(target=start_play, args=(True, fname))
        self.sound_process.daemon = True
        self.sound_process.start()

    

    def mouse_event(self, event):
        """
        метод для обработки собития мыши
        """
    
        # если была нажата ЛКМ
        if event.state == 8:
            # включаю флаг режима перетаскивания окна
            self.dragging_flag = True
            self.clicked_x = (self.window.winfo_pointerx()
                -self.canvas.coords('main')[0])
            self.clicked_y = (self.window.winfo_pointery()
                -self.canvas.coords('main')[1])
        elif event.state == 264:
            if self.is_moved == False:
                self.timer.hide_timer()
            self.dragging_flag = False
            self.is_moved = False

    def on_off_festoon(self, *args):
        '''
        Метод включения/отключения мигания гирлянды
        '''
        if self.tree_animation.festoon() == False:
            self.canvas.itemconfigure('main', image=self.main_tree_image)

    def drag_object(self, event):
        """
        метод для перетаскивания елки
        """
        if self.dragging_flag:
            self.is_moved = True
            self.window_x = self.window.winfo_pointerx()-self.clicked_x
            self.window_y = self.window.winfo_pointery()-self.clicked_y
            # двигаю изображение с тегом main на холсте
            self.canvas.move('main',
                -self.canvas.coords('main')[0]+self.window_x, 
                -self.canvas.coords('main')[1]+self.window_y)

    def animation_thread(self):
        '''
        метод для запуска генератора действий в отдельном потоке
        '''
        thread = threading.Thread(target=self.main_thread)
        thread.daemon = True
        thread.start()

    def main_thread(self):
        '''
        метод воспроизведения анимации
        '''
        while True:
            self.tree_animation.tree_animate(self.canvas, self.tree_images)
            time.sleep(1/script_speed)
            snows_persent = random.randint(1, 100)
            if snows_persent <= snows_spawn_persent:
                self.snow.spawn(random.randint(0, 1))
            self.snow.snow_processing()



class SpruceTreeAnimation():
    '''
    Класс обработки мигания гирлянды елочки
    '''
    def __init__(self, total_frames, festoon_anim):
        self.total_frames = total_frames #сколько всего кадров
        self.current_frame = 0 # номер текущего кадра
        self.animation_count = 0 # счётчик
        self.animated = True # флаг, что гирлянда включена
        self.festoon_anim = festoon_anim

    def tree_animate(self, canvas, tree_images):
        '''
        метод анимации гирлянды
        '''
        if self.animated == False:
            return
        if self.animation_count < festoon_speed:
            self.animation_count += 1
            return
        self.animation_count = 0
        canvas.itemconfigure('main', image=tree_images[self.festoon_anim[self.current_frame]])
        self.current_frame += 1
        if self.current_frame > self.total_frames:
            self.current_frame = 0

    def festoon(self):
        '''метод включает/выключает гирлянду
        '''
        if self.animated == True:
            self.animated = False
            return False
        else:
            self.animated = True
            return True


class SnowGenerator():
    def __init__(self, window, canvas, screen_width, screen_height):
        self.window = window
        self.canvas = canvas
        self.canvas.tag_bind('dropped', '<Button-1>', self.clear_dropped_snows)
        self.canvas.tag_bind('snow', '<Enter>', self.delete_snow)
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.snow_list = [] # список тегов падающих снежинок
        self.dropped_snows = [] # список упавших снежинок
        self.snow_count = 0 # счётчик снежинок
        self.snow_max_speed = 1
        self.load_images()

    def clear_dropped_snows(self, *args):
        self.canvas.delete('dropped')
        # очищаю координаты выпавшего снега
        self.dropped_snows = []

    def delete_snow(self, event):
        '''
        удаляю падающую снежинку, если на неё был направлен курсор мыши
        '''
        self.canvas.delete(self.canvas.find_enclosed(
            self.window.winfo_pointerx()-5,
            self.window.winfo_pointery()-5,
            self.window.winfo_pointerx()+5,
            self.window.winfo_pointery()+5))

    def load_images(self):
        '''
        метод загружает в списки изображения
        '''
        self.snow_images = [] # список изображений для анимации
        # открываю папку с изображениями, заполняю списки картинок
        for f in os.listdir('img'):
            if 'snow' in f:
                self.snow_images.append(tk.PhotoImage(file='img/%s' %f))
                if self.snow_images[-1].width() > self.snow_max_speed:
                    self.snow_max_speed = self.snow_images[-1].width()

    def spawn(self, count=10):
        '''
        метод спавнит снежинки
        '''
        for i in range(count):
            # добавляю в список снежинку
            snow_image = random.randint(0, len(self.snow_images)-1)
            speed=self.snow_images[snow_image].width()
            speed=random.uniform(speed-0.3, speed+0.3)
            #
            self.snow_list.append(Snow(self.snow_count,
            self.snow_images[snow_image],
            speed,
            random.randint(0, snows_flutter)))
            # для пересоздания снежинок, если их слишком много
            try:
                self.canvas.delete('snow_%s' %self.snow_list[-1].snow_id)
            except:
                pass
            # создаю снежинку
            self.canvas.create_image(random.randint(0, self.screen_width),
                0,
                image=self.snow_list[-1].image,
                tag='snow_%s' %self.snow_list[-1].snow_id)
            self.canvas.addtag_withtag('snow', 'snow_%s' %self.snow_list[-1].snow_id)
            self.snow_count+=1
            # обнуляю счётчик снежинок после лимита
            if self.snow_count > snow_limit:
                # удаляю половину координат упавших снежинок
                self.snow_count = 0

    def snow_processing(self):
        '''
        метод падения снега
        '''

        delete_snow = []
        # соновной цикл обработки падения снежинок
        for s in self.snow_list:
            # проверка на накладывание одной снежинки на другую
            try:
                x = int(self.canvas.coords('snow_%s' %s.snow_id)[0])
                y = int(self.canvas.coords('snow_%s' %s.snow_id)[1]+1)
            except:
                continue
            if ('%s/%s' %(x,y)) in self.dropped_snows:
                delete_snow.append(s)
                # удаляю координаты снежинки, на которую упала другая
                self.dropped_snows.remove('%s/%s' %(x,y))
                continue

            # падение снежинки
            if s.check_falled(self.canvas, self.screen_height) == True:
                delete_snow.append(s)
            else:
                s.falling(self.canvas, self.snow_max_speed)
        # вношу координаты упавших снежинок в список
        for d in delete_snow:
            try:
                x = int(self.canvas.coords('snow_%s' %d.snow_id)[0])
                y = int(self.canvas.coords('snow_%s' %d.snow_id)[1])-(1-d.image.height())
            except:
                continue
            self.snow_list.remove(d)
            if ('%s/%s' %(x, y)) not in self.dropped_snows:
                self.dropped_snows.append('%s/%s' %(x, y))
            self.canvas.itemconfig('snow_%s' %d.snow_id, tag='dropped')


class Snow():
    '''
    Класс снежинок
    '''
    def __init__(self, snow_id, image, speed, flutter):
        self.snow_id = snow_id
        self.image = image
        self.speed = speed
        self.flutter_amplitude = flutter
        if flutter == 0:
            self.angle = random.uniform(-snows_angle, snows_angle)*self.speed
        else:
            self.angle = 0
        self.direction = random.randint(0, 1)
        self.current_flutter = 0
        self.flutter_counter = 0
        self.horizontal_counter = 0

    def flutter(self):
        '''
        метод для дрожания снежинки влево-вправо
        '''
        if self.flutter_amplitude != 0:
            if self.horizontal_counter != snows_h_speed:
                self.horizontal_counter += 1
                return 0
            else:
                self.horizontal_counter = 0
                if self.flutter_amplitude != abs(self.current_flutter):
                    if self.direction == 0:
                        self.current_flutter-=1
                    else:
                        self.current_flutter+=1
                    self.flutter_counter +=1
                else:
                    if self.direction == 0:
                        self.direction = 1
                        self.current_flutter+=1
                    else:
                        self.direction = 0
                        self.current_flutter-=1
                if self.current_flutter < 0:
                    return -1
                elif self.current_flutter > 0:
                    return 1
                else:
                    return 0
        else:
            return 0

    def falling(self, canvas, max_speed):
        '''
        метод падения снежинки
        '''
        canvas.move('snow_%s' %self.snow_id, self.flutter()+self.angle,
        self.speed/max_speed*snow_falling_speed)


    def check_falled(self, canvas, screen_height):
        '''
        метод проверяет, упала-ли снежинка. Если да, возвращает true
        '''
        # проверка на выход снежинки за пределы экрана
        if canvas.coords('snow_%s' %self.snow_id)[1] >= screen_height-self.image.height():
            canvas.moveto('snow_%s' %self.snow_id,
                int(canvas.coords('snow_%s' %self.snow_id)[0]),
                screen_height-self.image.height())
            return True


class NewYearTimer():
    '''
    класс часов, отсчитывающих время до Нового Года
    '''
    def __init__(self, canvas, screen_width, window):
        self.hide = timer_hide
        self.window = window
        self.canvas = canvas
        self.screen_width = screen_width
        self.dragging_flag = False
        self.load_images()
        self.bind_event()
        thread= threading.Thread(target=self.timer_thread)
        thread.daemon=True
        thread.start()
                
    def load_images(self):
        '''
        метод загружает изображения цифр и заднего фона для таймера
        '''
        self.digits = []
        for _ in range(10):
            self.digits.append(tk.PhotoImage(file='img/digits/%s.png' %_))
        count = 0
        for _ in range(7):
            self.canvas.create_image(
                self.screen_width/2-(6*self.digits[_].width())/2+count*self.digits[_].width(),
                self.digits[_].height()/1.8,
                image=None,
                tag='digit_%s' %count)
            self.canvas.addtag_withtag('digit', 'digit_%s' %count)
            count += 1


    def bind_event(self):
        self.canvas.tag_bind('digit', "<Button-1>", self.mouse_event)
        self.canvas.tag_bind('digit', "<ButtonRelease-1>", self.stop_dragging)
        self.canvas.tag_bind('digit', "<Motion>", self.drag_object)

    def stop_dragging(self, event):
        self.dragging_flag = False

    def mouse_event(self, event):
        """
        метод для обработки собития мыши
        """
    
        # если была нажата ЛКМ
        if event.state == 8:
            # включаю флаг режима перетаскивания окна
            self.dragging_flag = True
            self.clicked_x = (self.window.winfo_pointerx()
                -self.canvas.coords('digit')[0])
            self.clicked_y = (self.window.winfo_pointery()
                -self.canvas.coords('digit')[1])
        else:
            self.dragging_flag = False

    def drag_object(self, event):
        """
        метод для перетаскивания таймера
        """
        if self.dragging_flag:
            self.window_x = self.window.winfo_pointerx()-self.clicked_x
            self.window_y = self.window.winfo_pointery()-self.clicked_y
            # двигаю изображение с тегом main на холсте
            self.canvas.move('digit',
                -self.canvas.coords('digit')[0]+self.window_x, 
                -self.canvas.coords('digit')[1]+self.window_y)

    def timer_thread(self):
        while True:
            if self.hide == False:
                count = 0
                c_time = self.current_time()
                if c_time == False and self.hide == False:
                    self.hide = True
                    continue
                for _ in c_time:
                    self.canvas.itemconfigure('digit_%s' %count, image=self.digits[int(_)])
                    count+=1
                time.sleep(0.3)
                continue
            

            time.sleep(0.1)

    def current_time(self):
        '''
        возвращает время до НГ, либо False, если до НГ больше месяца
        '''
        if time.localtime().tm_yday <= 1:
            return '0000000'
        if time.localtime().tm_mon != 12:
            return False
        else:
            days = 365-time.localtime().tm_yday
            hours = 23-time.localtime().tm_hour
            minutes = 60-time.localtime().tm_min
            seconds = 60-time.localtime().tm_sec
            # высчитываю, сколько секунд до НГ
            seconds_to_new_year = str((days*24*60+hours*60+minutes)*60+seconds)
            seconds_to_new_year = '0'*(7-len(seconds_to_new_year))+seconds_to_new_year
            return seconds_to_new_year

    def hide_timer(self):
        if self.hide == False:
            self.canvas.itemconfigure('digit', image='')
            self.hide = True
        else:
            self.hide = False




if __name__ == "__main__":
    MainWindow = GUI()



'''
СДЕЛАТЬ
5)салюты в НОВЫЙ ГОД
'''