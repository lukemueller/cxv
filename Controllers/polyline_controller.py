from Models import polyline_model as pl
import wx

class Controller():

    def __init__(self, dicom_controller, dicom_view, background):
        self.dicom_controller = dicom_controller
        self.dicom_view = dicom_view
        self.canvas = self.dicom_view.canvas
        self.axes = self.dicom_view.axes
        self.background = background
        self.drag_v = False
        self.drag_pl = False
        self.prev_event = None
        self.tmp_line = None
        self.picked = None
        self.connect = False
        self.polylines = []
        self.curr_pl = None
        self.color_map = {'Red' : '#FF0000',
                          'Green' : '#00FF00',
                          'Blue' : '#0000FF',
                          'Yellow' : '#FFFF00',
                          'Purple' : '#FF00FF',
                          'White' : '#FFFFFF',
                          'Black' : '#000000'}
    
    def on_mouse_motion(self, event):
        if len(self.polylines) == 0: return
        if event.inaxes == self.dicom_view.ov_axes:
            event.xdata += self.dicom_controller.coral_slab[0]
            event.ydata += self.dicom_controller.coral_slab[1]
        if self.drag_v:
            self.drag_vertex(event)
        elif self.drag_pl:
            self.drag_polyline(event)
        elif self.connect:
            x, = self.curr_pl.verticies[-1].get_xdata()
            y, = self.curr_pl.verticies[-1].get_ydata()
            self.tmp_line, = self.axes.plot([x, event.xdata], [y, event.ydata],
                                    c='#00FF00', marker='-',
                                    zorder=1, animated=True)
        self.prev_event = event
        try: self.curr_pl.set_label(self.polylines.index(self.curr_pl))
        except: pass
    
    def on_mouse_press(self, event):
        if event.inaxes == self.dicom_view.ov_axes:
            event.xdata += self.dicom_controller.coral_slab[0]
            event.ydata += self.dicom_controller.coral_slab[1]
        if event.button == 1:
            self.on_left_click(event)
        elif event.button == 3:
            self.on_right_click(event)
            
    def on_mouse_release(self, event):
        self.drag_v = False
        self.drag_pl = False
            
    def on_left_click(self, event):
        if self.on_pick(event): return
        if self.connect:
            self.append_tmp_line()
        else:
            self.curr_pl = pl.Polyline(self, self.axes)
            self.polylines.append(self.curr_pl)
            self.connect = True
            self.dicom_controller.changed = True
            
        self.curr_pl.add_vertex(event.xdata, event.ydata)
            
    def on_right_click(self, event):
        if self.connect:
            self.tmp_line = None
            self.connect = False
            self.curr_pl.color = '#FF0000'
            self.curr_pl.set_colors()
            self.validate()
        elif self.on_pick(event):
            self.dicom_controller.draw_all()
            if self.picked.contains(event)[0]:
                self.mpl_event = event
                self.create_popup_menu(self.curr_pl.is_line(self.picked))
                
    def on_pick(self, event):
        self.picked = None
        for polyline in self.polylines:
            for line in polyline.lines:
                if line.contains(event)[0]:
                    self.picked = line
                    self.curr_pl = polyline
                    self.drag_pl = True
            for vertex in polyline.verticies:
                if vertex.contains(event)[0]:
                    self.picked = vertex
                    self.curr_pl = polyline
                    self.drag_v = True
        if not self.picked: return False
        else: return True
        
    def delete_polyline(self, event):
        self.drag_v = False
        self.drag_pl = False
        self.dicom_controller.changed = True
        self.polylines.remove(self.curr_pl)
        for i in range(len(self.polylines)):
            self.polylines[i].set_label(i)

    def add_vertex(self, event):
        self.drag_v = False
        self.drag_pl = False
        self.dicom_controller.changed = True
        line_index = self.curr_pl.get_line_index(self.picked)
        new_line = self.curr_pl.insert_line(line_index+1, [0,0], [0,0])
        new_vertex = self.curr_pl.insert_vertex(line_index+1,
                                                self.mpl_event.xdata,
                                                self.mpl_event.ydata)
        self.curr_pl.set_line(self.picked, 
                              [self.picked.get_xdata()[0], self.mpl_event.xdata],
                              [self.picked.get_ydata()[0], self.mpl_event.ydata])
        v = self.curr_pl.get_vertex(line_index+2)
        self.curr_pl.set_line(new_line,
                              [self.mpl_event.xdata, v.get_xdata()[0]],
                              [self.mpl_event.ydata, v.get_ydata()[0]])
        self.picked = new_vertex
        self.curr_pl.set_colors()

    def delete_vertex(self, event):
        self.drag_v = False
        self.drag_pl = False
        self.dicom_controller.changed = True
        if self.curr_pl.is_first(self.picked):
            self.curr_pl.remove_vertex(0)
            self.curr_pl.remove_line(0)
        elif self.curr_pl.is_last(self.picked):
            self.curr_pl.verticies.pop()
            self.curr_pl.lines.pop()
        else:
            vertex_index = self.curr_pl.get_vertex_index(self.picked)
            self.curr_pl.remove_vertex(vertex_index)
            self.curr_pl.remove_line(vertex_index-1)
            l = self.curr_pl.get_line(vertex_index-1)
            v = self.curr_pl.get_vertex(vertex_index-1)
            self.curr_pl.set_line(l,
                                  [v.get_xdata()[0], l.get_xdata()[1]], 
                                  [v.get_ydata()[0], l.get_ydata()[1]])
        self.validate()
        
    def set_color(self, event):
        self.drag_v = False
        self.drag_pl = False
        color = self.menu.FindItemById(event.GetId()).GetItemLabel()
        self.curr_pl.color = self.color_map[color]
        self.curr_pl.set_colors()
                
    def append_tmp_line(self):
        self.curr_pl.add_line(self.tmp_line.get_xdata(), self.tmp_line.get_ydata())
        self.tmp_line = None
        
    def validate(self):
        if self.curr_pl.is_alone():
            self.polylines.remove(self.curr_pl)
            self.curr_pl = None
        
    def drag_vertex(self, event):
        self.dicom_controller.changed = True
        i = self.curr_pl.get_vertex_index(self.picked)
        self.curr_pl.set_vertex(self.picked, event.xdata, event.ydata)
        if not self.curr_pl.is_first(self.picked):
            line = self.curr_pl.get_line(i-1)
            self.curr_pl.set_line(line,
                                  [line.get_xdata()[0], event.xdata],
                                  [line.get_ydata()[0], event.ydata])
        if not self.curr_pl.is_last(self.picked):
            line = self.curr_pl.get_line(i)
            self.curr_pl.set_line(line,
                                  [event.xdata, line.get_xdata()[1]],
                                  [event.ydata, line.get_ydata()[1]])
            
    def drag_polyline(self, event):
        self.dicom_controller.changed = True
        x_offset = event.xdata - self.prev_event.xdata
        y_offset = event.ydata - self.prev_event.ydata
        for line in self.curr_pl.lines:
            x1, x2 = line.get_xdata()
            y1, y2 = line.get_ydata()
            x1 += x_offset
            x2 += x_offset
            y1 += y_offset
            y2 += y_offset
            self.curr_pl.set_line(line,
                                  [x1, x2],
                                  [y1, y2])
        for vertex in self.curr_pl.verticies:
            x, = vertex.get_xdata()
            y, = vertex.get_ydata()
            x += x_offset
            y += y_offset
            self.curr_pl.set_vertex(vertex, x, y)    
        
    def draw_polylines(self, adjustable, locked):
        if self.tmp_line: self.axes.draw_artist(self.tmp_line)
        for polyline in self.polylines:
            for line in polyline.lines:
                self.axes.draw_artist(line)
            if adjustable:
                for vertex in polyline.verticies:
                    self.axes.draw_artist(vertex)
            self.axes.draw_artist(polyline.label)
                
    def create_popup_menu(self, line):
        if not self.picked: return
        self.menu = wx.Menu()
        if line:
            for each in self.popup_line_data():
                self.add_option(self.menu, *each)
        else:
            for each in self.popup_vertex_data():
                self.add_option(self.menu, *each)
        color_menu = wx.Menu()
        for each in self.popup_color_data():
            self.add_option(color_menu, *each)
        self.menu.AppendMenu(-1, 'color', color_menu)
        try: self.dicom_view.PopupMenu(self.menu)
        except: pass    # avoid C++ assertion error
        self.menu.Destroy()
        
    def add_option(self, menu, label, handler):
        option = menu.Append(-1, label)
        self.dicom_view.Bind(wx.EVT_MENU, handler, option)
        
    def popup_line_data(self):
        label = 'delete polyline ' + self.curr_pl.get_label()
        return [('add vertex here', self.add_vertex),
                (label, self.delete_polyline)
                ]
        
    def popup_vertex_data(self):
        label = 'delete polyline ' + self.curr_pl.get_label()
        return [('delete vertex', self.delete_vertex),
                (label, self.delete_polyline)
                ]
        
    def popup_color_data(self):
        return [
                ('Red', self.set_color),
                ('Green', self.set_color),
                ('Blue', self.set_color),
                ('Yellow', self.set_color),
                ('Purple', self.set_color),
                ('White', self.set_color),
                ('Black', self.set_color)
                ]