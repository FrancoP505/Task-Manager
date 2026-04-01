import json
import os
from tkinter import *
from tkinter import ttk, messagebox
from datetime import datetime, date, timedelta
from plyer import notification
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

DATA_FILE = "data.json"
NOTIFICATION_LOG = "notifications.json"

SUCCESS = "success"
DANGER = "danger"
INFO = "info"
PRIMARY = "primary"
SECONDARY = "secondary"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"categories": [], "tasks": []}

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

def get_priority_label(priority):
    labels = {1: "Bajo", 2: "Medio", 3: "Alto"}
    return labels.get(priority, "Bajo")

class TaskManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestor de Tareas")
        self.root.geometry("1200x700")
        self.root.minsize(900, 500)
        
        self.data = load_data()
        self.notification_log = load_notification_log()
        
        self.setup_styles()
        self.setup_ui()
        self.refresh_categories()
        self.refresh_tasks()
        self.check_notifications()
        self.start_notification_check()
    
    def setup_styles(self):
        self.style = ttk.Style("cosmo")
        
        self.root.configure(bg="#f0f0f0")
        
        self.style.configure("Title.TLabel", font=("Helvetica", 14, "bold"), background="#f0f0f0")
        self.style.configure("Card.TFrame", background="white")
        self.style.configure("Treeview", rowheight=28, font=("Helvetica", 10))
        self.style.configure("Treeview.Heading", font=("Helvetica", 10, "bold"))
    
    def setup_ui(self):
        main_container = Frame(self.root, bg="#f0f0f0")
        main_container.pack(fill=BOTH, expand=True, padx=15, pady=15)
        
        header_frame = Frame(main_container, bg="#2c3e50", height=60)
        header_frame.pack(fill=X, pady=(0, 15))
        header_frame.pack_propagate(False)
        
        title_label = Label(header_frame, text="Gestor de Tareas", font=("Helvetica", 20, "bold"), 
                           bg="#2c3e50", fg="white")
        title_label.pack(side=LEFT, padx=20)
        
        content_frame = Frame(main_container, bg="#f0f0f0")
        content_frame.pack(fill=BOTH, expand=True)
        
        left_panel = Frame(content_frame, bg="white", relief=FLAT, borderwidth=1)
        left_panel.pack(side=LEFT, fill=Y, padx=(0, 10), pady=0)
        
        cat_header = Frame(left_panel, bg="#3498db")
        cat_header.pack(fill=X)
        Label(cat_header, text="Categorías", font=("Helvetica", 12, "bold"), 
              bg="#3498db", fg="white", pady=8).pack()
        
        self.category_listbox = Listbox(left_panel, font=("Helvetica", 11), 
                                        selectbackground="#3498db", selectforeground="white",
                                        borderwidth=0, highlightthickness=0,
                                        bg="#f8f9fa")
        self.category_listbox.pack(fill=BOTH, expand=True, padx=10, pady=10)
        self.category_listbox.bind("<<ListboxSelect>>", self.on_category_select)
        
        cat_btn_frame = Frame(left_panel, bg="white")
        cat_btn_frame.pack(fill=X, padx=10, pady=(0, 10))
        
        ttk.Button(cat_btn_frame, text="Agregar", command=self.add_category, 
                  bootstyle=SUCCESS, width=10).pack(side=LEFT, padx=2)
        ttk.Button(cat_btn_frame, text="Eliminar", command=self.delete_category, 
                  bootstyle=DANGER, width=10).pack(side=LEFT, padx=2)
        
        right_panel = Frame(content_frame, bg="white", relief=FLAT, borderwidth=1)
        right_panel.pack(side=LEFT, fill=BOTH, expand=True)
        
        task_header = Frame(right_panel, bg="#2ecc71")
        task_header.pack(fill=X)
        
        header_content = Frame(task_header, bg="#2ecc71")
        header_content.pack(fill=X, padx=15, pady=8)
        
        Label(header_content, text="Tareas", font=("Helvetica", 12, "bold"), 
              bg="#2ecc71", fg="white").pack(side=LEFT)
        
        self.filter_var = StringVar(value="all")
        filter_combo = ttk.Combobox(header_content, textvariable=self.filter_var, 
                                    values=["Todas", "Pendientes", "Completadas", "Expiradas"],
                                    state="readonly", width=12)
        filter_combo.pack(side=RIGHT)
        filter_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_tasks())
        
        task_actions = Frame(right_panel, bg="white", pady=10)
        task_actions.pack(fill=X, padx=15)
        
        ttk.Button(task_actions, text="Agregar Tarea", command=self.add_task, 
                  bootstyle=PRIMARY).pack(side=LEFT, padx=2)
        ttk.Button(task_actions, text="Cambiar Estado", command=self.toggle_task, 
                  bootstyle=INFO).pack(side=LEFT, padx=2)
        ttk.Button(task_actions, text="Eliminar", command=self.delete_task, 
                  bootstyle=DANGER).pack(side=LEFT, padx=2)
        
        columns = ("Descripción", "Prioridad", "Estado", "Creada", "Expira", "Categoría")
        self.task_tree = ttk.Treeview(right_panel, columns=columns, show="headings",
                                       style="Custom.Treeview")
        
        for col in columns:
            self.task_tree.heading(col, text=col)
        
        self.task_tree.column("Descripción", width=250)
        self.task_tree.column("Prioridad", width=80)
        self.task_tree.column("Estado", width=90)
        self.task_tree.column("Creada", width=100)
        self.task_tree.column("Expira", width=100)
        self.task_tree.column("Categoría", width=100)
        
        self.task_tree.tag_configure("Expirada", foreground="#e74c3c", font=("Helvetica", 10, "bold"))
        self.task_tree.tag_configure("Completada", foreground="#27ae60")
        self.task_tree.tag_configure("Pendiente", foreground="#2c3e50")
        
        scrollbar = ttk.Scrollbar(right_panel, orient=VERTICAL, command=self.task_tree.yview)
        self.task_tree.configure(yscrollcommand=scrollbar.set)
        
        self.task_tree.pack(fill=BOTH, expand=True, padx=15, pady=(0, 15))
        scrollbar.pack(side=RIGHT, fill=Y, pady=(0, 15), padx=(0, 15))
        
        self.task_tree.bind("<Double-Button-1>", self.on_task_double_click)
    
    def refresh_categories(self):
        self.category_listbox.delete(0, END)
        for cat in self.data["categories"]:
            self.category_listbox.insert(END, cat["name"])
    
    def get_selected_category_id(self):
        selection = self.category_listbox.curselection()
        if not selection:
            return None
        index = selection[0]
        return self.data["categories"][index]["id"]
    
    def on_category_select(self, event):
        self.refresh_tasks()
    
    def get_task_status(self, task):
        today = date.today()
        
        if task["completed"]:
            return "Completada"
        
        if task.get("expiry_date") and task.get("expiry_date") != "No expira":
            try:
                expiry = datetime.strptime(task["expiry_date"], "%Y-%m-%d").date()
                if expiry < today:
                    return "Expirada"
            except ValueError:
                pass
        
        return "Pendiente"
    
    def refresh_tasks(self):
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)
        
        selected_cat_id = self.get_selected_category_id()
        filter_status = self.filter_var.get().lower()
        
        for task in self.data["tasks"]:
            if selected_cat_id is not None and task["category_id"] != selected_cat_id:
                continue
            
            task_status = self.get_task_status(task)
            
            if filter_status == "pendientes" and task_status != "Pendiente":
                continue
            if filter_status == "completadas" and task_status != "Completada":
                continue
            if filter_status == "expiradas" and task_status != "Expirada":
                continue
            
            cat_name = ""
            for cat in self.data["categories"]:
                if cat["id"] == task["category_id"]:
                    cat_name = cat["name"]
                    break
            
            created_date = task.get("created_at", "")
            expiry_date = task.get("expiry_date", "")
            priority = task.get("priority", 1)
            priority_label = get_priority_label(priority)
            
            tag = "Pendiente"
            if task_status == "Completada":
                tag = "Completada"
            elif task_status == "Expirada":
                tag = "Expirada"
            
            self.task_tree.tag_configure("Expirada", foreground="#e74c3c", font=("Helvetica", 10, "bold"))
            self.task_tree.tag_configure("Completada", foreground="#27ae60")
            self.task_tree.tag_configure("Pendiente", foreground="#2c3e50")
            
            self.task_tree.insert("", END, values=(
                task["description"],
                priority_label,
                task_status,
                created_date,
                expiry_date,
                cat_name
            ), tags=(str(task["id"]), tag))
    
    def add_category(self):
        dialog = Toplevel(self.root)
        dialog.title("Agregar Categoría")
        dialog.geometry("400x150")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        
        main_frame = Frame(dialog, padx=20, pady=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        Label(main_frame, text="Nombre de Categoría:", font=("Helvetica", 11)).pack(anchor=W, pady=(0, 5))
        
        entry = Entry(main_frame, font=("Helvetica", 11), relief=FLAT, bg="#f8f9fa")
        entry.pack(fill=X, pady=(0, 15))
        entry.focus()
        
        btn_frame = Frame(main_frame)
        btn_frame.pack(fill=X)
        
        ttk.Button(btn_frame, text="Guardar", command=lambda: save_cat(), 
                   bootstyle=SUCCESS).pack(side=RIGHT, padx=2)
        ttk.Button(btn_frame, text="Cancelar", command=dialog.destroy, 
                   bootstyle=SECONDARY).pack(side=RIGHT, padx=2)
        
        def save_cat():
            name = entry.get().strip()
            if not name:
                messagebox.showwarning("Advertencia", "El nombre de la categoría no puede estar vacío")
                return
            
            new_cat = {"id": get_next_id(self.data["categories"]), "name": name}
            self.data["categories"].append(new_cat)
            save_data(self.data)
            self.refresh_categories()
            dialog.destroy()
        
        entry.bind("<Return>", lambda e: save_cat())
    
    def delete_category(self):
        selected = self.category_listbox.curselection()
        if not selected:
            messagebox.showwarning("Advertencia", "Selecciona una categoría para eliminar")
            return
        
        index = selected[0]
        cat_id = self.data["categories"][index]["id"]
        
        tasks_using = [t for t in self.data["tasks"] if t["category_id"] == cat_id]
        if tasks_using:
            if not messagebox.askyesno("Confirmar", 
                f"Esta categoría tiene {len(tasks_using)} tarea(s). ¿Eliminar categoría y sus tareas?"):
                return
        
        self.data["categories"].pop(index)
        self.data["tasks"] = [t for t in self.data["tasks"] if t["category_id"] != cat_id]
        save_data(self.data)
        self.refresh_categories()
        self.refresh_tasks()
    
    def add_task(self):
        if not self.data["categories"]:
            messagebox.showwarning("Advertencia", "Crea una categoría primero")
            return
        
        dialog = Toplevel(self.root)
        dialog.title("Agregar Tarea")
        dialog.geometry("420x420")
        dialog.transient(self.root)
        dialog.grab_set()
        
        main_frame = Frame(dialog, padx=25, pady=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        Label(main_frame, text="Descripción:", font=("Helvetica", 11)).pack(anchor=W, pady=(0, 5))
        desc_entry = Entry(main_frame, font=("Helvetica", 11), relief=FLAT, bg="#f8f9fa")
        desc_entry.pack(fill=X, pady=(0, 15))
        
        Label(main_frame, text="Prioridad:", font=("Helvetica", 11)).pack(anchor=W, pady=(0, 5))
        priority_var = IntVar(value=2)
        priority_frame = Frame(main_frame)
        priority_frame.pack(fill=X, pady=(0, 15))
        
        for val, label in [(1, "Bajo"), (2, "Medio"), (3, "Alto")]:
            Radiobutton(priority_frame, text=label, variable=priority_var, value=val,
                       font=("Helvetica", 10)).pack(side=LEFT, padx=15)
        
        Label(main_frame, text="Expira:", font=("Helvetica", 11)).pack(anchor=W, pady=(0, 5))
        expires_var = StringVar(value="yes")
        expires_frame = Frame(main_frame)
        expires_frame.pack(fill=X, pady=(0, 10))
        
        Radiobutton(expires_frame, text="Sí", variable=expires_var, value="yes",
                   font=("Helvetica", 10), command=lambda: toggle_date()).pack(side=LEFT, padx=15)
        Radiobutton(expires_frame, text="No", variable=expires_var, value="no",
                   font=("Helvetica", 10), command=lambda: toggle_date()).pack(side=LEFT, padx=15)
        
        Label(main_frame, text="Fecha de expiración (AAAA-MM-DD):", font=("Helvetica", 11)).pack(anchor=W, pady=(0, 5))
        date_entry = Entry(main_frame, font=("Helvetica", 11), relief=FLAT, bg="#f8f9fa")
        date_entry.pack(fill=X, pady=(0, 15))
        
        def toggle_date():
            if expires_var.get() == "yes":
                date_entry.config(state=NORMAL)
            else:
                date_entry.delete(0, END)
                date_entry.insert(0, "No expira")
                date_entry.config(state=DISABLED)
        
        toggle_date()
        
        Label(main_frame, text="Categoría:", font=("Helvetica", 11)).pack(anchor=W, pady=(0, 5))
        cat_var = StringVar()
        cat_combo = ttk.Combobox(main_frame, textvariable=cat_var, state="readonly",
                                  font=("Helvetica", 11))
        cat_combo["values"] = [c["name"] for c in self.data["categories"]]
        cat_combo.pack(fill=X, pady=(0, 20))
        if self.data["categories"]:
            cat_combo.current(0)
        
        def save_task():
            description = desc_entry.get().strip()
            if not description:
                messagebox.showwarning("Advertencia", "La descripción no puede estar vacía")
                return
            
            if expires_var.get() == "yes":
                expiry_date = date_entry.get().strip()
                if expiry_date and expiry_date != "No expira":
                    try:
                        datetime.strptime(expiry_date, "%Y-%m-%d")
                    except ValueError:
                        messagebox.showwarning("Advertencia", "Formato de fecha inválido. Usa AAAA-MM-DD")
                        return
            else:
                expiry_date = "No expira"
            
            category_name = cat_var.get()
            category_id = None
            for cat in self.data["categories"]:
                if cat["name"] == category_name:
                    category_id = cat["id"]
                    break
            
            created_at = date.today().strftime("%Y-%m-%d")
            
            new_task = {
                "id": get_next_id(self.data["tasks"]),
                "description": description,
                "completed": False,
                "priority": priority_var.get(),
                "created_at": created_at,
                "expiry_date": expiry_date,
                "category_id": category_id
            }
            self.data["tasks"].append(new_task)
            save_data(self.data)
            self.refresh_tasks()
            dialog.destroy()
        
        btn_frame = Frame(main_frame)
        btn_frame.pack(fill=X)
        
        ttk.Button(btn_frame, text="Guardar", command=save_task, bootstyle=SUCCESS).pack(side=RIGHT, padx=2)
        ttk.Button(btn_frame, text="Cancelar", command=dialog.destroy, bootstyle=SECONDARY).pack(side=RIGHT, padx=2)
    
    def on_task_double_click(self, event):
        selection = self.task_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        task_id = int(self.task_tree.item(item, "tags")[0])
        
        task = next((t for t in self.data["tasks"] if t["id"] == task_id), None)
        if not task:
            return
        
        dialog = Toplevel(self.root)
        dialog.title("Edit Task")
        dialog.geometry("420x420")
        dialog.transient(self.root)
        dialog.grab_set()
        
        main_frame = Frame(dialog, padx=25, pady=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        Label(main_frame, text="Description:", font=("Helvetica", 11)).pack(anchor=W, pady=(0, 5))
        desc_entry = Entry(main_frame, font=("Helvetica", 11), relief=FLAT, bg="#f8f9fa")
        desc_entry.insert(0, task["description"])
        desc_entry.pack(fill=X, pady=(0, 15))
        
        Label(main_frame, text="Priority:", font=("Helvetica", 11)).pack(anchor=W, pady=(0, 5))
        priority_var = IntVar(value=task.get("priority", 1))
        priority_frame = Frame(main_frame)
        priority_frame.pack(fill=X, pady=(0, 15))
        
        for val, label in [(1, "Low"), (2, "Medium"), (3, "High")]:
            Radiobutton(priority_frame, text=label, variable=priority_var, value=val,
                       font=("Helvetica", 10)).pack(side=LEFT, padx=15)
        
        current_expires = "yes" if task.get("expiry_date") and task.get("expiry_date") != "No expires" else "no"
        Label(main_frame, text="Expires:", font=("Helvetica", 11)).pack(anchor=W, pady=(0, 5))
        expires_var = StringVar(value=current_expires)
        expires_frame = Frame(main_frame)
        expires_frame.pack(fill=X, pady=(0, 10))
        
        Radiobutton(expires_frame, text="Yes", variable=expires_var, value="yes",
                   font=("Helvetica", 10), command=lambda: toggle_date()).pack(side=LEFT, padx=15)
        Radiobutton(expires_frame, text="No", variable=expires_var, value="no",
                   font=("Helvetica", 10), command=lambda: toggle_date()).pack(side=LEFT, padx=15)
        
        Label(main_frame, text="Expiry Date (YYYY-MM-DD):", font=("Helvetica", 11)).pack(anchor=W, pady=(0, 5))
        date_entry = Entry(main_frame, font=("Helvetica", 11), relief=FLAT, bg="#f8f9fa")
        if current_expires == "yes":
            date_entry.insert(0, task.get("expiry_date", ""))
        else:
            date_entry.insert(0, "No expires")
            date_entry.config(state=DISABLED)
        date_entry.pack(fill=X, pady=(0, 15))
        
        def toggle_date():
            if expires_var.get() == "yes":
                date_entry.config(state=NORMAL)
            else:
                date_entry.delete(0, END)
                date_entry.insert(0, "No expires")
                date_entry.config(state=DISABLED)
        
        Label(main_frame, text="Category:", font=("Helvetica", 11)).pack(anchor=W, pady=(0, 5))
        cat_var = StringVar()
        cat_combo = ttk.Combobox(main_frame, textvariable=cat_var, state="readonly",
                                  font=("Helvetica", 11))
        cat_combo["values"] = [c["name"] for c in self.data["categories"]]
        cat_combo.pack(fill=X, pady=(0, 20))
        
        for i, cat in enumerate(self.data["categories"]):
            if cat["id"] == task["category_id"]:
                cat_combo.current(i)
                break
        
        def save_task():
            description = desc_entry.get().strip()
            if not description:
                messagebox.showwarning("Advertencia", "La descripción no puede estar vacía")
                return
            
            if expires_var.get() == "yes":
                expiry_date = date_entry.get().strip()
                if expiry_date and expiry_date != "No expira":
                    try:
                        datetime.strptime(expiry_date, "%Y-%m-%d")
                    except ValueError:
                        messagebox.showwarning("Advertencia", "Formato de fecha inválido. Usa AAAA-MM-DD")
                        return
            else:
                expiry_date = "No expira"
            
            category_name = cat_var.get()
            category_id = None
            for cat in self.data["categories"]:
                if cat["name"] == category_name:
                    category_id = cat["id"]
                    break
            
            task["description"] = description
            task["priority"] = priority_var.get()
            task["expiry_date"] = expiry_date
            task["category_id"] = category_id
            
            save_data(self.data)
            self.refresh_tasks()
            dialog.destroy()
    
    def toggle_task(self):
        selection = self.task_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Selecciona una tarea para cambiar su estado")
            return
        
        item = selection[0]
        task_id = int(self.task_tree.item(item, "tags")[0])
        
        for task in self.data["tasks"]:
            if task["id"] == task_id:
                task["completed"] = not task["completed"]
                break
        
        save_data(self.data)
        self.refresh_tasks()
    
    def delete_task(self):
        selection = self.task_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Selecciona una tarea para eliminar")
            return
        
        item = selection[0]
        task_id = int(self.task_tree.item(item, "tags")[0])
        
        self.data["tasks"] = [t for t in self.data["tasks"] if t["id"] != task_id]
        save_data(self.data)
        self.refresh_tasks()
    
    def check_notifications(self):
        today = date.today()
        
        for task in self.data["tasks"]:
            if task["completed"]:
                continue
            
            if not task.get("expiry_date") or task.get("expiry_date") == "No expira":
                continue
            
            try:
                expiry = datetime.strptime(task["expiry_date"], "%Y-%m-%d").date()
            except ValueError:
                continue
            
            task_id = str(task["id"])
            days_until_expiry = (expiry - today).days
            
            if task.get("priority") == 2:
                if days_until_expiry == 2:
                    key = f"{task_id}_medium_2days"
                    if key not in self.notification_log:
                        send_notification("Recordatorio", f"Tienes dos días para terminar la actividad: {task['description']}")
                        self.notification_log[key] = True
                        save_notification_log(self.notification_log)
            
            elif task.get("priority") == 3:
                if 1 <= days_until_expiry <= 5:
                    key = f"{task_id}_high_{days_until_expiry}days"
                    if key not in self.notification_log:
                        send_notification("Importante", f"La tarea: {task['description']} es importante, tienes hasta el día {task['expiry_date']}")
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