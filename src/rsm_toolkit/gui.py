"""Small local Tk desktop interface; calculation runs in a separate process."""
from __future__ import annotations
import json
from importlib.resources import files
from io import BytesIO
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from . import gui_workflow as workflow


class Application:
    def __init__(self, root):
        self.root=root
        self.process=None
        self.temp=None
        self.result_folder=None
        self.image_source=None
        root.title('RSM Toolkit')
        from PIL import Image, ImageTk
        icon_data=files('rsm_toolkit').joinpath('data','icons','rsm.png').read_bytes()
        with Image.open(BytesIO(icon_data)) as icon:
            self.window_icons=[ImageTk.PhotoImage(icon.resize((size,size),Image.Resampling.LANCZOS),master=root)
                               for size in (16,32,48,256)]
        root.iconphoto(True,*self.window_icons)
        root.geometry('1220x850')
        root.minsize(900,700)
        root.protocol('WM_DELETE_WINDOW',self.close)
        self.variables={k:(tk.BooleanVar(root,value=v) if isinstance(v,bool) else tk.StringVar(root,value=v))
                        for k,v in workflow.defaults().items()}
        header=ttk.Frame(root,padding=10)
        header.pack(fill='x')
        ttk.Label(header,text='RSM Toolkit',font=('Segoe UI',17,'bold')).pack(side='left')
        for label,command in [('New',self.reset),('Load settings',self.load),('Save settings',self.save)]:
            ttk.Button(header,text=label,command=command).pack(side='left',padx=6)
        body=ttk.Panedwindow(root,orient='horizontal')
        body.pack(fill='both',expand=True,padx=10)
        left=ttk.Frame(body,width=480)
        right=ttk.Frame(body)
        body.add(left,weight=0)
        body.add(right,weight=1)
        tabs=ttk.Notebook(left)
        tabs.pack(fill='both',expand=True)
        self.tabs=tabs
        self.pages=[]
        for name in ('1. File','2. Sample','3. Advanced'):
            page=ttk.Frame(tabs,padding=10)
            tabs.add(page,text=name)
            page.columnconfigure(1,weight=1)
            self.pages.append(page)
        file,sample,advanced=self.pages
        self.entry(file,0,'Measurement','file',self.browse)
        self.entry(file,1,'Save in folder','output',self.output)
        self.entry(file,2,'Map name','name')
        self.entry(file,3,'Plot title','title')
        self.combo(file,4,'Display','mode',['points','grid'])
        self.combo(file,5,'Intensity scale','scale',['log','linear'])
        self.entry(file,6,'Color range (decades)','decades')
        self.note(file,7,'Points shows measured bins. Grid shows bin means; no interpolation.\n'
                  'Each run saves a new folder containing the plot, data and reusable settings.')
        self.check(file,8,'Show theoretical substrate / film markers','overlays')
        ttk.Label(file,text='Presets',font=('Segoe UI',10,'bold')).grid(row=9,column=0,columnspan=3,sticky='w',pady=(20,5))
        ttk.Button(file,text='Symmetric (11-20), 35% Zn',command=lambda:self.example(False)).grid(row=10,column=0,columnspan=3,sticky='ew',pady=4)
        ttk.Button(file,text='Asymmetric (12-30), 35% Zn',command=lambda:self.example(True)).grid(row=11,column=0,columnspan=3,sticky='ew',pady=4)
        self.note(file,12,'Presets fill the sample and orientation fields.\n'
                  'Review them for your measurement before plotting.')

        self.combo(sample,0,'Substrate model','substrate',[*workflow.CIF_MATERIALS,'Custom cell'])
        self.entry(sample,1,'Custom substrate name','substrate_name')
        self.entry(sample,2,'Custom cell (a b c α β γ)','substrate_cell')
        self.combo(sample,3,'Film model','film',['CdZnS Vegard',*workflow.CIF_MATERIALS,'Custom cell','None'])
        self.entry(sample,4,'Zn (%) for CdZnS','zinc')
        self.entry(sample,5,'Custom film name','film_name')
        self.entry(sample,6,'Custom cell (a b c α β γ)','film_cell')
        self.entry(sample,7,'Norm: substrate surface','norm')
        self.entry(sample,8,'RSM: substrate reflection','reflection')
        self.entry(sample,9,'InPlane: crystal direction','inplane')
        self.note(sample,10,'InPlane is a direct crystal direction lying in the surface plane.')
        self.check(sample,11,'Film crystal axes aligned with substrate','aligned')
        self.entry(sample,12,'Film Norm (if not aligned)','film_norm')
        self.entry(sample,13,'Film InPlane (if not aligned)','film_inplane')
        self.entry(sample,14,'Film RSM (blank = substrate)','film_reflection')
        self.note(sample,15,'Examples: 11-20 or 1 1 -2 0. Cell lengths: Å; angles: degrees.\n'
                  'Custom cell fields are used only for Custom cell. CdZnS uses a relaxed\n'
                  'linear alloy model; Zn % is never guessed. Materials are optional without markers.')

        self.note(advanced,0,'Geometry: coplanar omega / 2theta.\n'
                  'Chi/Phi motor values are stored with the measurement.\n'
                  'For general vector geometry, use a JSON configuration with the CLI.')
        self.combo(advanced,2,'Map +Qy points','sense',
                   ['Choose axis sense','Along InPlane (+y)','Opposite InPlane (+y)'])
        self.entry(advanced,3,'Extra omega offset (degrees)','omega_offset')
        self.entry(advanced,4,'Extra 2theta offset (degrees)','detector_offset')
        self.entry(advanced,5,'Wavelength Å (blank = file)','wavelength')
        self.note(advanced,6,'Leave offsets at 0 unless you have a documented reason.\n'
                  'Offsets are added to recorded angles; peaks are never aligned automatically.\n'
                  'With markers, axis sense must be selected explicitly. Opposite rotates\n'
                  'the crystal frame 180° about its normal.')

        self.preview=ttk.Label(right,text='Your plot will appear here.',anchor='center')
        self.preview.pack(fill='both',expand=True)
        self.preview.bind('<Configure>',lambda event:self.show_image())
        self.open_button=ttk.Button(right,text='Open saved output folder',command=self.open_output,state='disabled')
        self.open_button.pack(pady=8)
        footer=ttk.Frame(root,padding=10)
        footer.pack(fill='x')
        self.plot_button=ttk.Button(footer,text='Plot and save',command=self.plot)
        self.plot_button.pack(side='left')
        self.status=tk.StringVar(root,value='Choose a file, enter settings, then Plot and save.')
        ttk.Label(footer,textvariable=self.status,wraplength=950).pack(side='left',padx=12)

    def entry(self,page,row,label,key,command=None):
        ttk.Label(page,text=label).grid(row=row,column=0,sticky='w',pady=5,padx=(0,8))
        ttk.Entry(page,textvariable=self.variables[key],width=25).grid(row=row,column=1,sticky='ew',pady=5)
        if command:
            ttk.Button(page,text='Browse…',command=command).grid(row=row,column=2,padx=4)

    def combo(self,page,row,label,key,values):
        ttk.Label(page,text=label).grid(row=row,column=0,sticky='w',pady=5,padx=(0,8))
        ttk.Combobox(page,textvariable=self.variables[key],values=values,state='readonly',width=27).grid(row=row,column=1,columnspan=2,sticky='ew',pady=5)

    def check(self,page,row,label,key):
        ttk.Checkbutton(page,text=label,variable=self.variables[key]).grid(row=row,column=0,columnspan=3,sticky='w',pady=7)

    def note(self,page,row,text):
        ttk.Label(page,text=text,wraplength=440,foreground='#475569').grid(row=row,column=0,columnspan=3,sticky='w',pady=10)

    def fields(self):
        return {k:v.get() for k,v in self.variables.items()}

    def apply(self,fields):
        for key,value in fields.items():
            self.variables[key].set(value)

    def reset(self):
        self.apply(workflow.defaults())

    def browse(self):
        path=filedialog.askopenfilename(title='Choose XRD measurement',filetypes=[('XRD data','*.raw *.brml'),('All files','*.*')])
        if path:
            self.variables['file'].set(path)
            self.variables['name'].set(Path(path).stem)

    def output(self):
        path=filedialog.askdirectory(title='Choose output folder')
        if path:self.variables['output'].set(path)

    def example(self,asymmetric):
        f=workflow.preset(asymmetric)
        f['output']=self.variables['output'].get()
        name='rsm(12-30)along10-10.raw' if asymmetric else 'RSM(11-20)along0001.raw'
        path=Path.cwd()/'example_data'/name
        f['file']=str(path) if path.exists() else self.variables['file'].get()
        self.apply(f)
        self.status.set('Preset loaded. Review Sample and Advanced, then Plot and save.')

    def load(self):
        path=filedialog.askopenfilename(title='Load GUI settings.json',filetypes=[('JSON settings','*.json')])
        if path:
            try:
                self.apply(workflow.load_settings(path))
                self.status.set('Settings loaded. Select a new measurement if needed.')
            except Exception as exc:messagebox.showerror('Cannot load settings',str(exc))

    def save(self):
        path=filedialog.asksaveasfilename(title='Save reusable GUI settings',initialfile='settings.json',defaultextension='.json')
        if path:
            try:workflow.save_settings(path,self.fields())
            except Exception as exc:messagebox.showerror('Cannot save settings',str(exc))

    def plot(self):
        if self.process is not None:return
        try:
            form=self.fields()
            workflow.build_configuration(form)
            if not Path(form['file']).is_file():raise ValueError('Choose an existing measurement file on the File tab.')
            self.temp=tempfile.TemporaryDirectory(prefix='rsm-gui-')
            task=Path(self.temp.name)/'settings.json'
            workflow.save_settings(task,form)
            result=Path(self.temp.name)/'result.json'
            self.process=subprocess.Popen([sys.executable,'-m','rsm_toolkit.gui','--worker',str(task),str(result)],
                                          stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                                          creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            self.plot_button.config(state='disabled')
            self.status.set('Calculating and saving… You can continue reviewing the form. This run uses the settings at click time.')
            self.root.after(200,self.poll)
        except Exception as exc:
            if self.temp:self.temp.cleanup();self.temp=None
            messagebox.showerror('Check your settings',str(exc))

    def poll(self):
        if self.process.poll() is None:
            self.root.after(200,self.poll)
            return
        try:
            result=json.loads((Path(self.temp.name)/'result.json').read_text(encoding='utf-8'))
            if 'error' in result:raise ValueError(result['error'])
            self.result_folder=Path(result['folder'])
            from PIL import Image
            with Image.open(self.result_folder/'map.png') as im:self.image_source=im.copy()
            self.show_image()
            self.open_button.config(state='normal')
            self.status.set('Saved: '+str(self.result_folder))
        except Exception as exc:
            self.status.set('Plot failed. Previous preview, if any, is unchanged.')
            messagebox.showerror('Could not create map',str(exc))
        finally:
            self.process=None
            self.temp.cleanup()
            self.temp=None
            self.plot_button.config(state='normal')

    def show_image(self):
        if self.image_source is None:return
        from PIL import Image,ImageTk
        im=self.image_source.copy()
        im.thumbnail((max(100,self.preview.winfo_width()-10),max(100,self.preview.winfo_height()-10)),Image.Resampling.LANCZOS)
        self.photo=ImageTk.PhotoImage(im,master=self.root)
        self.preview.config(image=self.photo,text='')

    def open_output(self):
        if self.result_folder:
            if sys.platform=='win32':os.startfile(str(self.result_folder))
            elif sys.platform=='darwin':subprocess.Popen(['open',str(self.result_folder)])
            else:subprocess.Popen(['xdg-open',str(self.result_folder)])

    def close(self):
        if self.process is not None:
            messagebox.showinfo('Calculation running','Please wait for this run to finish before closing.')
            return
        self.root.destroy()


def main():
    if len(sys.argv)>1 and sys.argv[1]=='--worker':
        import traceback
        import warnings
        import matplotlib
        matplotlib.use('Agg')
        result=Path(sys.argv[3])
        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always')
                folder=workflow.execute(workflow.load_settings(sys.argv[2]))
            (folder/'warnings.txt').write_text('\n'.join(str(w.message) for w in caught),encoding='utf-8')
            value={'folder':str(folder)}
        except Exception as exc:
            value={'error':str(exc)}
            result.with_suffix('.log').write_text(traceback.format_exc(),encoding='utf-8')
        result.write_text(json.dumps(value),encoding='utf-8')
        return
    root=tk.Tk()
    Application(root)
    root.mainloop()


if __name__=='__main__':main()
