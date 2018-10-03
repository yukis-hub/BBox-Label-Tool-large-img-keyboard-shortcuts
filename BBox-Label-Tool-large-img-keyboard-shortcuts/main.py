#-------------------------------------------------------------------------------
# Name:        Object bounding box label tool
# Purpose:     Label object bboxes for ImageNet Detection data
# Author:      Qiushi
# Created:     06/06/2014

#
#-------------------------------------------------------------------------------
from __future__ import division
from Tkinter import *
import tkMessageBox
from PIL import Image, ImageTk
import ttk
import os
import glob
import random
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

# colors for the bboxes
COLORS = ['red', 'blue', 'olive', 'teal', 'cyan', 'green', 'black']
# image sizes for the examples
SIZE = 100,80

WINDOW_SIZE = 400

class LabelTool():
    def __init__(self, master):
        # set up the main frame
        self.parent = master
        self.parent.title("LabelTool")
        self.frame = Frame(self.parent)
        self.frame.pack(fill=BOTH, expand=1)
        self.parent.resizable(width = FALSE, height = FALSE)

        # initialize global state
        self.imageDir = ''
        self.imageList= []
        self.egDir = ''
        self.egList = []
        self.outDir = ''
        self.cur = 0
        self.total = 0
        self.category = 0
        self.imagename = ''
        self.labelfilename = ''
        self.tkimg = None
        self.currentLabelclass = ''
        self.cla_can_temp = []
        self.classcandidate_filename = 'class.txt'
        self.windowsize_filename = 'windowsize.txt'

        # initialize mouse state
        self.STATE = {}
        self.STATE['click'] = 0
        self.STATE['x'], self.STATE['y'] = 0, 0

        # reference to bbox
        self.bboxIdList = []
        self.bboxId = None
        self.bboxList = []
        self.hl = None
        self.vl = None

        # ----------------- GUI stuff ---------------------
        # dir entry & load
        self.label = Label(self.frame, text = "Image Dir:")
        self.label.grid(row = 0, column = 0, sticky = E)
        self.entry = Entry(self.frame)
        self.entry.grid(row = 0, column = 1, sticky = W+E)
        self.ldBtn = Button(self.frame, text = "Load", command = self.loadDir)
        self.ldBtn.grid(row = 0, column = 2,sticky = W+E)

        # main panel for labeling
        self.mainPanel = Canvas(self.frame, cursor='tcross')
        self.mainPanel.bind("<Button-1>", self.mouseClick)
        self.mainPanel.bind("<Motion>", self.mouseMove)



        # ---------------------- shortcut key -------------------------
        self.parent.bind("<Escape>", self.cancelBBox)  # press <Espace> to cancel current bbox
        
        #change        
        #self.parent.bind("s", self.cancelBBox)
        self.parent.bind("<Left>", self.prevImage) # press '<-' to go backforward
        self.parent.bind("<Right>", self.nextImage) # press '->' to go forward

        #add
        self.parent.bind("c", self.setClass) # press 'c' to confirm class
        self.parent.bind("<Control_L>"+"z", self.delBBox_prev) # del previous bbox
        
        self.parent.bind("0", self.setClass_0)
        self.parent.bind("1", self.setClass_1)
        self.parent.bind("2", self.setClass_2)
        self.parent.bind("3", self.setClass_3)
        self.parent.bind("4", self.setClass_4)
        self.parent.bind("5", self.setClass_5)
        self.parent.bind("6", self.setClass_6)
        self.parent.bind("7", self.setClass_7)
        self.parent.bind("8", self.setClass_8)
        self.parent.bind("9", self.setClass_9)
        self.parent.bind(".", self.setClass_point)
        self.parent.bind(",", self.setClass_point)
        self.parent.bind("+", self.setClass_plus)
        self.parent.bind("-", self.setClass_minus)
        self.parent.bind("*", self.setClass_pm)
        self.parent.bind("i"+"n", self.setClass_in_nasi)
        self.parent.bind("i"+"a", self.setClass_in_ari)
        self.parent.bind("o"+"n", self.setClass_out_nasi)
        self.parent.bind("o"+"a", self.setClass_out_ari)






        self.mainPanel.grid(row = 1, column = 1, rowspan = 4, sticky = W+N)
        global WINDOW_SIZE
        # choose class
        self.classname = StringVar()
        self.classcandidate = ttk.Combobox(self.frame,state='readonly',textvariable=self.classname)
        self.classcandidate.grid(row=1,column=2)
        if os.path.exists(self.classcandidate_filename):
        	with open(self.classcandidate_filename) as cf:
        		for line in cf.readlines():
        			# print line
        			self.cla_can_temp.append(line.strip('\n'))
        if os.path.exists(self.windowsize_filename):
            with open(self.windowsize_filename) as cf:
                WINDOW_SIZE =int(''.join(i for i in cf.readline() if i.isdigit()))
        #print self.cla_can_temp
        self.classcandidate['values'] = self.cla_can_temp
        self.classcandidate.current(0)

        self.currentLabelclass = self.classcandidate.get() #init

        self.btnclass = Button(self.frame, text = 'ConfirmClass', command = self.setClass)
        self.btnclass.grid(row=2,column=2,sticky = W+E)

        # showing bbox info & delete bbox
        self.lb1 = Label(self.frame, text = 'Bounding boxes:')
        self.lb1.grid(row = 3, column = 2,  sticky = W+N)
        self.listbox = Listbox(self.frame, width = 22, height = 12)
        self.listbox.grid(row = 4, column = 2, sticky = N+S)
        self.btnDel = Button(self.frame, text = 'Delete', command = self.delBBox)
        self.btnDel.grid(row = 5, column = 2, sticky = W+E+N)
        self.btnClear = Button(self.frame, text = 'ClearAll', command = self.clearBBox)
        self.btnClear.grid(row = 6, column = 2, sticky = W+E+N)

        # control panel for image navigation
        self.ctrPanel = Frame(self.frame)
        self.ctrPanel.grid(row = 7, column = 1, columnspan = 2, sticky = W+E)
        self.prevBtn = Button(self.ctrPanel, text='<< Prev', width = 10, command = self.prevImage)
        self.prevBtn.pack(side = LEFT, padx = 5, pady = 3)
        self.nextBtn = Button(self.ctrPanel, text='Next >>', width = 10, command = self.nextImage)
        self.nextBtn.pack(side = LEFT, padx = 5, pady = 3)
        self.progLabel = Label(self.ctrPanel, text = "Progress:     /    ")
        self.progLabel.pack(side = LEFT, padx = 5)
        self.tmpLabel = Label(self.ctrPanel, text = "Go to Image No.")
        self.tmpLabel.pack(side = LEFT, padx = 5)
        self.idxEntry = Entry(self.ctrPanel, width = 5)
        self.idxEntry.pack(side = LEFT)
        self.goBtn = Button(self.ctrPanel, text = 'Go', command = self.gotoImage)
        self.goBtn.pack(side = LEFT)


        # example pannel for illustration
        self.egPanel = Frame(self.frame, border = 10)
        self.egPanel.grid(row = 1, column = 0, rowspan = 5, sticky = N)
        self.tmpLabel2 = Label(self.egPanel, text = "Examples:")
        self.tmpLabel2.pack(side = TOP, pady = 5)
        self.egLabels = []
        for i in range(3):
            self.egLabels.append(Label(self.egPanel))
            self.egLabels[-1].pack(side = TOP)

        # display mouse position
        self.disp = Label(self.ctrPanel, text='')
        self.disp.pack(side = RIGHT)

        self.frame.columnconfigure(1, weight = 1)
        self.frame.rowconfigure(4, weight = 1)

        # for debugging
##        self.setImage()
##        self.loadDir()

    def loadDir(self, dbg = False):
        if not dbg:
            s = self.entry.get()
            self.parent.focus()
            self.category = int(s)
        else:
            s = r'D:\workspace\python\labelGUI'
##        if not os.path.isdir(s):
##            tkMessageBox.showerror("Error!", message = "The specified dir doesn't exist!")
##            return
        # get image list
        self.imageDir = os.path.join(r'./Images', '%03d' %(self.category))
        #print self.imageDir
        #print self.category
        self.imageList = glob.glob(os.path.join(self.imageDir, '*.jpg'))
        
        
        #add
        self.imageList.sort()
        
        
        #print self.imageList.sort()
        #self.imageList.sort()
        if len(self.imageList) == 0:
            print 'No .jpg images found in the specified dir!'
            return

        # default to the 1st image in the collection
        self.cur = 1
        self.total = len(self.imageList)

         # set up output dir
        self.outDir = os.path.join(r'./Labels', '%03d' %(self.category))
        if not os.path.exists(self.outDir):
            os.mkdir(self.outDir)

        # load example bboxes
        #self.egDir = os.path.join(r'./Examples', '%03d' %(self.category))
        self.egDir = os.path.join(r'./Examples/demo')
        print os.path.exists(self.egDir)
        if not os.path.exists(self.egDir):
            return
        filelist = glob.glob(os.path.join(self.egDir, '*.jpg'))
        self.tmp = []
        self.egList = []
        random.shuffle(filelist)
        for (i, f) in enumerate(filelist):
            if i == 3:
                break
            im = Image.open(f)
            r = min(SIZE[0] / im.size[0], SIZE[1] / im.size[1])
            new_size = int(r * im.size[0]), int(r * im.size[1])
            self.tmp.append(im.resize(new_size, Image.ANTIALIAS))
            self.egList.append(ImageTk.PhotoImage(self.tmp[-1]))
            self.egLabels[i].config(image = self.egList[-1], width = SIZE[0], height = SIZE[1])

        self.loadImage()
        print '%d images loaded from %s' %(self.total, s)

    def loadImage(self):
        # load image
        global WINDOW_SIZE
        imagepath = self.imageList[self.cur - 1]
        self.img = Image.open(imagepath)
        self.scale = min(WINDOW_SIZE / self.img.size[0], WINDOW_SIZE / self.img.size[1])
        self.imgnewsize = int(self.scale * self.img.size[0]), int(self.scale * self.img.size[1])
        self.tkimg = ImageTk.PhotoImage(self.img.resize(self.imgnewsize,Image.ANTIALIAS))
        self.mainPanel.config(width = self.tkimg.width(), height = self.tkimg.height())
        self.mainPanel.create_image(0, 0, image = self.tkimg, anchor=NW)
        self.progLabel.config(text = "%04d/%04d" %(self.cur, self.total))

        # load labels
        self.clearBBox()
        self.imagename = os.path.split(imagepath)[-1].split('.')[0]
        labelname = self.imagename + '.txt'
        self.labelfilename = os.path.join(self.outDir, labelname)
        bbox_cnt = 0
        if os.path.exists(self.labelfilename):
            with open(self.labelfilename) as f:
                for (i, line) in enumerate(f):
                    if i == 0:
                        bbox_cnt = int(line.strip())
                        continue
                    # tmp = [int(t.strip()) for t in line.split()]
                    tmp = line.split()
                    # print tmp
                    self.bboxList.append(tuple(tmp))
                    tmpId = self.mainPanel.create_rectangle(int(int(tmp[0])*self.scale), int(int(tmp[1])*self.scale), \
                                                            int(int(tmp[2])*self.scale), int(int(tmp[3])*self.scale), \
                                                            width = 2, \
                                                            outline = COLORS[(len(self.bboxList)-1) % len(COLORS)])
                    # print tmpId
                    self.bboxIdList.append(tmpId)
                    self.listbox.insert(END, '%s : (%d, %d) -> (%d, %d)' %(tmp[4],int(tmp[0]), int(tmp[1]), \
                                                            int(tmp[2]), int(tmp[3])))
                    self.listbox.itemconfig(len(self.bboxIdList) - 1, fg = COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])

    def saveImage(self):
        with open(self.labelfilename, 'w') as f:
            f.write('%d\n' %len(self.bboxList))
            for bbox in self.bboxList:
                f.write(' '.join(map(str, bbox)) + '\n')
        print 'Image No. %d saved' %(self.cur)


    def mouseClick(self, event):
        if self.STATE['click'] == 0:
            self.STATE['x'], self.STATE['y'] = event.x, event.y
        else:
            x1, x2 = min(self.STATE['x'], event.x), max(self.STATE['x'], event.x)
            y1, y2 = min(self.STATE['y'], event.y), max(self.STATE['y'], event.y)
            self.bboxList.append((int(x1/self.scale), int(y1/self.scale), int(x2/self.scale), int(y2/self.scale), self.currentLabelclass))
            self.bboxIdList.append(self.bboxId)
            self.bboxId = None
            self.listbox.insert(END, '%s : (%d, %d) -> (%d, %d)' %(self.currentLabelclass,int(x1/self.scale), int(y1/self.scale), int(x2/self.scale), int(y2/self.scale)))
            self.listbox.itemconfig(len(self.bboxIdList) - 1, fg = COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])
        self.STATE['click'] = 1 - self.STATE['click']

    def mouseMove(self, event):
    	try:
    		self.scale
    	except:
    		self.scale=1
        self.disp.config(text = 'x: %d, y: %d' %(int(event.x/self.scale), int(event.y/self.scale)))
        if self.tkimg:
            if self.hl:
                self.mainPanel.delete(self.hl)
            self.hl = self.mainPanel.create_line(0, event.y, self.tkimg.width(), event.y, width = 2)
            if self.vl:
                self.mainPanel.delete(self.vl)
            self.vl = self.mainPanel.create_line(event.x, 0, event.x, self.tkimg.height(), width = 2)
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
            self.bboxId = self.mainPanel.create_rectangle(self.STATE['x'], self.STATE['y'], \
                                                            event.x, event.y, \
                                                            width = 2, \
                                                            outline = COLORS[len(self.bboxList) % len(COLORS)])

    def cancelBBox(self, event):
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
                self.bboxId = None
                self.STATE['click'] = 0

    def delBBox(self):
        sel = self.listbox.curselection()
        if len(sel) != 1 :
            return
        idx = int(sel[0])
        self.mainPanel.delete(self.bboxIdList[idx])
        self.bboxIdList.pop(idx)
        self.bboxList.pop(idx)
        self.listbox.delete(idx)
    
    #add
    def delBBox_prev(self, event):
        #print(self.bboxIdList)
        if len(self.bboxIdList) == 0:
            return
        #idx = -1
        idx = len(self.bboxIdList) - 1
        self.mainPanel.delete(self.bboxIdList[idx])
        self.bboxIdList.pop(idx)
        self.bboxList.pop(idx)
        self.listbox.delete(idx)


    def clearBBox(self):
        for idx in range(len(self.bboxIdList)):
            self.mainPanel.delete(self.bboxIdList[idx])
        self.listbox.delete(0, len(self.bboxList))
        self.bboxIdList = []
        self.bboxList = []

    def prevImage(self, event = None):
        self.saveImage()
        if self.cur > 1:
            self.cur -= 1
            self.loadImage()

    def nextImage(self, event = None):
        self.saveImage()
        if self.cur < self.total:
            self.cur += 1
            self.loadImage()

    def gotoImage(self):
        idx = int(self.idxEntry.get())
        if 1 <= idx and idx <= self.total:
            self.saveImage()
            self.cur = idx
            self.loadImage()

    def setClass(self, event = None):
    	self.currentLabelclass = self.classcandidate.get()
    	print 'set label class to :',self.currentLabelclass


    #add
    def setClass_0(self, event = None):
    	self.currentLabelclass = self.classcandidate['values'][0]
    	print 'set label class to :',self.currentLabelclass

    def setClass_1(self, event = None):
    	self.currentLabelclass = self.classcandidate['values'][1]
    	print 'set label class to :',self.currentLabelclass
    
    def setClass_2(self, event = None):
    	self.currentLabelclass = self.classcandidate['values'][2]
    	print 'set label class to :',self.currentLabelclass

    def setClass_3(self, event = None):
    	self.currentLabelclass = self.classcandidate['values'][3]
    	print 'set label class to :',self.currentLabelclass

    def setClass_4(self, event = None):
    	self.currentLabelclass = self.classcandidate['values'][4]
    	print 'set label class to :',self.currentLabelclass
    
    def setClass_5(self, event = None):
    	self.currentLabelclass = self.classcandidate['values'][5]
    	print 'set label class to :',self.currentLabelclass


    def setClass_6(self, event = None):
    	self.currentLabelclass = self.classcandidate['values'][6]
    	print 'set label class to :',self.currentLabelclass

    def setClass_7(self, event = None):
    	self.currentLabelclass = self.classcandidate['values'][7]
    	print 'set label class to :',self.currentLabelclass
    
    def setClass_8(self, event = None):
    	self.currentLabelclass = self.classcandidate['values'][8]
    	print 'set label class to :',self.currentLabelclass

    def setClass_9(self, event = None):
    	self.currentLabelclass = self.classcandidate['values'][9]
    	print 'set label class to :',self.currentLabelclass

    def setClass_point(self, event = None):
    	self.currentLabelclass = self.classcandidate['values'][10]
    	print 'set label class to :',self.currentLabelclass
    
    def setClass_plus(self, event = None):
    	self.currentLabelclass = self.classcandidate['values'][11]
    	print 'set label class to :',self.currentLabelclass

    def setClass_minus(self, event = None):
    	self.currentLabelclass = self.classcandidate['values'][12]
    	print 'set label class to :',self.currentLabelclass

    def setClass_pm(self, event = None):
    	self.currentLabelclass = self.classcandidate['values'][13]
    	print 'set label class to :',self.currentLabelclass
    
    def setClass_in_nasi(self, event = None):
    	self.currentLabelclass = self.classcandidate['values'][14]
    	print 'set label class to :',self.currentLabelclass

    def setClass_in_ari(self, event = None):
    	self.currentLabelclass = self.classcandidate['values'][15]
    	print 'set label class to :',self.currentLabelclass

    def setClass_out_nasi(self, event = None):
    	self.currentLabelclass = self.classcandidate['values'][16]
    	print 'set label class to :',self.currentLabelclass

    def setClass_out_ari(self, event = None):
    	self.currentLabelclass = self.classcandidate['values'][17]
    	print 'set label class to :',self.currentLabelclass


##    def setImage(self, imagepath = r'test2.png'):
##        self.img = Image.open(imagepath)
##        self.tkimg = ImageTk.PhotoImage(self.img)
##        self.mainPanel.config(width = self.tkimg.width())
##        self.mainPanel.config(height = self.tkimg.height())
##        self.mainPanel.create_image(0, 0, image = self.tkimg, anchor=NW)

if __name__ == '__main__':
    root = Tk()
    tool = LabelTool(root)
    root.resizable(width =  True, height = True)
    root.mainloop()
