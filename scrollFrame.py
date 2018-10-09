try:
	import Tkinter
	import ttk
except:
	import tkinter as Tkinter
	from tkinter import ttk

class VerticalScrolledFrame(Tkinter.Frame):
    """A pure Tkinter scrollable frame that actually works!
    * Use the 'interior' attribute to place widgets inside the scrollable frame
    * Construct and pack/place/grid normally
    * This frame only allows vertical scrolling

    """
    def __init__(self, parent, *args, **kw):
        Tkinter.Frame.__init__(self, parent, *args, **kw)            
        
        # create a canvas object and a vertical scrollbar for scrolling it
        vscrollbar = ttk.Scrollbar(self, orient=Tkinter.VERTICAL)
        vscrollbar.pack(fill=Tkinter.Y, side=Tkinter.RIGHT, expand=Tkinter.FALSE)
        self.canvas = canvas = Tkinter.Canvas(self, bd=0, highlightthickness=0,
                        yscrollcommand=vscrollbar.set,*args, **kw)
        canvas.pack(side=Tkinter.LEFT, fill=Tkinter.BOTH, expand=Tkinter.TRUE)
        vscrollbar.config(command=canvas.yview)
        
        # reset the view
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)
        
        # create a frame inside the canvas which will be scrolled with it
        self.__to_destroy = False
        self.interior = interior = Tkinter.Frame(canvas)
        interior_id = canvas.create_window(0, 0, window=interior,
                                           anchor=Tkinter.NW)

        # track changes to the canvas and frame width and sync them,
        # also updating the scrollbar
        def _configure_interior(event):
            #print('config',event.__dict__)
            if self.__to_destroy is True:
                return
            # update the scrollbars to match the size of the inner frame
            req_width,req_height,canvas_width = interior.winfo_reqwidth(), interior.winfo_reqheight(), canvas.winfo_width()
            canvas.config(scrollregion="0 0 %s %s" % (req_width,req_height))
            #print (req_width,req_height,canvas_width, canvas.winfo_height())
            if req_height > canvas.winfo_height():
                # update the canvas's width to fit the inner frame
                canvas.config(width=req_width,height=req_height)
            elif req_width != canvas_width:
                # update the inner frame's width to fill the canvas
                canvas.config(width=req_width)
        interior.bind('<Configure>', _configure_interior)
        
        def _configure_canvas(event):
            if self.__to_destroy is True:
                return
            #print ('canvas',interior.winfo_reqwidth(),interior.winfo_reqheight(),canvas.winfo_height())
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the inner frame's width to fill the canvas
                canvas.itemconfigure(interior_id, width=canvas.winfo_width())
        canvas.bind('<Configure>', _configure_canvas)
    def Scroll(self,event):
            self.canvas.yview_scroll(-1*(event.delta//120), "units")
    def destroy(self):
            self.__to_destroy = True
            self.interior.destroy()
