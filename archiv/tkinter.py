from tkinter import ttk as ttk
from tkinter import messagebox
import tkinter as tk

class GuiInterface(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.parent.title("Network Configurator")
        self.parent.resizable(False, False)

        self.createCanvas()
    
    def createCanvas(self):
        
        self.workspace_canvas = tk.Canvas(self.parent, bg="white", height=500, width=500)
        self.workspace_canvas.bind("<Button-1>", self.onClickLeft)
        self.workspace_canvas.bind("<Button-3>", self.onClickRight)
        self.workspace_canvas.bind("<B1-Motion>", self.onDrag)

        self.workspace_canvas.pack(side=tk.RIGHT)
        self.button_1 = ttk.Button(self.parent, text="Připojit", width=15 ,command=self.connectButtonHandler)
        self.button_1.pack(side=tk.BOTTOM)

        #self.test_rectangle = self.workspace_canvas.create_rectangle(10, 10, 100, 100, fill="red", outline="black", width = 1)
        #self.test_rectangle2 = self.workspace_canvas.create_rectangle(150, 10, 240, 100, fill="blue", outline="black", width = 1)
        self.myimg = tk.PhotoImage(file='router.png')
        self.test_rectangle = self.workspace_canvas.create_image(50, 50, image=self.myimg, tags=("devices", "router_1"))
        self.test_rectangle2 = self.workspace_canvas.create_image(200, 200, image=self.myimg, tags=("devices", "router_2"))
        self.test_rectangle3 = self.workspace_canvas.create_image(50, 400, image=self.myimg, tags=("devices", "router_3"))
        self.test_rectangle4 = self.workspace_canvas.create_image(200, 400, image=self.myimg, tags=("devices", "router_4"))   

    def onClickRight(self, event):
        selected = self.workspace_canvas.find_overlapping(event.x-10, event.y-10, event.x+10, event.y+10)
        if selected:
            self.workspace_canvas.selected = selected[-1]  # select the top-most item
        self.messagebox = tk.Frame(self.parent, borderwidth=1, relief=tk.SUNKEN)
        
        #vyskakovaci okno
        top = tk.Toplevel(self.parent)
        top.geometry("750x250")
        top.title("okno")
        tk.Label(top, text= f"{selected}").place(x=150,y=80)
        self.comboselection = ttk.Combobox(top, values=[1, 2, 3, 4])
        self.comboselection.place(x=150, y=120)
        ttk.Button(top, text="Připojit", width=15 , command= lambda: self.connectButtonHandler(selected)).place(x=150, y=150)



    def connectButtonHandler(self, selected):
        #connects selected object to object selected in combobox with line
        self.combo_selected = self.comboselection.get()

        tag = f"connector_{self.workspace_canvas.find_withtag(selected)[0]}_{self.workspace_canvas.find_withtag(self.combo_selected)[0]}"
        #self.workspace_canvas.delete(tag) #teoreticky toto nepotrebuju?

        print(self.workspace_canvas.find_withtag(selected))
        print(self.workspace_canvas.find_withtag(self.combo_selected))

        device_a_xy = self.workspace_canvas.coords(self.workspace_canvas.find_withtag(selected))
        device_b_xy = self.workspace_canvas.coords(self.workspace_canvas.find_withtag(self.combo_selected))
        connector = self.workspace_canvas.create_line(device_a_xy[0], device_a_xy[1], device_b_xy[0], device_b_xy[1], tags=(tag,))
        self.workspace_canvas.tag_lower(connector)

    def onClickLeft(self, event):
        selected = self.workspace_canvas.find_overlapping(event.x-10, event.y-10, event.x+10, event.y+10)
        if selected:
            self.workspace_canvas.selected = selected[-1]  # vybere nejblizsi (v popredi) objekt
            self.workspace_canvas.startxy = (event.x, event.y)
            #print(self.workspace_canvas.selected, self.workspace_canvas.startxy)
            print(self.get_connected_items(self.workspace_canvas.selected))
        else:
            self.workspace_canvas.selected = None

    def onDrag(self, event):
        if self.workspace_canvas.selected:
            dx, dy = event.x-self.workspace_canvas.startxy[0], event.y-self.workspace_canvas.startxy[1] #vypocet vzdalenosti posunuti z predchozi pozice
            self.workspace_canvas.move(self.workspace_canvas.selected, dx, dy) #posun objektu
            self.workspace_canvas.startxy = (event.x, event.y) #update posledni pozice
    

    def isConnected(self, device):
        pass

    def get_connected_items(self, tag1):
        # Get all items with tag1
        items_with_tag1 = set(self.workspace_canvas.find_withtag(tag1))
        print(f"items_with_tag1: {items_with_tag1}")
        # Initialize a set to store the connected items
        connected_items = set()


        for item in items_with_tag1:
            tags = self.workspace_canvas.gettags(item) # Get all the tags of the current item
            print(f"tags: {tags}")           
            for tag in tags:  # Iterate over each tag
                print(f"tag: {tag}")
                # If the tag is not tag1, add the items with this tag to the connected items
                if "router_" in tag and tag != tag1:
                    connected_items.update(self.workspace_canvas.find_withtag(tag))

        # Return the connected items
        return connected_items
      


    def isConnected_old(self, device):
        """
        Funkce prijme zarizeni (objekt na canvasu) a zkontroluje jestli je dane zarizeni propojeno s jinym zarizenim
        pokud je zarizeni propojeno s dalsim zarizenim, vrati list obsahujici vsechny propojene zarizeni
        pokud neni, vrati zpet pouze puvodni zarizeni (objekt na cavasu) v tuple
        """
        #osetrit aby se nemohli prekryvat zarizeni (a asi i cary)
        self.device_coords = self.workspace_canvas.coords(device)
        self.device_overlaps = self.workspace_canvas.find_overlapping(self.device_coords[0]-10, self.device_coords[1]-10, self.device_coords[0]+10, self.device_coords[1]+10) #zkontroluju jestli objekt prekryva/je prekryvan jinym objektem = vrati list prekryvajich objektu
        if len(self.device_overlaps) >= 2: #pokud je delka listu vetsi nez 2, objekty se prekryvaji
            self.connector_coords = self.workspace_canvas.coords(self.device_overlaps[0]) #zjistim souradnice spojovnice
            self.connected_group = self.workspace_canvas.find_overlapping(self.connector_coords[0], self.connector_coords[1], self.connector_coords[2], self.connector_coords[3]) #zjistim zda je spojovnice prekryvana (na vsech souradnicich spojovice)
            print(self.connected_group)
            return(self.connected_group)
        elif len(self.device_overlaps) == 1: #pokud je delka listu rovna 1, objekty se neprekryvaji
            return(device,)
        
        """
        #neaktualni, pozdeji smazat
        self.devices = self.workspace_canvas.find_withtag("devices")
        for self.device in self.devices:
            self.device_coords = self.workspace_canvas.coords(self.device)
            self.overlapping_devices = self.workspace_canvas.find_overlapping(self.device_coords[0]-10, self.device_coords[1]-10, self.device_coords[0]+10, self.device_coords[1]+10)
            if (len(self.overlapping_devices)>=2):
                return True
            else:
                return False
        """

    def updateConnectorLine(self, device_a, device_b):
        tag = f"connector_{device_a}_{device_b}"
        self.workspace_canvas.delete(tag)

        device_a_xy = self.workspace_canvas.coords(device_a)
        device_b_xy = self.workspace_canvas.coords(device_b)

        #pro obdelniky
        #x_str1 = (rec1_xy[0] + rec1_xy[2])/2
        #y_str1 = (rec1_xy[1] + rec1_xy[3])/2
        #x_str2 = (rec2_xy[0] + rec2_xy[2])/2
        #y_str2 = (rec2_xy[1] + rec2_xy[3])/2

        self.connector = self.workspace_canvas.create_line(device_a_xy[0], device_a_xy[1], device_b_xy[0], device_b_xy[1], tags=(tag,), width=1)
        self.workspace_canvas.tag_lower(self.connector)
        

root = tk.Tk()
window = GuiInterface(root)
window.mainloop()