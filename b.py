from Tkinter import *
myicon = Tk()

cv = Canvas(myicon,width=800, height=600,bg = 'white')

d = {1:'error',2:'hourglass',3:'info',4:'question',5:'warning',6:'gray12',7:'gray25',8:'gray50',9:'gray75'}
for i in d:
    cv.create_bitmap((10+i*20,200),bitmap = d[i])
	
cv.create_oval((2,2,110,110),fill = 'lightgreen')
cv.create_oval((100,10,105,55),fill = 'green')
cv.create_bitmap(120,160,bitmap = d[3])
cv.create_text((200,260),text = '^',
               anchor = W
               )

lst = [300, 240, 301, 320, 345, 400] 
cv.create_line(lst, fill='red')
cv.pack()
#myicon.iconify()
myicon.mainloop()
