import curses
import locale

locale.setlocale(locale.LC_ALL, '')
coding = locale.getpreferredencoding()

class UnicodeAdditions(object):

    VERTICAL = {
        1: u'\u2581',
        2: u'\u2582',
        3: u'\u2583',
        4: u'\u2584',
        5: u'\u2585',
        6: u'\u2586',
        7: u'\u2587',
        8: u'\u2588',
        "seperator": u'\u2500',
    }

    HORIZONTAL = {
        1: u'\u258F',
        2: u'\u258E',
        3: u'\u258D',
        4: u'\u258C',
        5: u'\u258B',
        6: u'\u258A',
        7: u'\u2589',
        8: u'\u2588',
    }

    def __init__(self):
        pass

class Bar(UnicodeAdditions):

    def __init__(self, height, width, y_pos, x_pos, screen):
        self.height = height
        self.width = width
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.window = self.create_window()
        self.fill_percentage = {105: curses.color_pair(0)}
        self.categories = ['fill', 'border', 'seperator', 'title', 'text']
        self.color = {}
        for cat in self.categories:
            self.color[cat] = curses.color_pair(0)
        curses.init_pair(1, curses.COLOR_RED, -1)
        curses.init_pair(2, curses.COLOR_GREEN, -1)
        curses.init_pair(3, curses.COLOR_YELLOW, -1)
        curses.init_pair(4, curses.COLOR_BLUE, -1)
        curses.init_pair(5, curses.COLOR_WHITE, -1)
        curses.init_pair(6, curses.COLOR_BLACK, -1)
        self.RED = curses.color_pair(1)
        self.GREEN = curses.color_pair(2)
        self.YELLOW = curses.color_pair(3)
        self.BLUE = curses.color_pair(4)
        self.WHITE = curses.color_pair(5)
        self.BLACK = curses.color_pair(6)
        self.colors()

    def colors(self):
        pass

    def create_window(self):
        return curses.newwin(
            self.height,
            self.width,
            self.y_pos,
            self.x_pos
        )

    def update_window(self, title, values, offset=0):
        self.window.clear()
        self.draw_border()
        self.update_bars(title, values, offset)
        self.window.refresh()

    def set_colors(self, dict_o_colors):
        grab = ["border", "seperator", "title", "text"]
        for key in grab:
            try:
                self.color[key] = dict_o_colors[key]
            except:
                print "The category '%s' is not valid." % key

    def set_fill_percentage(self, dictionary): 
        self.fill_percentage = dictionary

    def get_color(self, value, percentage=None):
        if value != "fill":
            return self.color[value]
        else:
            return self.get_fill_color(percentage)

    def get_fill_color(self, percentage):
        keys = self.fill_percentage.keys()
        keys.sort()
        for key in keys:
            if key >= percentage:
                return self.fill_percentage[key]
        return -1


class HorizontalBar(Bar):

    def draw_border(self):
        width = self.width - 2
        top =    u'\u250F' + u'\u2501' * width + u'\u2513'
        bottom = u'\u2517' + u'\u2501' * width + u'\u251B' 
        self.window.addstr(0, 0, top.encode(coding), self.color["border"])
        try:
            self.window.addstr(self.height - 1, 0, bottom.encode(coding), self.color["border"]) 
        except curses.error:
            pass
        self.window.move(0, 0)

    def update_bars(self, title, values, offset):
        width = self.width - 4
        levels = width * 8
        i = 0
        for title, percent in values.iteritems():
            if i != 0:
                seperator = self.VERTICAL["seperator"] * (self.width - 4)
                self.window.addstr(offset + i - 1, 2, seperator.encode(coding),
                                   self.get_color("seperator"))
            value = percent / 100 * levels
            full_bars = int(value / 8)
            part_bar = int(value) % 8
            bar = full_bars * self.HORIZONTAL[8]
            if part_bar != 0:
                bar += self.HORIZONTAL[part_bar]
            self.window.addstr(offset + i, 2, title.encode(coding), self.get_color("title"))
            self.window.addstr(offset + i + 1, 2, bar.encode(coding), self.get_color("fill", percent))
            i += 3

class HorizontalText(Bar):

    def draw_border(self):
        width = self.width - 2
        top =    u'\u250F' + u'\u2501' * width + u'\u2513'
        bottom = u'\u2517' + u'\u2501' * width + u'\u251B' 
        self.window.addstr(0, 0, top.encode(coding), self.color["border"])
        try:
            self.window.addstr(self.height - 1, 0, bottom.encode(coding), self.color["border"]) 
        except curses.error:
            pass
        self.window.move(0, 0)

    def update_bars(self, title, values, offset):
        width = self.width - 4
        i = 0
        for title, text in values.iteritems():
            if i != 0:
                seperator = self.VERTICAL["seperator"] * (self.width - 4)
                self.window.addstr(offset + i - 1, 2, seperator.encode(coding),
                                   self.get_color("seperator"))
            self.window.addstr(offset + i, 2, title.encode(coding), self.get_color("title"))
            self.window.addstr(offset + i + 1, 2, text.encode(coding), self.get_color("text"))
            i += 3
            

class VerticalBar(Bar):

    def draw_border(self):
        width = self.width - 2 
        top =    u'\u250F' + u'\u2501' * width + u'\u2513'
        bottom = u'\u2517' + u'\u2501' * width + u'\u251B' 
        self.window.addstr(0, 0, top.encode(coding), self.get_color("border"))
        try:
            self.window.addstr(self.height - 1, 0, bottom.encode(coding), self.get_color("border"))
        except curses.error:
            pass
        self.window.move(0, 0)

    def update_bars(self, title, values, offset):
        height = self.height - 5
        levels = height * 8
        i = 0
        for footer, percent in values.iteritems():
            value = percent / 100 * levels
            footer = footer[0]
            full_bars = int(value / 8)
            part_bar = int(value) % 8
            x_offset, y_offset = (2, -1)
            x = (i * 2) + x_offset
            for j in range(0, full_bars):
                y = j + y_offset
                self.window.addstr(height - y, x, self.VERTICAL[8].encode(coding), self.get_color("fill", percent))
            if part_bar != 0:
                self.window.addstr(height - full_bars - y_offset, x, self.VERTICAL[part_bar].encode(coding), self.get_color("fill", percent))
            seperator = self.VERTICAL["seperator"] * (self.width - 4)
            self.window.addstr(self.height - 3, 2, seperator.encode(coding), self.get_color("seperator"))
            self.window.addstr(self.height - 2, x, footer.encode(coding), self.get_color("title"))
            i += 1 
        self.window.addstr(1, x_offset, title, self.get_color("title"))
