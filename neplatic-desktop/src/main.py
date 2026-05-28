#!/usr/bin/env python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from tkinter import ttk, messagebox
from src.controllers.auth_controller import AuthController
from src.controllers.ruta_controller import RutaController
from src.utils.config import settings
from src.utils.logger import setup_logger

logger = setup_logger("neplatic-desktop")

class LoginWindow:
    def __init__(self, master):
        self.master = master
        master.title("Inicio de Sesión")
        master.geometry("300x200")
        
        ttk.Label(master, text="Usuario:").pack(pady=5)
        self.username_entry = ttk.Entry(master)
        self.username_entry.pack(pady=5)
        
        ttk.Label(master, text="Contraseña:").pack(pady=5)
        self.password_entry = ttk.Entry(master, show="*")
        self.password_entry.pack(pady=5)
        
        ttk.Button(master, text="Iniciar Sesión", command=self.login).pack(pady=20)
        
        self.auth_controller = AuthController()
    
    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        user = self.auth_controller.login(username, password)
        if user:
            messagebox.showinfo("Éxito", f"Bienvenido, {user.nombres}")
            self.master.withdraw()  # hide login window
            self.open_main_window(user)
        else:
            messagebox.showerror("Error", "Credenciales inválidas")
    
    def open_main_window(self, user):
        MainWindow(tk.Toplevel(self.master), user, self.master)

class MainWindow:
    def __init__(self, master, user, login_window):
        self.master = master
        self.user = user
        self.login_window = login_window
        master.title("Menú Principal")
        master.geometry("400x300")
        
        self.ruta_controller = RutaController(user)
        
        ttk.Label(master, text=f"Bienvenido, {user.nombres}", font=("Arial", 14)).pack(pady=20)
        
        btn_frame = ttk.Frame(master)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="Ver mis rutas", command=self.ver_rutas).grid(row=0, column=0, padx=10, pady=5)
        ttk.Button(btn_frame, text="Ver mis deudas", command=self.ver_deudas).grid(row=0, column=1, padx=10, pady=5)
        ttk.Button(btn_frame, text="Registrar notificación", command=self.registrar_notificacion).grid(row=1, column=0, padx=10, pady=5)
        ttk.Button(btn_frame, text="Salir", command=self.salir).grid(row=1, column=1, padx=10, pady=5)
        
        master.protocol("WM_DELETE_WINDOW", self.salir)
    
    def ver_rutas(self):
        rutas = self.ruta_controller.listar_rutas_usuario()
        if rutas:
            mensaje = "\n".join([f"Ruta {r.id_ruta}: {r.fecha_ruta} - {r.estado_ruta}" for r in rutas])
        else:
            mensaje = "No hay rutas"
        messagebox.showinfo("Mis Rutas", mensaje)
    
    def ver_deudas(self):
        deudas = self.ruta_controller.listar_deudas_asignadas()
        if deudas:
            mensaje = "\n".join([f"Deuda {d.id_deuda}: Lote {d.codigo_lote} - S/{d.saldo_pendiente}" for d in deudas])
        else:
            mensaje = "No hay deudas"
        messagebox.showinfo("Mis Deudas", mensaje)
    
    def registrar_notificacion(self):
        # Simple dialog to input data
        dialog = tk.Toplevel(self.master)
        dialog.title("Registrar Notificación")
        dialog.geometry("350x250")
        
        ttk.Label(dialog, text="ID deuda:").pack(pady=5)
        id_deuda_entry = ttk.Entry(dialog)
        id_deuda_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Dirección visitada:").pack(pady=5)
        direccion_entry = ttk.Entry(dialog)
        direccion_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Persona contactada:").pack(pady=5)
        persona_entry = ttk.Entry(dialog)
        persona_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Parentesco:").pack(pady=5)
        parentesco_entry = ttk.Entry(dialog)
        parentesco_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Estado:\n1.NOTIFICADO 2.AUSENTE 3.DIR_ERRADA 4.RECHAZADO 5.FALLECIDO").pack(pady=5)
        id_estado_entry = ttk.Entry(dialog)
        id_estado_entry.pack(pady=5)
        
        def submit():
            try:
                id_deuda = int(id_deuda_entry.get())
                direccion = direccion_entry.get()
                persona = persona_entry.get()
                parentesco = parentesco_entry.get()
                id_estado = int(id_estado_entry.get())
                self.ruta_controller.registrar_notificacion(id_deuda, direccion, persona, parentesco, id_estado)
                messagebox.showinfo("Éxito", "Notificación registrada")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Error: {e}")
        
        ttk.Button(dialog, text="Registrar", command=submit).pack(pady=10)
    
    def salir(self):
        if messagebox.askokcancel("Salir", "¿Está seguro de que desea salir?"):
            self.ruta_controller.close()
            self.master.destroy()
            self.login_window.destroy()

def main():
    root = tk.Tk()
    app = LoginWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()