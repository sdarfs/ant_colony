#!/usr/bin/python
import argparse

import ut
import tkinter as tk
from copy import copy
from random import choice, randrange, randint
from tkinter import *
import tomllib
from tkinter import messagebox

with open("config.toml", mode="rb") as fp:
    _CONFIG_ = tomllib.load(fp)

global e_w, e_h, move_tab
e_w = _CONFIG_['environment']['width']
e_h = _CONFIG_['environment']['height']

pheromones = []

STEP_SIZE = _CONFIG_['ant']['stepsize']
STEP_GRID = ut.cp((-1 * STEP_SIZE, 0, STEP_SIZE), (-1 * STEP_SIZE, 0, STEP_SIZE))
STEP_GRID.remove((0, 0))

move_tab = STEP_GRID
class Nest:
    def __init__(self, canvas):
        self.canvas = canvas
        self.posx = randrange(50, 150)
        self.posy = randrange(50, 150)
        self.radius = 10
        self.display = circle(self.posx, self.posy, self.radius, canvas,
                              _CONFIG_['graphics']['nest']['colour'])
        self.food_storage = _CONFIG_['nest']['ini_foodqty']

    def feed_ant(self, ant):
        desired_energy_topup = _CONFIG_['ant']['ini_energy'] - ant.energy
        actual_energy_topup = min(desired_energy_topup, self.food_storage)
        self.food_storage -= actual_energy_topup
        return actual_energy_topup


class Food:
    def __init__(self, canvas):
        self.life = 100

        self.posx = randrange(80, 160)
        self.posy = randrange(80, 150)
        self.display = circle(self.posx, self.posy, randint(10, 25), canvas, "#83aa6b")

    def replace(self, canvas):
        old_posx = self.posx
        old_posy = self.posy
        self.posx = randrange(120, 250)
        self.posy = randrange(180, 350)
        canvas.move(self.display, self.posx - old_posx, self.posy - old_posy)
        self.life = 100


class Pheromone:
    def __init__(self, ant, canvas):
        self.posx = ant.posx
        self.posy = ant.posy
        self.life = _CONFIG_['pheromone']['persistence']
        self.display = circle(self.posx, self.posy, _CONFIG_['graphics']['pheromone']['radius'], canvas,
                              _CONFIG_['graphics']['pheromone']['colour'])


class Insects:
    def __init__(self, nest, canvas):
        self.canvas = canvas
        self.posx = nest.posx
        self.posy = nest.posy
        self.display = circle(self.posx, self.posy, _CONFIG_['graphics']['insects']['radius'], self.canvas,
                              _CONFIG_['graphics']['insects']['scouting_colour'])
        self.scout_mode = True
        self.energy = _CONFIG_['insects']['energy']

    def remove_from_display(self):
        self.canvas.delete(self.display)


class Ant(Insects):
    def __init__(self, nest, canvas):
        super().__init__(nest, canvas)
        self.display = circle(self.posx, self.posy, _CONFIG_['graphics']['ant']['radius'], self.canvas,
                              _CONFIG_['graphics']['ant']['scouting_colour'])
        self.energy = _CONFIG_['ant']['ini_energy']


class AntBuilder(Ant):
    def __init__(self, nest, canvas):
        super().__init__(nest, canvas)
        self.display = circle(self.posx, self.posy, _CONFIG_['graphics']['ant']['radius'], self.canvas,
                              _CONFIG_['graphics']['ant']['builder_colour'])

        self.energy = _CONFIG_['ant']['ini_energy']


class AntWarrior(Ant):
    def __init__(self, nest, canvas):
        super().__init__(nest, canvas)
        self.display = circle(self.posx, self.posy, _CONFIG_['graphics']['ant']['radius'], self.canvas,
                              _CONFIG_['graphics']['ant']['warrior_colour'])

        self.energy = _CONFIG_['ant']['ini_energy']


class Environment:
    def __init__(self, ant_number, ant_make_count, ant_warrior_count, mode, root):
        super().__init__()
        self.ant_number = ant_number
        self.ant_make = ant_make_count
        self.ant_warrior = ant_warrior_count
        self.window = root
        self.mode = mode
        self.sim_loop = 0

        self.environment = tk.Canvas(
            self.window, width=e_w, height=e_h, background=_CONFIG_['graphics']['environment']['backgroundcolour'])
        self.environment.grid(column=0, row=0, columnspan=6)

        self.status_vars = [StringVar() for i in range(8)]
        _ = [var.set(f'Ini ({i}) ...') for i, var in enumerate(self.status_vars)]
        _ = [Label(self.window, textvariable=var).grid(column=i, row=1, sticky='nw') for i, var in
             enumerate(self.status_vars[:4])]
        _ = [Label(self.window, textvariable=var).grid(column=i, row=2, sticky='nw') for i, var in
             enumerate(self.status_vars[4:])]

        # btn = Button(self.window, text='Стоп').grid(column=4, row=2, sticky='nw')

        # Initialization of the nest
        self.nest = Nest(self.environment)

        # Initialization of the food
        self.food = Food(self.environment)

        self.ant_data = [Ant(self.nest, self.environment, ) for i in range(self.ant_number)]
        self.antBuilder_data = [AntBuilder(self.nest, self.environment) for i in range(self.ant_make)]
        self.antWarrior_data = [AntWarrior(self.nest, self.environment) for i in range(self.ant_warrior)]
        # self.spider_data = [Spider(self.environment, self.nest) for i in range(self.spider)]

        self.environment.after(
            1, self.move_forever())

        self.window.mainLoop()

    def move_forever(self):
        while 1:
            self.f_move()

    def f_move(self):
        """Simulates the movements ants
        """
        self.sim_loop += 1

        for pheromone in pheromones:
            # At each loop the life expectancy of pheromones decreases by 1
            pheromone.life -= 1
            if pheromone.life <= 0:  # If the life expectancy of a pheromone reaches 0 it is removed
                self.environment.delete(pheromone.display)
                pheromones.remove(pheromone)
        if self.nest.food_storage > _CONFIG_['ant']['energy_to_create_new_ant']:
            ch = randint(1, 3)
            if ch == 1:
                number_new_ants = int(self.nest.food_storage // _CONFIG_['ant']['energy_to_create_new_ant'])
                self.ant_data = self.ant_data + [Ant(self.nest, self.environment) for i in range(number_new_ants)]
                self.nest.food_storage -= number_new_ants * _CONFIG_['ant']['energy_to_create_new_ant']
            elif ch == 2:
                number_new_ants_w = int(self.nest.food_storage // _CONFIG_['ant']['energy_to_create_new_ant'])
                self.antWarrior_data = self.antWarrior_data + [AntWarrior(self.nest, self.environment) for i in
                                                               range(number_new_ants_w)]
                self.nest.food_storage -= number_new_ants_w * _CONFIG_['ant']['energy_to_create_new_ant']
            else:
                number_new_ants_b = int(self.nest.food_storage // _CONFIG_['ant']['energy_to_create_new_ant'])
                self.antBuilder_data = self.antBuilder_data + [AntBuilder(self.nest, self.environment) for i in
                                                               range(number_new_ants_b)]
                self.nest.food_storage -= number_new_ants_b * _CONFIG_['ant']['energy_to_create_new_ant']
        if len(self.ant_data) + len(self.antWarrior_data) + len(self.antBuilder_data) == 0:
            print("Муравьи погибли.\nВыход из программы...")
            exit(0)

        for ant in self.ant_data:
            if sim_args.mode == 'basic':
                ant.energy -= 0.001
                if ant.energy <= 0:
                    ant.remove_from_display()
                    self.ant_data = [an_ant for an_ant in self.ant_data if an_ant is not ant]
                    continue

            if ant.scout_mode:
                if ant.posx <= 0 or ant.posy <= 0 or ant.posx >= e_w - 1 or ant.posy >= e_h - 1:
                    coord = choice(dont_out(ant))
                else:

                    coord = pheromones_affinity(ant, self.environment, len(self.ant_data))
                    if not coord:
                        coord = move_tab
                    coord = choice(coord)

                ant.posx += coord[0]
                ant.posy += coord[1]
                self.environment.move(ant.display, coord[0], coord[1])

                collision = collide(self.environment, ant)
                if collision == 2:
                    self.food.life -= 1
                    self.environment.itemconfig(self.food.display, fill="#83aa6b")
                    ant.energy = _CONFIG_['ant']['ini_energy']

                    if self.food.life < 1:
                        self.food.replace(self.environment)
                        self.environment.itemconfig(self.food.display, fill="#83aa6b")
                    ant.scout_mode = False
                    self.environment.itemconfig(ant.display, fill=_CONFIG_['graphics']['ant']['notscouting_colour'])

                    _ = [pheromones.append(Pheromone(ant, self.environment))
                         for i in range(_CONFIG_['pheromone']['qty_ph_upon_foodfind'])]

                elif collision == 1:
                    ant.energy += self.nest.feed_ant(ant)


            else:
                coord = choice(find_nest(ant, self.environment, len(self.ant_data)))
                proba = choice([0] * 23 + [1])
                if proba:
                    pheromones.append(Pheromone(ant, self.environment))
                ant.posx += coord[0]
                ant.posy += coord[1]
                self.environment.move(ant.display, coord[0], coord[1])
                if collide(self.environment, ant) == 1:
                    ant.scout_mode = True
                    self.environment.itemconfig(ant.display, fill=_CONFIG_['graphics']['ant']['scouting_colour'])

                    self.nest.food_storage += 1

                    ant.energy += self.nest.feed_ant(ant)

            if len(self.ant_data) <= 100:
                self.environment.update()

        for ant_b in self.antBuilder_data:
            ant_b.energy -= 0.003
            if ant_b.energy <= 0:
                ant_b.remove_from_display()
                self.antBuilder_data = [an_ant_b for an_ant_b in self.antBuilder_data if an_ant_b is not ant_b]
                continue

            if ant_b.scout_mode:
                if ant_b.posx <= 0 or ant_b.posy <= 0 or ant_b.posx >= e_w - 1 or ant_b.posy >= e_h - 1:
                    coord = choice(dont_out(ant_b))
                else:
                    coord = pheromones_affinity(ant_b, self.environment, len(self.antBuilder_data))
                    if not coord:
                        coord = move_tab
                    coord = choice(coord)

                ant_b.posx += coord[0]
                ant_b.posy += coord[1]
                self.environment.move(ant_b.display, coord[0], coord[1])

                collision = collide(self.environment, ant_b)

                if collision == 2:
                    self.food.life -= 5
                    self.environment.itemconfig(self.food.display, fill="#83aa6b")
                    ant_b.energy = _CONFIG_['ant']['ini_energy']

                    # Если еда была перемещена
                    if self.food.life < 1:
                        self.food.replace(self.environment)
                        self.environment.itemconfig(self.food.display, fill="#83aa6b")
                    ant_b.scout_mode = False
                    self.environment.itemconfig(ant_b.display, fill=_CONFIG_['graphics']['ant']['notscouting_colour'])
                    _ = [pheromones.append(Pheromone(ant_b, self.environment))
                         for i in range(_CONFIG_['pheromone']['qty_ph_upon_foodfind'])]
                elif collision == 1:
                    ant_b.energy += self.nest.feed_ant(ant_b)
                    # если муравей "коснулся" еды, то образуется связь

            else:  # если муравьишка нашел еду
                coord = choice(find_nest(ant_b, self.environment, len(self.antBuilder_data)))
                proba = choice([0] * 23 + [1])
                if proba:
                    pheromones.append(Pheromone(ant_b, self.environment))
                ant_b.posx += coord[0]
                ant_b.posy += coord[1]
                self.environment.move(ant_b.display, coord[0], coord[1])

                if collide(self.environment, ant_b) == 1:
                    ant_b.scout_mode = True
                    self.environment.itemconfig(ant_b.display, fill=_CONFIG_['graphics']['ant']['builder_colour'])
                    self.nest.food_storage += 5
                    ant_b.energy += self.nest.feed_ant(ant_b)
            if (self.nest.food_storage) // 10 > ant_b.energy:
                self.nest.radius += 20

            if len(self.antBuilder_data) <= 100:
                self.environment.update()


        for ant_w in self.antWarrior_data:
            if sim_args.mode == 'basic':
                ant_w.energy -= 0.001
                if ant_w.energy <= 0:
                    ant_w.remove_from_display()
                    self.antWarrior_data = [an_ant for an_ant in self.antWarrior_data if an_ant is not ant_w]
                    continue

            if ant_w.scout_mode:
                if ant_w.posx <= 0 or ant_w.posy <= 0 or ant_w.posx >= e_w - 1 or ant_w.posy >= e_h - 1:
                    coord = choice(dont_out(ant_w))
                else:

                    coord = pheromones_affinity(ant_w, self.environment, len(self.antWarrior_data))
                    if not coord:
                        coord = move_tab
                    coord = choice(coord)

                ant_w.posx += coord[0]
                ant_w.posy += coord[1]
                self.environment.move(ant_w.display, coord[0], coord[1])

                collision = collide(self.environment, ant_w)
                if collision == 2:
                    self.food.life -= 1
                    self.environment.itemconfig(self.food.display, fill="#83aa6b")
                    ant_w.energy = _CONFIG_['ant']['ini_energy']

                    if self.food.life < 1:
                        self.food.replace(self.environment)
                        self.environment.itemconfig(self.food.display, fill="#83aa6b")
                    ant_w.scout_mode = False
                    self.environment.itemconfig(ant_w.display, fill=_CONFIG_['graphics']['ant']['notscouting_colour'])

                    _ = [pheromones.append(Pheromone(ant_w, self.environment))
                         for i in range(_CONFIG_['pheromone']['qty_ph_upon_foodfind'])]

                elif collision == 1:
                    ant_w.energy += self.nest.feed_ant(ant_w)


            else:
                coord = choice(find_nest(ant_w, self.environment, len(self.antWarrior_data)))
                proba = choice([0] * 23 + [1])
                if proba:
                    pheromones.append(Pheromone(ant_w, self.environment))
                ant_w.posx += coord[0]
                ant_w.posy += coord[1]
                self.environment.move(ant_w.display, coord[0], coord[1])
                if collide(self.environment, ant_w) == 1:
                    ant_w.scout_mode = True
                    self.environment.itemconfig(ant_w.display, fill=_CONFIG_['graphics']['ant']['warrior_colour'])

                    self.nest.food_storage += 1

                    ant_w.energy += self.nest.feed_ant(ant_w)

            if len(self.antWarrior_data) <= 100:
                self.environment.update()

        # Подсчет средней энергии
        avg_energy, avg_energy_builder, avg_energy_warrior, avg_energy_spider = 0, 0, 0, 0
        if len(self.ant_data) > 0:
            avg_energy = sum([an_ant.energy for an_ant in self.ant_data]) / len(self.ant_data)
        if len(self.antBuilder_data) > 0:
            avg_energy_builder = sum([an_ant.energy for an_ant in self.antBuilder_data]) / len(self.antBuilder_data)
        if len(self.antWarrior_data) > 0:
            avg_energy_warrior = sum([an_ant.energy for an_ant in self.antWarrior_data]) / len(self.antWarrior_data)

        self.status_vars[0].set(f'Добытчиков еды: {len(self.ant_data)}')
        self.status_vars[1].set(f'Строителей: {len(self.antBuilder_data)}')
        self.status_vars[2].set(f'Разведчиков: {len(self.antWarrior_data)}')
        self.status_vars[3].set(f'Запас еды: {self.nest.food_storage:.2f}')
        self.status_vars[4].set(f'Энергия добытчиков: {avg_energy:.2f}')
        self.status_vars[5].set(f'Энергия строителей: {avg_energy_builder:.2f}')
        self.status_vars[6].set(f'Энергия разведчиков: {avg_energy_warrior:.2f}')
        self.status_vars[7].set(f'Количество несобранной еды: {self.food.life}')


def circle(x, y, radius, canvas, color):
    """Функция рисования круга"""
    return canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill=color, outline='')


def collide(canvas, ant):
    """
        Returns 1 если муравей в гнезде
        Returns 2 если муравей нашел еду/паука
        """
    ant_coords = canvas.coords(ant.display)
    if canvas.find_overlapping(ant_coords[0], ant_coords[1], ant_coords[2], ant_coords[3])[0] == 1:
        return 1
    elif canvas.find_overlapping(ant_coords[0], ant_coords[1], ant_coords[2], ant_coords[3])[0] == 2:
        return 2
    else:
        return 0


def dont_out(ant):
    new_move_tab = copy(move_tab)
    # if not 0<= ant.posx <= e_w or 0 <= ant.posy <= e_h:
    abs_grid = [(pos[0] + ant.posx, pos[1] + ant.posy) for pos in new_move_tab]
    new_move_tab = [(pos[0] - ant.posx, pos[1] - ant.posy) for pos in abs_grid if
                    (0 <= pos[0] <= e_w and 0 <= pos[1] <= e_h)]
    return new_move_tab

def find_nest(ant, canvas, ant_num):
    ant_coords = (ant.posx, ant.posy)
    HG_o = canvas.find_overlapping(0, 0, ant_coords[0], ant_coords[1])
    HD_o = canvas.find_overlapping(e_w, 0, ant_coords[0], ant_coords[1])
    BG_o = canvas.find_overlapping(0, e_h, ant_coords[0], ant_coords[1])
    BD_o = canvas.find_overlapping(e_w, e_h, ant_coords[0], ant_coords[1])
    HGn = HG_o[0]
    HDn = HD_o[0]
    BGn = BG_o[0]
    BDn = BD_o[0]

    HG = len(HG_o) - 2 - ant_num
    HD = len(HD_o) - 2 - ant_num
    BG = len(BG_o) - 2 - ant_num
    BD = len(BD_o) - 2 - ant_num

    new_move_tab = []
    if HGn == 1:
        if not HG > 1:
            new_move_tab += [(-1*STEP_SIZE, 0), (0, -STEP_SIZE), (-1*STEP_SIZE, -1*STEP_SIZE)]
        else:
            new_move_tab += [(-1*STEP_SIZE, 0), (0, -STEP_SIZE), (-1*STEP_SIZE, -1*STEP_SIZE)] * HG
    if HDn == 1:
        if not HD > 1:
            new_move_tab += [(STEP_SIZE, 0), (0, -1*STEP_SIZE), (STEP_SIZE, -1*STEP_SIZE)]
        else:
            new_move_tab += [(STEP_SIZE, 0), (0, -1*STEP_SIZE), (STEP_SIZE, -1*STEP_SIZE)] * HD
    if BGn == 1:
        if not BG > 1:
            new_move_tab += [(-1*STEP_SIZE, 0), (0, STEP_SIZE), (-1*STEP_SIZE, STEP_SIZE)]
        else:
            new_move_tab += [(-1*STEP_SIZE, 0), (0, STEP_SIZE), (-1*STEP_SIZE, STEP_SIZE)] * BG
    if BDn == 1:
        if not BD > 1:
            new_move_tab += [(STEP_SIZE, 0), (0, STEP_SIZE), (STEP_SIZE, STEP_SIZE)]
        else:
            new_move_tab += [(STEP_SIZE, 0), (0, STEP_SIZE), (STEP_SIZE, STEP_SIZE)] * BD
    if len(new_move_tab) > 0:
        return new_move_tab
    return move_tab

def pheromones_affinity(ant, canvas, ant_num):
    """Returns a new movement table for which there will be a high probability of approaching pheromones

    """
    if pheromones == []:
        return []
    ant_coords = (ant.posx, ant.posy)

    HG_o = canvas.find_overlapping(0, 0, ant_coords[0], ant_coords[1])
    HD_o = canvas.find_overlapping(e_w, 0, ant_coords[0], ant_coords[1])
    BG_o = canvas.find_overlapping(0, e_h, ant_coords[0], ant_coords[1])
    BD_o = canvas.find_overlapping(e_w, e_h, ant_coords[0], ant_coords[1])
    HG = len(HG_o) - (2 + ant_num)
    HD = len(HD_o) - (2 + ant_num)
    BG = len(BG_o) - (2 + ant_num)
    BD = len(BD_o) - (2 + ant_num)
    new_move_tab = []

    if HG > 1:
        new_move_tab += [(-1*STEP_SIZE, 0), (0, -1*STEP_SIZE), (-1*STEP_SIZE, -1*STEP_SIZE)] * HG

    if HD > 1:
        new_move_tab += [(STEP_SIZE, 0), (0, -1*STEP_SIZE), (STEP_SIZE, -1*STEP_SIZE)] * HD

    if BG > 1:
        new_move_tab += [(-1*STEP_SIZE, 0), (0, STEP_SIZE), (-1*STEP_SIZE, STEP_SIZE)] * BG

    if BD > 1:
        new_move_tab += [(STEP_SIZE, 0), (0, STEP_SIZE), (STEP_SIZE, STEP_SIZE)] * BD

    return new_move_tab




class mainWindow:
    def __init__(self, mode):
        self.root = Tk()
        self.root.geometry('300x350')
        self.root.geometry('300x350')
        self.root.title('Создание муравьиной фермы')
        self.mode = mode

        tk.Label(self.root, text='Добытчики еды:').place(x=10, y=10)
        tk.Label(self.root, text="Строители: ").place(x=10, y=40)
        tk.Label(self.root, text="Разведчики: ").place(x=10, y=70)

        val = StringVar()
        val1 = StringVar()
        val2 = StringVar()

        ant_field = tk.Spinbox(from_=0.0, to=100.0, textvariable=val)  # (self.root, textvariable=val)
        ant_field.place(x=120, y=10, width=66)

        ant_make_field = tk.Spinbox(from_=0.0, to=100.0, textvariable=val1)
        ant_make_field.place(x=120, y=40, width=66)

        ant_war_field = tk.Spinbox(from_=0.0, to=100.0, textvariable=val2)
        ant_war_field.place(x=120, y=70, width=66)
        mainmenu = Menu(self.root)
        self.root.config(menu=mainmenu)
        filemenu = Menu(mainmenu, tearoff=0)

        def clicked():
            messagebox.showinfo('Муравиная ферма', 'Чтобы начать работу с программой необходимо ввести количество муравьев от 0 до 100 и нажать кнопку "Ок"')
        filemenu.add_command(label="Выход", command=self.root.destroy)

        helpmenu = Menu(mainmenu, tearoff=0)
        helpmenu.add_command(label="О программе",command=clicked)


        mainmenu.add_cascade(label="Файл", menu=filemenu)
        mainmenu.add_cascade(label="Справка", menu=helpmenu)





        def secondWindow(val_, val1_, val2_):
            window = tk.Tk()
            window.title('Муравьиная колония')
            window.bind("<Escape>", lambda quit: window.destroy())

            val = int(val_.get())
            val1 = int(val1_.get())
            val2 = int(val2_.get())
            Environment(val, val1, val2, mode, window)


        def create_new_window(event):
            self.root.destroy()
            secondWindow(val, val1, val2)

        but = Button(self.root, text='Ok')
        but.bind('<Button->', create_new_window)
        but.pack(anchor=S, padx=10, pady=100)
        self.root.mainloop()



if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser(
            prog='Colony ant simulator',
            description='Simulation of ants colony.'
        )
        parser.add_argument('-m', dest='mode', nargs='?', default='basic', choices=['basic', 'reality'],
                        help='Simulation mode (default: "reality")')
        sim_args = parser.parse_args()
        mainWindow(sim_args.mode)

    except KeyboardInterrupt:
        print("Exiting...")
        exit(0)

# for ant_builder in self.antBuilder_data:
#    ant_builder.energy -=0.001
#    if ant_builder.energy <= 0:
#        ant_builder.remove_from_display()
#        self.anBuilder_data = [an_ant for an_ant in self.antBuilder_data if an_ant is not ant_builder]
#        continue
#
#    if ant_builder.posx <= 0 or ant_builder.posy <= 0 or ant_builder.posx >= e_w - 1 or ant_builder.posy >= e_h - 1:
#        coord = choice(dont_out_ant(ant_builder))
#    else:
#        coord = pheromones_affinity(ant_builder, self.environment, len(self.ant_data))
#        if not coord:
#            coord = move_tab_ant
#        coord = choice(coord)
#
#    ant_builder.posx += coord[0]
#    ant_builder.posy += coord[1]
#    self.environment.move(ant_builder.display, coord[0], coord[1])
#    if self.nest.food_storage > 55:
#            self.nest.radius += 1
#
# for ant_warrior in self.antWarrior_data:
#    ant_warrior.energy -= 0.001
#    if ant_warrior.energy <= 0:
#        ant_warrior.remove_from_display()
#        self.antWarrior_data = [an_ant for an_ant in self.antWarrior_data if an_ant is not ant_warrior]
#        continue
#    if ant_warrior.posx <= 0 or ant_warrior.posy <= 0 or ant_warrior.posx >= e_w - 1 or ant_warrior.posy >= e_h - 1:
#        coord = choice(dont_out_ant(ant_warrior))
#    else:
#        coord = pheromones_affinity(ant_warrior, self.environment, len(self.ant_data))
#        if not coord:
#            coord = move_tab_ant
#        coord = choice(coord)
#
#    ant_warrior.posx += coord[0]
#    ant_warrior.posy += coord[1]
#    self.environment.move(ant_warrior.display, coord[0], coord[1])
#
#    collision = collide(self.environment, ant_warrior)
#
#    if collision == 2:
#        self.w_food.life -= 1
#        self.environment.itemconfig(self.food.display, fill="#83aa6b")
#        ant_warrior.energy = _CONFIG_['ant']['war_energy']
#
#        # Если еда была перемещена
#        if self.w_food.life < 1:
#            self.w_food.replace(self.environment)
#            self.environment.itemconfig(self.w_food.display, fill="#83aa6b")
#    elif collision == 1:
#        ant_warrior.energy += self.nest.feed_ant(ant_warrior)
#        # если муравей "коснулся" еды, то образуется связь
#    _ = [pheromones.append(Pheromone(ant_warrior, self.environment))
#         for i in range(_CONFIG_['pheromone']['qty_ph_upon_foodfind'])]
#
#    coord = choice(find_nest(ant_warrior, self.environment, len(self.antWarrior_data)))
#    proba = choice([0] * 23 + [1])
#    if proba:
#        pheromones.append(Pheromone(ant_warrior, self.environment))
#    ant_warrior.posx += coord[0]
#    ant_warrior.posy += coord[1]
#    self.environment.move(ant_warrior.display, coord[0], coord[1])
#
#    if collide(self.environment, ant_warrior) == 1:
#
#        self.nest.food_storage += 5
#        ant_warrior.energy += self.nest.feed_ant(ant_warrior)
#
#
# for spider in self.spider_data:
#    spider.energy -= 0.001
#    if spider.energy <= 0:
#        spider.remove_from_display()
#        self.spider_data = [a_spider for a_spider in self.spider_data if a_spider is not spider]
#        continue
#   #if spider.posx <= 0 or spider.posy <= 0 or spider.posx >= e_w - 1 or spider.posy >= e_h - 1:
#   #    #coord = choice(dont_out_ant(spider))
#   #else:
#   #    coord = pheromones_affinity_for_ants(spider, self.environment, len(self.spider_data))
#   #    if not coord:
#   #        coord = move_tab_spider
#   #    coord = choice(coord)
#    coord = choice(dont_out(spider))
#    spider.posx += coord[0]
#    spider.posy += coord[1]
#    self.environment.move(spider.display, coord[0], coord[1])
#
#    collision = collide(self.environment, spider)
#
#    if collision == 1:
#        self.nest.food_storage -= 1
#        spider.energy += 1
#        # Если гнездо было перемещено
#        if self.nest.food_storage <= 0:
#            self.nest.replace(self.environment)
#
#    _ = [pheromones.append(Pheromone(spider, self.environment))
#             for i in range(_CONFIG_['pheromone']['qty_ph_upon_foodfind'])]

# class Spider(Insects):
#    def __init__(self, canvas, nest):
#        super().__init__(canvas, nest)
#        self.canvas = canvas
#        self.posx = randint(0, 500)
#        self.posy = randint(0, 500)
#        self.display = circle(self.posx, self.posy, _CONFIG_['graphics']['spider']['radius'], self.canvas,
#                              _CONFIG_['graphics']['spider']['colour'])
#        self.energy = _CONFIG_['spider']['energy']
#
