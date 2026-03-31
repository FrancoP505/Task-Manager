import json
import os
from tkinter import *
from tkinter import ttk, messagebox
from datetime import datetime, date, timedelta
from plyer import notification

DATA_FILE = "data.json"
NOTIFICATION_LOG = "notifications.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"Categorias": [], "Tareas": []}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_notification_log():
    if os.path.exists(NOTIFICATION_LOG):
        with open(NOTIFICATION_LOG, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_notification_log(log):
    with open(NOTIFICATION_LOG, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)

def send_notification(title, message):
    try:
        notification.notify(title=title, message=message, timeout=10)
    except Exception as e:
        print(f"Notification error: {e}")

def get_next_id(items):
    return max((item["id"] for item in items), default=0) + 1

def get_Prioridad_label(Prioridad):
    labels = {1: "Bajo", 2: "Medio", 3: "Alto"}
    return labels.get(Prioridad, "Bajo")

class TaskManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Task Manager")
        self.root.geometry("1100x600")
        
        self.data = load_data()
        self.notification_log = load_notification_log()
        self.toaster = None
        
        self.setup_ui()
        self.refresh_Categorias()
        self.refresh_Tareas()
        self.check_notifications()
        self.start_notification_check()
    
    def setup_ui(self):
        main_paned = PanedWindow(self.root, orient=HORIZONTAL)
        main_paned.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        left_frame = Frame(main_paned, width=200)
        main_paned.add(left_frame, minsize=200)
        
        Label(left_frame, text="Categorias", font=("Arial", 12, "bold")).pack(pady=5)
        
        self.category_listbox = Listbox(left_frame)
        self.category_listbox.pack(fill=BOTH, expand=True, pady=5)
        self.category_listbox.bind("<<ListboxSelect>>", self.on_category_select)
        
        cat_btn_frame = Frame(left_frame)
        cat_btn_frame.pack(fill=X, pady=5)
        
        Button(cat_btn_frame, text="Añadir", command=self.add_category).pack(side=LEFT, expand=True, padx=2)
        Button(cat_btn_frame, text="Eliminar", command=self.delete_category).pack(side=LEFT, expand=True, padx=2)
        
        right_frame = Frame(main_paned)
        main_paned.add(right_frame)
        
        top_frame = Frame(right_frame)
        top_frame.pack(fill=X, pady=5)
        
        Label(top_frame, text="Tareas", font=("Arial", 12, "bold")).pack(side=LEFT)
        
        # opciones de filtro
        self.filter_var = StringVar(value="Todas")
        filter_menu = OptionMenu(top_frame, self.filter_var, "Todas", "Pendiente", "Completado", "Expirado", command=lambda _: self.refresh_Tareas())
        filter_menu.pack(side=RIGHT)
        
        self.task_tree = ttk.Treeview(right_frame, columns=("Descripcion", "Prioridad", "Estado", "Creado", "Expira", "Categoria"), show="headings")
        self.task_tree.heading("Descripcion", text="Descripcion")
        self.task_tree.heading("Prioridad", text="Prioridad")
        self.task_tree.heading("Estado", text="Estado")
        self.task_tree.heading("Creado", text="Creado")
        self.task_tree.heading("Expira", text="Expira")
        self.task_tree.heading("Categoria", text="Categoria")
        
        self.task_tree.column("Descripcion", width=200)
        self.task_tree.column("Prioridad", width=70)
        self.task_tree.column("Estado", width=80)
        self.task_tree.column("Creado", width=100)
        self.task_tree.column("Expira", width=100)
        self.task_tree.column("Categoria", width=100)
        
        self.task_tree.pack(fill=BOTH, expand=True, pady=5)
        self.task_tree.bind("<Double-Button-1>", self.on_task_double_click)
        
        style = ttk.Style()
        style.configure("Treeview", rowheight=25)
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"))
        style.configure("Expirado.Treeview", foreground="red")
        style.configure("Completado.Treeview", foreground="green")
        style.configure("Pendiente.Treeview", foreground="black")
        
        self.task_tree.tag_configure("Expirado", foreground="red")
        self.task_tree.tag_configure("Completado", foreground="green")
        self.task_tree.tag_configure("Pendiente", foreground="black")
        
        task_btn_frame = Frame(right_frame)
        task_btn_frame.pack(fill=X, pady=5)
        
        Button(task_btn_frame, text="Añadir tarea", command=self.add_task).pack(side=LEFT, padx=2)
        Button(task_btn_frame, text="Cambiar estado", command=self.toggle_task).pack(side=LEFT, padx=2)
        Button(task_btn_frame, text="Eliminar tarea", command=self.delete_task).pack(side=LEFT, padx=2)
    
    def refresh_Categorias(self):
        self.category_listbox.delete(0, END)
        for cat in self.data["Categorias"]:
            self.category_listbox.insert(END, cat["name"])
    
    def get_selected_category_id(self):
        selection = self.category_listbox.curselection()
        if not selection:
            return None
        index = selection[0]
        return self.data["Categorias"][index]["id"]
    
    def on_category_select(self, event):
        self.refresh_Tareas()
    
    def get_task_status(self, task):
        today = date.today()
        
        if task["Completado"]:
            return "Completado"
        
        if task.get("fecha_de_expiracion") and task.get("fecha_de_expiracion") != "No expira":
            try:
                expiry = datetime.strptime(task["fecha_de_expiracion"], "%Y-%m-%d").date()
                if expiry < today:
                    return "Expirado"
            except ValueError:
                pass
        
        return "Pendiente"
    
    def refresh_Tareas(self):
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)
        
        selected_cat_id = self.get_selected_category_id()
        filter_status = self.filter_var.get()
        
        for task in self.data["Tareas"]:
            if selected_cat_id is not None and task["category_id"] != selected_cat_id:
                continue
            
            task_status = self.get_task_status(task)
            
            if filter_status == "Pendiente" and task_status != "Pendiente":
                continue
            if filter_status == "Completado" and task_status != "Completado":
                continue
            if filter_status == "Expirado" and task_status != "Expirado":
                continue
            
            cat_name = ""
            for cat in self.data["Categorias"]:
                if cat["id"] == task["category_id"]:
                    cat_name = cat["name"]
                    break
            
            creado_date = task.get("creado_at", "")
            Fecha_de_expiracion = task.get("fecha_de_expiracion", "")
            Prioridad = task.get("Prioridad", 1)
            Prioridad_label = get_Prioridad_label(Prioridad)
            
            tag = "Pendiente"
            if task_status == "Completado":
                tag = "Completado"
            elif task_status == "Expirado":
                tag = "Expirado"
            
            self.task_tree.insert("", END, values=(
                task["Descripcion"],
                Prioridad_label,
                task_status,
                creado_date,
                Fecha_de_expiracion,
                cat_name
            ), tags=(str(task["id"]), tag))
    
    def add_category(self):
        dialog = Toplevel(self.root)
        dialog.title("Añadir Categoría")
        dialog.geometry("400x100")
        dialog.transient(self.root)
        dialog.grab_set()
        
        Label(dialog, text="Nombre de la categoría:").pack(pady=5)
        entry = Entry(dialog)
        entry.pack(pady=5, padx=20, fill=X)
        
        def save():
            name = entry.get().strip()
            if not name:
                messagebox.showwarning("Warning", "El nombre de la categoría no puede estar vacío")
                return
            
            new_cat = {"id": get_next_id(self.data["Categorias"]), "name": name}
            self.data["Categorias"].append(new_cat)
            save_data(self.data)
            self.refresh_Categorias()
            dialog.destroy()
        
        Button(dialog, text="Guardar", command=save).pack(pady=5)
    
    def delete_category(self):
        selected = self.category_listbox.curselection()
        if not selected:
            messagebox.showwarning("Warning", "Selecciona una categoría para eliminar")
            return
        
        index = selected[0]
        cat_id = self.data["Categorias"][index]["id"]
        
        Tareas_using = [t for t in self.data["Tareas"] if t["category_id"] == cat_id]
        if Tareas_using:
            if not messagebox.askyesno("Confirm", f"Esta categoría tiene {len(Tareas_using)} task(s). Eliminar categoría también eliminará estas tareas. ¿Deseas continuar?"):
                return
        
        self.data["Categorias"].pop(index)
        self.data["Tareas"] = [t for t in self.data["Tareas"] if t["category_id"] != cat_id]
        save_data(self.data)
        self.refresh_Categorias()
        self.refresh_Tareas()
    
    def add_task(self):
        if not self.data["Categorias"]:
            messagebox.showwarning("Warning", "Crea una categoría primero")
            return
        
        dialog = Toplevel(self.root)
        dialog.title("Añadir Tarea")
        dialog.geometry("400x380")
        dialog.transient(self.root)
        dialog.grab_set()
        
        Label(dialog, text="Descripcion:").pack(pady=5)
        desc_entry = Entry(dialog)
        desc_entry.pack(pady=5, padx=20, fill=X)
        
        Label(dialog, text="Prioridad:").pack(pady=5)
        Prioridad_var = IntVar(value=2)
        Prioridad_frame = Frame(dialog)
        Prioridad_frame.pack(pady=5)
        Radiobutton(Prioridad_frame, text="Baja (1)", variable=Prioridad_var, value=1).pack(side=LEFT, padx=10)
        Radiobutton(Prioridad_frame, text="Media (2)", variable=Prioridad_var, value=2).pack(side=LEFT, padx=10)
        Radiobutton(Prioridad_frame, text="Alta (3)", variable=Prioridad_var, value=3).pack(side=LEFT, padx=10)
        
        Label(dialog, text="Expira:").pack(pady=5)
        expires_var = StringVar(value="yes")
        expires_frame = Frame(dialog)
        expires_frame.pack(pady=5)
        Radiobutton(expires_frame, text="Sí", variable=expires_var, value="yes", command=lambda: toggle_date_entry()).pack(side=LEFT, padx=10)
        Radiobutton(expires_frame, text="No", variable=expires_var, value="no", command=lambda: toggle_date_entry()).pack(side=LEFT, padx=10)
        
        Label(dialog, text="Fecha de expiración (Año-Mes-Día):").pack(pady=5)
        date_entry = Entry(dialog)
        date_entry.pack(pady=5, padx=20, fill=X)
        
        Label(dialog, text="Categoria:").pack(pady=5)
        cat_var = StringVar()
        cat_combo = ttk.Combobox(dialog, textvariable=cat_var, state="readonly")
        cat_combo["values"] = [c["name"] for c in self.data["Categorias"]]
        cat_combo.pack(pady=5, padx=20, fill=X)
        if self.data["Categorias"]:
            cat_combo.current(0)
        
        def toggle_date_entry():
            if expires_var.get() == "yes":
                date_entry.config(state=NORMAL)
            else:
                date_entry.delete(0, END)
                date_entry.insert(0, "No expira")
                date_entry.config(state=DISABLED)
        
        toggle_date_entry()
        
        def save():
            Descripcion = desc_entry.get().strip()
            if not Descripcion:
                messagebox.showwarning("Warning", "La descripción no puede estar vacía")
                return
            
            if expires_var.get() == "yes":
                Fecha_de_expiracion = date_entry.get().strip()
                if Fecha_de_expiracion and Fecha_de_expiracion != "No expira":
                    try:
                        datetime.strptime(Fecha_de_expiracion, "%Y-%m-%d")
                    except ValueError:
                        messagebox.showwarning("Warning", "Formato de fecha inválido. Usa YYYY-MM-DD")
                        return
            else:
                Fecha_de_expiracion = "No expira"
            
            category_name = cat_var.get()
            category_id = None
            for cat in self.data["Categorias"]:
                if cat["name"] == category_name:
                    category_id = cat["id"]
                    break
            
            creado_at = date.today().strftime("%Y-%m-%d")
            
            new_task = {
                "id": get_next_id(self.data["Tareas"]),
                "Descripcion": Descripcion,
                "Completado": False,
                "Prioridad": Prioridad_var.get(),
                "creado_at": creado_at,
                "fecha_de_expiracion": Fecha_de_expiracion,
                "category_id": category_id
            }
            self.data["Tareas"].append(new_task)
            save_data(self.data)
            self.refresh_Tareas()
            dialog.destroy()
        
        Button(dialog, text="Guardar", command=save).pack(pady=10)
    
    def on_task_double_click(self, event):
        selection = self.task_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        task_id = int(self.task_tree.item(item, "tags")[0])
        
        task = next((t for t in self.data["Tareas"] if t["id"] == task_id), None)
        if not task:
            return
        
        dialog = Toplevel(self.root)
        dialog.title("Edit Task")
        dialog.geometry("400x380")
        dialog.transient(self.root)
        dialog.grab_set()
        
        Label(dialog, text="Descripción:").pack(pady=5)
        desc_entry = Entry(dialog)
        desc_entry.insert(0, task["Descripcion"])
        desc_entry.pack(pady=5, padx=20, fill=X)
        
        Label(dialog, text="Prioridad:").pack(pady=5)
        Prioridad_var = IntVar(value=task.get("Prioridad", 1))
        Prioridad_frame = Frame(dialog)
        Prioridad_frame.pack(pady=5)
        Radiobutton(Prioridad_frame, text="Baja (1)", variable=Prioridad_var, value=1).pack(side=LEFT, padx=10)
        Radiobutton(Prioridad_frame, text="Media (2)", variable=Prioridad_var, value=2).pack(side=LEFT, padx=10)
        Radiobutton(Prioridad_frame, text="Alta (3)", variable=Prioridad_var, value=3).pack(side=LEFT, padx=10)
        
        current_expires = "yes" if task.get("fecha_de_expiracion") and task.get("fecha_de_expiracion") != "No expira" else "no"
        Label(dialog, text="Expira:").pack(pady=5)
        expires_var = StringVar(value=current_expires)
        expires_frame = Frame(dialog)
        expires_frame.pack(pady=5)
        Radiobutton(expires_frame, text="Sí", variable=expires_var, value="yes", command=lambda: toggle_date_entry()).pack(side=LEFT, padx=10)
        Radiobutton(expires_frame, text="No", variable=expires_var, value="no", command=lambda: toggle_date_entry()).pack(side=LEFT, padx=10)
        
        Label(dialog, text="Fecha de expiración (Año-Mes-Día):").pack(pady=5)
        date_entry = Entry(dialog)
        if current_expires == "yes":
            date_entry.insert(0, task.get("fecha_de_expiracion", ""))
        else:
            date_entry.insert(0, "No expira")
            date_entry.config(state=DISABLED)
        date_entry.pack(pady=5, padx=20, fill=X)
        
        Label(dialog, text="Categoria:").pack(pady=5)
        cat_var = StringVar()
        cat_combo = ttk.Combobox(dialog, textvariable=cat_var, state="readonly")
        cat_combo["values"] = [c["name"] for c in self.data["Categorias"]]
        cat_combo.pack(pady=5, padx=20, fill=X)
        
        for i, cat in enumerate(self.data["Categorias"]):
            if cat["id"] == task["category_id"]:
                cat_combo.current(i)
                break
        
        def toggle_date_entry():
            if expires_var.get() == "yes":
                date_entry.config(state=NORMAL)
            else:
                date_entry.delete(0, END)
                date_entry.insert(0, "No expira")
                date_entry.config(state=DISABLED)
        
        def save():
            Descripcion = desc_entry.get().strip()
            if not Descripcion:
                messagebox.showwarning("Warning", "El campo de descripción no puede estar vacío")
                return
            
            if expires_var.get() == "yes":
                Fecha_de_expiracion = date_entry.get().strip()
                if Fecha_de_expiracion and Fecha_de_expiracion != "No expira":
                    try:
                        datetime.strptime(Fecha_de_expiracion, "%Y-%m-%d")
                    except ValueError:
                        messagebox.showwarning("Warning", "Formato de fecha inválido. Usa Año-Mes-Día (YYYY-MM-DD)")
                        return
            else:
                Fecha_de_expiracion = "No expira"
            
            category_name = cat_var.get()
            category_id = None
            for cat in self.data["Categorias"]:
                if cat["name"] == category_name:
                    category_id = cat["id"]
                    break
            
            task["Descripcion"] = Descripcion
            task["Prioridad"] = Prioridad_var.get()
            task["fecha_de_expiracion"] = Fecha_de_expiracion
            task["category_id"] = category_id
            
            save_data(self.data)
            self.refresh_Tareas()
            dialog.destroy()
        
        Button(dialog, text="Guardar", command=save).pack(pady=10)
    
    def toggle_task(self):
        selection = self.task_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Selecciona una tarea para cambiar su estado")
            return
        
        item = selection[0]
        task_id = int(self.task_tree.item(item, "tags")[0])
        
        for task in self.data["Tareas"]:
            if task["id"] == task_id:
                task["Completado"] = not task["Completado"]
                break
        
        save_data(self.data)
        self.refresh_Tareas()
    
    def delete_task(self):
        selection = self.task_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Selecciona una tarea para eliminar")
            return
        
        item = selection[0]
        task_id = int(self.task_tree.item(item, "tags")[0])
        
        self.data["Tareas"] = [t for t in self.data["Tareas"] if t["id"] != task_id]
        save_data(self.data)
        self.refresh_Tareas()
    
    def check_notifications(self):
        today = date.today()
        
        for task in self.data["Tareas"]:
            if task["Completado"]:
                continue
            
            if not task.get("fecha_de_expiracion") or task.get("fecha_de_expiracion") == "No expira":
                continue
            
            try:
                expiry = datetime.strptime(task["fecha_de_expiracion"], "%Y-%m-%d").date()
            except ValueError:
                continue
            
            task_id = str(task["id"])
            days_until_expiry = (expiry - today).days
            
            if task.get("Prioridad") == 2:
                if days_until_expiry == 2:
                    key = f"{task_id}_Medio_2days"
                    if key not in self.notification_log:
                        send_notification("Recordatorio", f"Tienes dos días para terminar la actividad: {task['Descripcion']}")
                        self.notification_log[key] = True
                        save_notification_log(self.notification_log)
            
            elif task.get("Prioridad") == 3:
                if 1 <= days_until_expiry <= 5:
                    key = f"{task_id}_Alto_{days_until_expiry}days"
                    if key not in self.notification_log:
                        send_notification("Importante", f"La tarea: {task['Descripcion']} es importante, tienes hasta el día {task['Fecha_de_expiracion']}")
                        self.notification_log[key] = True
                        save_notification_log(self.notification_log)
    
    def start_notification_check(self):
        def check_loop():
            self.check_notifications()
            self.root.after(3600000, check_loop)
        
        self.root.after(5000, check_loop)

def main():
    root = Tk()
    app = TaskManagerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()