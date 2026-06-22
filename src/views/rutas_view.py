import tkinter as tk
import threading
from tkinter import messagebox, ttk
import webbrowser

from src.controllers.ruta_controller import RutaController
from src.services.sync_service import SyncService
from src.ui.modern_widgets import PALETTE, HoverButton, style_treeview


class RutasView(tk.Frame):
    DEBT_COLUMNS = [
        "id_deuda",
        "contribuyente",
        "documento",
        "tipo_tributo",
        "codigo_lote",
        "sector",
        "direccion_predio",
        "saldo",
        "estado_cobranza",
    ]

    def __init__(self, parent, current_user, mode="rutas"):
        super().__init__(parent, bg=PALETTE["app_bg"])
        self.current_user = current_user
        self.mode = mode
        self.controller = RutaController(current_user)
        self.sync_service = SyncService()
        self._all_routes = []
        self._all_debts = []
        self._refresh_token = 0
        self._build()

    def _build(self):
        header = tk.Frame(self, bg=PALETTE["app_bg"])
        header.pack(fill=tk.X, padx=8, pady=(0, 12))
        title = {
            "rutas": "Mis rutas",
            "deudas": "Deudas",
        }.get(self.mode, "Rutas")
        subtitle = {
            "rutas": "Listado de rutas asignadas y estado general.",
            "deudas": "Deudas asociadas a la ruta actual.",
        }.get(self.mode, "Modulo operativo")
        tk.Label(header, text=title, bg=PALETTE["app_bg"], fg=PALETTE["text"], font=("Segoe UI Semibold", 18)).pack(anchor="w")
        tk.Label(header, text=subtitle, bg=PALETTE["app_bg"], fg=PALETTE["text_muted"], font=("Segoe UI", 9)).pack(anchor="w", pady=(4, 0))

        self._build_listings()

    def _build_listings(self):
        actions = tk.Frame(self, bg=PALETTE["app_bg"])
        actions.pack(fill=tk.X, padx=8, pady=(0, 10))
        
        # Búsqueda
        search_label = "Buscar DNI/RUC, nombre, predio, sector, manzana o lote:" if self.mode == "deudas" else "Buscar:"
        tk.Label(actions, text=search_label, bg=PALETTE["app_bg"], fg=PALETTE["text"], font=("Segoe UI Semibold", 9)).pack(side=tk.LEFT, padx=(0, 4))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(actions, textvariable=self.search_var, style="Modern.TEntry", width=25)
        search_entry.pack(side=tk.LEFT, padx=(0, 12))
        search_entry.bind("<KeyRelease>", lambda _e: self._apply_search())
        
        # Acciones según el modo
        if self.mode == "rutas":
            HoverButton(actions, text="Asignar Ruta a Notificador", command=self.asignar_ruta_dialog, bg=PALETTE["accent"], hover_bg=PALETTE["accent_hover"], border=PALETTE["accent"], font=("Segoe UI Semibold", 9), padx=12, pady=8).pack(side=tk.LEFT, padx=(0, 8))
            HoverButton(actions, text="Ver ubicacion de ruta", command=self.open_route_location_detail, bg=PALETTE["surface_soft"], fg=PALETTE["text"], hover_bg="#e2e8f0", active_bg="#e2e8f0", border=PALETTE["border"], font=("Segoe UI Semibold", 9), padx=12, pady=8).pack(side=tk.LEFT, padx=(0, 8))
        
        # Botón general
        HoverButton(actions, text="Sincronizar cola", command=self.sync_queue, bg=PALETTE["accent"], hover_bg=PALETTE["accent_hover"], border=PALETTE["accent"], font=("Segoe UI Semibold", 9), padx=12, pady=8).pack(side=tk.LEFT)

        self.summary = tk.Frame(self, bg=PALETTE["app_bg"])
        self.summary.pack(fill=tk.X, padx=8, pady=(0, 10))

        card = tk.Frame(self, bg=PALETTE["surface"], highlightbackground=PALETTE["border"], highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        if self.mode == "rutas":
            self.routes_tab = tk.Frame(card, bg=PALETTE["surface"])
            self.routes_tab.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            self._build_tree_tab(self.routes_tab, "routes_tree", ["id_ruta", "fecha_ruta", "estado_ruta", "total_deudas", "deudas_atendidas", "distancia_estimada_km"])
        elif self.mode == "deudas":
            self.debts_tab = tk.Frame(card, bg=PALETTE["surface"])
            self.debts_tab.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            # Admin ve todas las deudas del año actual con columnas ricas
            self._build_tree_tab(self.debts_tab, "deudas_tree", self.DEBT_COLUMNS)

        self.refresh()

    def _build_tree_tab(self, parent, attr, columns):
        frame = tk.Frame(parent, bg=PALETTE["surface"])
        frame.pack(fill=tk.BOTH, expand=True)
        tree = ttk.Treeview(frame, columns=columns, show="headings", style="Modern.Treeview")
        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview, style="Modern.Vertical.TScrollbar")
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        style_treeview(tree, ttk.Style())
        if attr == "routes_tree":
            tree.bind("<Double-1>", lambda _e: self.open_route_location_detail())
        if attr == "deudas_tree":
            tree.bind("<Double-1>", lambda _e: self.open_debt_detail())
        setattr(self, attr, tree)

    def _build_notificar(self):
        card = tk.Frame(self, bg=PALETTE["surface"], highlightbackground=PALETTE["border"], highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        inner = tk.Frame(card, bg=PALETTE["surface"], padx=18, pady=18)
        inner.pack(fill=tk.BOTH, expand=True)

        def field(label, row, show=None):
            tk.Label(inner, text=label, bg=PALETTE["surface"], fg=PALETTE["text"], font=("Segoe UI Semibold", 10)).grid(row=row * 2, column=0, sticky="w", pady=(0, 6))
            entry = ttk.Entry(inner, style="Modern.TEntry", show=show)
            entry.grid(row=row * 2 + 1, column=0, sticky="ew", pady=(0, 12))
            return entry

        inner.columnconfigure(0, weight=1)
        self.id_deuda_entry = field("ID de deuda", 0)
        self.direccion_entry = field("Direccion exacta", 1)
        self.persona_entry = field("Persona contactada", 2)
        self.parentesco_entry = field("Parentesco / relacion", 3)

        tk.Label(inner, text="Resultado de la visita", bg=PALETTE["surface"], fg=PALETTE["text"], font=("Segoe UI Semibold", 10)).grid(row=8, column=0, sticky="w", pady=(0, 6))
        self.estado_cb = ttk.Combobox(
            inner,
            values=[
                "1 - NOTIFICADO",
                "2 - AUSENTE",
                "3 - DIRECCION ERRADA",
                "4 - RECHAZADO",
                "5 - CONTRIBUYENTE FALLECIDO",
            ],
            state="readonly",
            style="Modern.TCombobox",
        )
        self.estado_cb.grid(row=9, column=0, sticky="ew", pady=(0, 14))
        self.estado_cb.current(0)

        HoverButton(inner, text="Guardar visita", command=self.submit, bg=PALETTE["accent"], hover_bg=PALETTE["accent_hover"], border=PALETTE["accent"], font=("Segoe UI Semibold", 10), padx=14, pady=10).grid(row=10, column=0, sticky="e", pady=(10, 0))

    def refresh(self):
        self._refresh_token += 1
        token = self._refresh_token
        self._show_loading()
        threading.Thread(target=self._load_data_async, args=(token,), daemon=True).start()

    def _show_loading(self):
        self._render_stats_cards("...", "...", "...")
        if self.mode == "rutas" and hasattr(self, "routes_tree"):
            for item in self.routes_tree.get_children():
                self.routes_tree.delete(item)
            self.routes_tree.insert("", "end", values=("Cargando...", "", "", "", "", ""))
        elif self.mode == "deudas" and hasattr(self, "deudas_tree"):
            self._configure_debt_tree()
            for item in self.deudas_tree.get_children():
                self.deudas_tree.delete(item)
            self.deudas_tree.insert("", "end", values=("Cargando...", "", "", "", "", "", "", "", ""))

    def _load_data_async(self, token):
        try:
            routes = self.controller.listar_rutas_usuario()
            debts = self.controller.listar_deudas_anio_actual() if self.current_user.id_rol in (1, 2) else self.controller.listar_deudas_asignadas()
            pending_sync = len(self.sync_service.obtener_cola_local().get("pending", []))
            table_rows = routes if self.mode == "rutas" else debts
            self.after(0, lambda: self._apply_async_data(token, routes, debts, pending_sync, table_rows, None))
        except Exception as exc:
            self.after(0, lambda error=exc: self._apply_async_data(token, [], [], 0, [], error))

    def _apply_async_data(self, token, routes, debts, pending_sync, table_rows, error):
        if token != self._refresh_token or not self.winfo_exists():
            return
        self._render_stats_cards(len(routes), len(debts), pending_sync)
        if error:
            messagebox.showerror("Rutas", f"No fue posible cargar la informacion.\n\nDetalle: {error}", parent=self)
        if self.mode == "rutas":
            self._render_routes_rows(table_rows, error)
        elif self.mode == "deudas":
            self._render_debt_rows(table_rows, error)

    def _render_stats_cards(self, routes_count, debts_count, pending_sync):
        for widget in self.summary.winfo_children():
            widget.destroy()
        cards = [
            ("Rutas", routes_count, "Asignadas al usuario"),
            ("Deudas", debts_count, "Pendientes de visita"),
            ("Cola", pending_sync, "Pendientes por sincronizar"),
        ]
        for index, (label, value, meta) in enumerate(cards):
            frame = tk.Frame(self.summary, bg=PALETTE["surface"], highlightbackground=PALETTE["border"], highlightthickness=1)
            frame.grid(row=0, column=index, sticky="nsew", padx=(0 if index == 0 else 8, 0))
            tk.Label(frame, text=label, bg=PALETTE["surface"], fg=PALETTE["text_muted"], font=("Segoe UI", 9)).pack(anchor="w", padx=14, pady=(12, 4))
            tk.Label(frame, text=str(value), bg=PALETTE["surface"], fg=PALETTE["text"], font=("Segoe UI Semibold", 20)).pack(anchor="w", padx=14)
            tk.Label(frame, text=meta, bg=PALETTE["surface"], fg=PALETTE["text_muted"], font=("Segoe UI", 9)).pack(anchor="w", padx=14, pady=(0, 12))

    def _render_routes_rows(self, routes, error=None):
        for item in self.routes_tree.get_children():
            self.routes_tree.delete(item)
        self.routes_tree["columns"] = ["id_ruta", "fecha_ruta", "estado_ruta", "total_deudas", "deudas_atendidas", "distancia_estimada_km"]
        headings = {
            "id_ruta": "ID ruta",
            "fecha_ruta": "Fecha",
            "estado_ruta": "Estado",
            "total_deudas": "Total",
            "deudas_atendidas": "Atendidas",
            "distancia_estimada_km": "Km estimados",
        }
        for col, text in headings.items():
            self.routes_tree.heading(col, text=text)
            self.routes_tree.column(col, width=130, anchor="center")
        if error:
            self._all_routes = []
            self.routes_tree.insert("", "end", values=(f"Error: {error}", "", "", "", "", ""))
            return
        self._all_routes = routes or []
        if not self._all_routes:
            self.routes_tree.insert("", "end", values=("Sin datos", "", "", "", "", ""))
            return
        for count, route in enumerate(self._all_routes):
            if count >= 500:
                break
            self.routes_tree.insert("", "end", values=(
                route.id_ruta,
                getattr(route, "fecha_ruta", ""),
                getattr(route, "estado_ruta", ""),
                getattr(route, "total_deudas", 0),
                getattr(route, "deudas_atendidas", 0),
                getattr(route, "distancia_estimada_km", ""),
            ))

    def _configure_debt_tree(self):
        self.deudas_tree["columns"] = self.DEBT_COLUMNS
        headings = {
            "id_deuda": "ID",
            "contribuyente": "Contribuyente",
            "documento": "Documento",
            "tipo_tributo": "Tributo",
            "codigo_lote": "Predio",
            "sector": "Sector",
            "direccion_predio": "Direccion predio",
            "saldo": "Saldo",
            "estado_cobranza": "Estado",
        }
        col_widths = {
            "id_deuda": 70,
            "contribuyente": 180,
            "documento": 105,
            "tipo_tributo": 120,
            "codigo_lote": 100,
            "sector": 130,
            "direccion_predio": 210,
            "saldo": 115,
            "estado_cobranza": 130,
        }
        for col in self.DEBT_COLUMNS:
            self.deudas_tree.heading(col, text=headings[col])
            self.deudas_tree.column(col, width=col_widths.get(col, 120), anchor="center")

    def _render_debt_rows(self, debts, error=None):
        self._configure_debt_tree()
        for item in self.deudas_tree.get_children():
            self.deudas_tree.delete(item)
        if error:
            self._all_debts = []
            self.deudas_tree.insert("", "end", values=(f"Error: {error}", "", "", "", "", "", "", "", ""))
            return
        self._all_debts = debts or []
        if not self._all_debts:
            self.deudas_tree.insert("", "end", values=self._empty_debt_values())
            return
        for count, debt in enumerate(self._all_debts):
            if count >= 500:
                break
            self.deudas_tree.insert("", "end", values=self._debt_row_values(debt))

    def _apply_search(self):
        query = self.search_var.get().lower()
        
        if self.mode == "rutas":
            for item in self.routes_tree.get_children():
                self.routes_tree.delete(item)
            if self._all_routes:
                count = 0
                for route in self._all_routes:
                    if count >= 500: break
                    values = (
                        route.id_ruta,
                        getattr(route, "fecha_ruta", ""),
                        getattr(route, "estado_ruta", ""),
                        getattr(route, "total_deudas", 0),
                        getattr(route, "deudas_atendidas", 0),
                        getattr(route, "distancia_estimada_km", ""),
                    )
                    if not query or any(query in str(v).lower() for v in values):
                        self.routes_tree.insert("", "end", values=values)
                        count += 1
            else:
                self.routes_tree.insert("", "end", values=("Sin datos", "", "", "", "", ""))
                
        elif self.mode == "deudas":
            for item in self.deudas_tree.get_children():
                self.deudas_tree.delete(item)
            if self._all_debts:
                count = 0
                for debt in self._all_debts:
                    if count >= 500: break
                    values = self._debt_row_values(debt)
                    searchable = self._debt_search_values(debt)
                    if not query or any(query in str(v).lower() for v in searchable):
                        self.deudas_tree.insert("", "end", values=values)
                        count += 1
            else:
                self.deudas_tree.insert("", "end", values=self._empty_debt_values())

    def _format_money(self, value):
        try:
            return f"S/ {float(value or 0):,.2f}"
        except (TypeError, ValueError):
            return "S/ 0.00"

    def _debt_row_values(self, debt):
        return (
            getattr(debt, "id_deuda", ""),
            getattr(debt, "contribuyente", "") or "",
            getattr(debt, "documento", "") or "",
            getattr(debt, "tipo_tributo", "") or "",
            getattr(debt, "codigo_lote", "") or "",
            getattr(debt, "sector", "") or "",
            getattr(debt, "direccion_predio", "") or "",
            self._format_money(getattr(debt, "saldo", 0)),
            getattr(debt, "estado_cobranza", "") or "",
        )

    def _debt_search_values(self, debt):
        return self._debt_row_values(debt) + (
            getattr(debt, "manzana", "") or "",
            getattr(debt, "direccion_fiscal", "") or "",
            getattr(debt, "uso_predio", "") or "",
            getattr(debt, "anio_tributo", "") or "",
            getattr(debt, "periodo", "") or "",
        )

    def _empty_debt_values(self):
        return ("Sin datos", "", "", "", "", "", "", "", "")

    def _selected_route_id(self):
        selected = self.routes_tree.selection() if hasattr(self, "routes_tree") else ()
        if not selected:
            return None
        values = self.routes_tree.item(selected[0], "values")
        if not values or values[0] in ("Sin datos", "Cargando...", "") or str(values[0]).startswith("Error:"):
            return None
        try:
            return int(values[0])
        except (TypeError, ValueError):
            return None

    def open_route_location_detail(self):
        route_id = self._selected_route_id()
        if route_id is None:
            messagebox.showinfo("Rutas", "Selecciona una ruta primero.", parent=self)
            return

        dialog = tk.Toplevel(self)
        dialog.title(f"Ubicacion de ruta {route_id}")
        dialog.geometry("1120x620")
        dialog.transient(self)
        dialog.grab_set()
        dialog.configure(bg=PALETTE["app_bg"])

        shell = tk.Frame(dialog, bg=PALETTE["surface"], highlightbackground=PALETTE["border"], highlightthickness=1)
        shell.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)
        top = tk.Frame(shell, bg=PALETTE["surface"], padx=14, pady=12)
        top.pack(fill=tk.X)
        tk.Label(top, text=f"Ruta {route_id} - ubicacion de contribuyentes", bg=PALETTE["surface"], fg=PALETTE["text"], font=("Segoe UI Semibold", 15)).pack(side=tk.LEFT)
        status = tk.Label(top, text="Cargando...", bg=PALETTE["surface"], fg=PALETTE["text_muted"], font=("Segoe UI", 9))
        status.pack(side=tk.LEFT, padx=(14, 0))

        table_wrap = tk.Frame(shell, bg=PALETTE["surface"])
        table_wrap.pack(fill=tk.BOTH, expand=True, padx=14, pady=(0, 14))
        columns = ("orden", "contribuyente", "documento", "predio", "direccion", "sector", "manzana", "coordenadas", "saldo", "visitado")
        tree = ttk.Treeview(table_wrap, columns=columns, show="headings", style="Modern.Treeview")
        vsb = ttk.Scrollbar(table_wrap, orient="vertical", command=tree.yview, style="Modern.Vertical.TScrollbar")
        hsb = ttk.Scrollbar(table_wrap, orient="horizontal", command=tree.xview, style="Modern.Horizontal.TScrollbar")
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        tree.pack(side="left", fill="both", expand=True)
        style_treeview(tree, ttk.Style())

        headings = {
            "orden": "Orden",
            "contribuyente": "Contribuyente",
            "documento": "DNI/RUC",
            "predio": "Predio",
            "direccion": "Direccion",
            "sector": "Sector",
            "manzana": "Manzana",
            "coordenadas": "Coordenadas",
            "saldo": "Saldo",
            "visitado": "Visitado",
        }
        widths = {
            "orden": 70,
            "contribuyente": 180,
            "documento": 105,
            "predio": 100,
            "direccion": 230,
            "sector": 130,
            "manzana": 100,
            "coordenadas": 170,
            "saldo": 110,
            "visitado": 90,
        }
        for col in columns:
            tree.heading(col, text=headings[col])
            tree.column(col, width=widths[col], anchor="center")
        tree.insert("", "end", values=("Cargando...", "", "", "", "", "", "", "", "", ""))

        actions = tk.Frame(shell, bg=PALETTE["surface"], padx=14, pady=(0, 14))
        actions.pack(fill=tk.X)

        def selected_row():
            selected = tree.selection()
            if not selected:
                return None
            values = tree.item(selected[0], "values")
            return values if values and values[0] not in ("Cargando...", "Sin datos") else None

        def open_selected_map():
            values = selected_row()
            if not values:
                messagebox.showinfo("Rutas", "Selecciona una ubicacion primero.", parent=dialog)
                return
            coords = values[7]
            if not coords or coords == "Sin coordenadas":
                messagebox.showinfo("Rutas", "El predio seleccionado no tiene coordenadas registradas.", parent=dialog)
                return
            webbrowser.open(f"https://www.google.com/maps?q={coords}")

        HoverButton(actions, text="Abrir coordenadas", command=open_selected_map, bg=PALETTE["accent"], hover_bg=PALETTE["accent_hover"], border=PALETTE["accent"], font=("Segoe UI Semibold", 9), padx=12, pady=8).pack(side=tk.LEFT)
        HoverButton(actions, text="Cerrar", command=dialog.destroy, bg=PALETTE["surface_soft"], fg=PALETTE["text"], hover_bg="#e2e8f0", active_bg="#e2e8f0", border=PALETTE["border"], font=("Segoe UI Semibold", 9), padx=12, pady=8).pack(side=tk.RIGHT)

        def load_detail():
            try:
                rows = self.controller.obtener_detalle_ubicacion_ruta(route_id)
                dialog.after(0, lambda: apply_rows(rows, None))
            except Exception as exc:
                dialog.after(0, lambda error=exc: apply_rows([], error))

        def apply_rows(rows, error):
            if not dialog.winfo_exists():
                return
            for item in tree.get_children():
                tree.delete(item)
            if error:
                status.config(text="Error al cargar")
                tree.insert("", "end", values=(f"Error: {error}", "", "", "", "", "", "", "", "", ""))
                return
            status.config(text=f"{len(rows)} contribuyentes cargados")
            if not rows:
                tree.insert("", "end", values=("Sin datos", "", "", "", "", "", "", "", "", ""))
                return
            for row in rows:
                lat = getattr(row, "latitud", None)
                lon = getattr(row, "longitud", None)
                coords = f"{lat},{lon}" if lat is not None and lon is not None else "Sin coordenadas"
                tree.insert("", "end", values=(
                    getattr(row, "orden_visita", ""),
                    getattr(row, "contribuyente", "") or "",
                    getattr(row, "documento", "") or "",
                    getattr(row, "codigo_lote", "") or "",
                    getattr(row, "direccion_predio", "") or "",
                    getattr(row, "sector", "") or "",
                    getattr(row, "manzana", "") or "",
                    coords,
                    self._format_money(getattr(row, "saldo", 0)),
                    "SI" if getattr(row, "visitado", False) else "NO",
                ))

        threading.Thread(target=load_detail, daemon=True).start()

    def asignar_ruta_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("Asignar Ruta por Sector")
        dialog.geometry("450x300")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        dialog.configure(bg=PALETTE["app_bg"])

        frame = tk.Frame(dialog, bg=PALETTE["surface"], highlightbackground=PALETTE["border"], highlightthickness=1, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)
        
        tk.Label(frame, text="Asignar Nuevo Sector", bg=PALETTE["surface"], fg=PALETTE["text"], font=("Segoe UI Semibold", 14)).pack(anchor="w", pady=(0, 15))

        notificadores = self.controller.obtener_notificadores()
        sectores = self.controller.obtener_sectores()

        if not notificadores or not sectores:
            messagebox.showerror("Error", "Debe haber notificadores y sectores registrados en el sistema.", parent=dialog)
            dialog.destroy()
            return

        tk.Label(frame, text="Notificador:", bg=PALETTE["surface"], fg=PALETTE["text"], font=("Segoe UI Semibold", 9)).pack(anchor="w", pady=(0, 5))
        notificador_var = tk.StringVar()
        notificador_cb = ttk.Combobox(frame, textvariable=notificador_var, values=[f"{n.id_usuario} - {n.nombres} {n.apellidos}" for n in notificadores], style="Modern.TCombobox", state="readonly")
        notificador_cb.pack(fill=tk.X, pady=(0, 15))
        notificador_cb.current(0)

        tk.Label(frame, text="Sector:", bg=PALETTE["surface"], fg=PALETTE["text"], font=("Segoe UI Semibold", 9)).pack(anchor="w", pady=(0, 5))
        sector_var = tk.StringVar()
        sector_cb = ttk.Combobox(frame, textvariable=sector_var, values=[f"{s.id_sector} - {s.nombre}" for s in sectores], style="Modern.TCombobox", state="readonly")
        sector_cb.pack(fill=tk.X, pady=(0, 20))
        sector_cb.current(0)

        def apply_asignacion():
            id_usuario = int(notificador_var.get().split(" - ")[0])
            id_sector = int(sector_var.get().split(" - ")[0])
            
            res = self.controller.asignar_sector(id_usuario, id_sector)
            if res.get("success"):
                messagebox.showinfo("Éxito", res.get("message"), parent=dialog)
                self.refresh()
                dialog.destroy()
            else:
                messagebox.showerror("Error", res.get("message"), parent=dialog)

        btn_frame = tk.Frame(frame, bg=PALETTE["surface"])
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)
        HoverButton(btn_frame, text="Cancelar", command=dialog.destroy, bg=PALETTE["surface_soft"], fg=PALETTE["text"], hover_bg="#e2e8f0", active_bg="#e2e8f0", border=PALETTE["border"], font=("Segoe UI Semibold", 10), padx=12, pady=8).pack(side=tk.LEFT)
        HoverButton(btn_frame, text="Asignar", command=apply_asignacion, bg=PALETTE["accent"], hover_bg=PALETTE["accent_hover"], border=PALETTE["accent"], font=("Segoe UI Semibold", 10), padx=12, pady=8).pack(side=tk.RIGHT)

    def _render_stats(self):
        for widget in self.summary.winfo_children():
            widget.destroy()

        try:
            routes = self.controller.listar_rutas_usuario()
            if self.current_user.id_rol in (1, 2):
                debts = self.controller.listar_deudas_anio_actual()
            else:
                debts = self.controller.listar_deudas_asignadas()
            pending_sync = len(self.sync_service.obtener_cola_local().get("pending", []))
        except Exception as exc:
            messagebox.showerror("Rutas", f"No fue posible cargar la informacion.\n\nDetalle: {exc}", parent=self)
            routes = []
            debts = []
            pending_sync = 0

        cards = [
            ("Rutas", len(routes), "Asignadas al usuario"),
            ("Deudas", len(debts), "Pendientes de visita"),
            ("Cola", pending_sync, "Pendientes por sincronizar"),
        ]
        for index, (label, value, meta) in enumerate(cards):
            frame = tk.Frame(self.summary, bg=PALETTE["surface"], highlightbackground=PALETTE["border"], highlightthickness=1)
            frame.grid(row=0, column=index, sticky="nsew", padx=(0 if index == 0 else 8, 0))
            tk.Label(frame, text=label, bg=PALETTE["surface"], fg=PALETTE["text_muted"], font=("Segoe UI", 9)).pack(anchor="w", padx=14, pady=(12, 4))
            tk.Label(frame, text=str(value), bg=PALETTE["surface"], fg=PALETTE["text"], font=("Segoe UI Semibold", 20)).pack(anchor="w", padx=14)
            tk.Label(frame, text=meta, bg=PALETTE["surface"], fg=PALETTE["text_muted"], font=("Segoe UI", 9)).pack(anchor="w", padx=14, pady=(0, 12))

    def _load_routes(self):
        for item in self.routes_tree.get_children():
            self.routes_tree.delete(item)
        try:
            routes = self.controller.listar_rutas_usuario()
            self.routes_tree["columns"] = ["id_ruta", "fecha_ruta", "estado_ruta", "total_deudas", "deudas_atendidas", "distancia_estimada_km"]
            headings = {
                "id_ruta": "ID ruta",
                "fecha_ruta": "Fecha",
                "estado_ruta": "Estado",
                "total_deudas": "Total",
                "deudas_atendidas": "Atendidas",
                "distancia_estimada_km": "Km estimados",
            }
            for col, text in headings.items():
                self.routes_tree.heading(col, text=text)
                self.routes_tree.column(col, width=130, anchor="center")
            if routes:
                self._all_routes = routes
                count = 0
                for route in routes:
                    if count >= 500: break
                    self.routes_tree.insert("", "end", values=(
                        route.id_ruta,
                        getattr(route, "fecha_ruta", ""),
                        getattr(route, "estado_ruta", ""),
                        getattr(route, "total_deudas", 0),
                        getattr(route, "deudas_atendidas", 0),
                        getattr(route, "distancia_estimada_km", ""),
                    ))
                    count += 1
            else:
                self.routes_tree.insert("", "end", values=("Sin datos", "", "", "", "", ""))
        except Exception as exc:
            self._all_routes = []
            self.routes_tree.insert("", "end", values=(f"Error: {exc}", "", "", "", "", ""))

    def _load_debts_legacy(self):
        for item in self.deudas_tree.get_children():
            self.deudas_tree.delete(item)
        try:
            is_admin = self.current_user.id_rol in (1, 2)
            
            if is_admin:
                debts = self.controller.listar_deudas_anio_actual()
                self.deudas_tree["columns"] = ["id_deuda", "contribuyente", "documento", "codigo_lote", "direccion", "saldo", "estado_cobranza"]
                headings = {
                    "id_deuda": "ID",
                    "contribuyente": "Contribuyente",
                    "documento": "Documento",
                    "codigo_lote": "Lote",
                    "direccion": "Dirección",
                    "saldo": "Saldo Pendiente",
                    "estado_cobranza": "Estado",
                }
                col_widths = {"id_deuda": 60, "contribuyente": 180, "documento": 100, "codigo_lote": 100, "direccion": 180, "saldo": 120, "estado_cobranza": 130}
                for col, text in headings.items():
                    self.deudas_tree.heading(col, text=text)
                    self.deudas_tree.column(col, width=col_widths.get(col, 120), anchor="center")
                if debts:
                    self._all_debts = debts
                    for count, debt in enumerate(debts):
                        if count >= 500: break
                        saldo_val = getattr(debt, "saldo", 0) or 0
                        saldo_fmt = f"S/ {float(saldo_val):,.2f}"
                        self.deudas_tree.insert("", "end", values=(
                            debt.id_deuda,
                            getattr(debt, "contribuyente", ""),
                            getattr(debt, "documento", ""),
                            getattr(debt, "codigo_lote", ""),
                            getattr(debt, "direccion", "") or "",
                            saldo_fmt,
                            getattr(debt, "estado_cobranza", ""),
                        ))
                else:
                    self._all_debts = []
                    self.deudas_tree.insert("", "end", values=("Sin datos", "", "", "", "", "", ""))
            else:
                debts = self.controller.listar_deudas_asignadas()
                self.deudas_tree["columns"] = ["id_deuda", "codigo_lote", "orden_visita", "visitado"]
                headings = {"id_deuda": "ID deuda", "codigo_lote": "Lote", "orden_visita": "Orden", "visitado": "Visitado"}
                for col, text in headings.items():
                    self.deudas_tree.heading(col, text=text)
                    self.deudas_tree.column(col, width=150, anchor="center")
                if debts:
                    self._all_debts = debts
                    for count, debt in enumerate(debts):
                        if count >= 500: break
                        self.deudas_tree.insert("", "end", values=(
                            debt.id_deuda,
                            getattr(debt, "codigo_lote", ""),
                            getattr(debt, "orden_visita", ""),
                            "SI" if getattr(debt, "visitado", False) else "NO",
                        ))
                else:
                    self._all_debts = []
                    self.deudas_tree.insert("", "end", values=("Sin datos", "", "", ""))
        except Exception as exc:
            self._all_debts = []
            self.deudas_tree.insert("", "end", values=(f"Error: {exc}", "", "", ""))

    def _load_debts(self):
        for item in self.deudas_tree.get_children():
            self.deudas_tree.delete(item)
        try:
            debts = self.controller.listar_deudas_anio_actual() if self.current_user.id_rol in (1, 2) else self.controller.listar_deudas_asignadas()
            self.deudas_tree["columns"] = self.DEBT_COLUMNS
            headings = {
                "id_deuda": "ID",
                "contribuyente": "Contribuyente",
                "documento": "Documento",
                "tipo_tributo": "Tributo",
                "codigo_lote": "Predio",
                "sector": "Sector",
                "direccion_predio": "Direccion predio",
                "saldo": "Saldo",
                "estado_cobranza": "Estado",
            }
            col_widths = {
                "id_deuda": 70,
                "contribuyente": 180,
                "documento": 105,
                "tipo_tributo": 120,
                "codigo_lote": 100,
                "sector": 130,
                "direccion_predio": 210,
                "saldo": 115,
                "estado_cobranza": 130,
            }
            for col in self.DEBT_COLUMNS:
                self.deudas_tree.heading(col, text=headings[col])
                self.deudas_tree.column(col, width=col_widths.get(col, 120), anchor="center")

            if debts:
                self._all_debts = debts
                for count, debt in enumerate(debts):
                    if count >= 500:
                        break
                    self.deudas_tree.insert("", "end", values=self._debt_row_values(debt))
            else:
                self._all_debts = []
                self.deudas_tree.insert("", "end", values=self._empty_debt_values())
        except Exception as exc:
            self._all_debts = []
            self.deudas_tree.insert("", "end", values=(f"Error: {exc}", "", "", "", "", "", "", "", ""))

    def _selected_debt(self):
        selected = self.deudas_tree.selection()
        if not selected:
            return None
        values = self.deudas_tree.item(selected[0], "values")
        if not values or values[0] in ("Sin datos", "") or str(values[0]).startswith("Error:"):
            return None
        selected_id = str(values[0])
        for debt in self._all_debts:
            if str(getattr(debt, "id_deuda", "")) == selected_id:
                return debt
        return None

    def open_debt_detail(self):
        debt = self._selected_debt()
        if debt is None:
            return

        dialog = tk.Toplevel(self)
        dialog.title(f"Detalle de deuda {getattr(debt, 'id_deuda', '')}")
        dialog.geometry("760x560")
        dialog.transient(self)
        dialog.grab_set()
        dialog.configure(bg=PALETTE["app_bg"])

        shell = tk.Frame(dialog, bg=PALETTE["surface"], highlightbackground=PALETTE["border"], highlightthickness=1)
        shell.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)
        inner = tk.Frame(shell, bg=PALETTE["surface"], padx=18, pady=18)
        inner.pack(fill=tk.BOTH, expand=True)
        inner.columnconfigure(0, weight=1)
        inner.columnconfigure(1, weight=1)

        tk.Label(inner, text="Informacion sincronizada", bg=PALETTE["surface"], fg=PALETTE["text"], font=("Segoe UI Semibold", 16)).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 14))

        fields = [
            ("ID deuda", getattr(debt, "id_deuda", "")),
            ("Estado de cobranza", getattr(debt, "estado_cobranza", "")),
            ("Contribuyente", getattr(debt, "contribuyente", "")),
            ("Documento", getattr(debt, "documento", "")),
            ("Direccion fiscal", getattr(debt, "direccion_fiscal", "")),
            ("Tipo de tributo", getattr(debt, "tipo_tributo", "")),
            ("Anio tributario", getattr(debt, "anio_tributo", "")),
            ("Periodo", getattr(debt, "periodo", "")),
            ("Monto original", self._format_money(getattr(debt, "monto_original", 0))),
            ("Saldo pendiente", self._format_money(getattr(debt, "saldo", 0))),
            ("Fecha vencimiento", getattr(debt, "fecha_vencimiento", "")),
            ("Codigo predio", getattr(debt, "codigo_lote", "")),
            ("Direccion predio", getattr(debt, "direccion_predio", "")),
            ("Sector", getattr(debt, "sector", "")),
            ("Manzana", getattr(debt, "manzana", "")),
            ("Uso predio", getattr(debt, "uso_predio", "")),
            ("Area terreno", getattr(debt, "area_terreno_m2", "")),
            ("Area construida", getattr(debt, "area_construida_m2", "")),
            ("Latitud", getattr(debt, "latitud", "")),
            ("Longitud", getattr(debt, "longitud", "")),
        ]

        for index, (label, value) in enumerate(fields, start=1):
            row = (index + 1) // 2
            col = (index - 1) % 2
            box = tk.Frame(inner, bg=PALETTE["surface_soft"], highlightbackground=PALETTE["border"], highlightthickness=1)
            box.grid(row=row, column=col, sticky="nsew", padx=(0 if col == 0 else 8, 8 if col == 0 else 0), pady=(0, 8))
            tk.Label(box, text=label, bg=PALETTE["surface_soft"], fg=PALETTE["text_muted"], font=("Segoe UI", 8)).pack(anchor="w", padx=10, pady=(8, 2))
            tk.Label(box, text=str(value or "No registrado"), bg=PALETTE["surface_soft"], fg=PALETTE["text"], font=("Segoe UI Semibold", 10), wraplength=310, justify="left").pack(anchor="w", padx=10, pady=(0, 8))

        HoverButton(inner, text="Cerrar", command=dialog.destroy, bg=PALETTE["accent"], hover_bg=PALETTE["accent_hover"], border=PALETTE["accent"], font=("Segoe UI Semibold", 10), padx=14, pady=10).grid(row=12, column=1, sticky="e", pady=(8, 0))

    def sync_queue(self):
        result = self.sync_service.procesar_cola_pendiente()
        messagebox.showinfo("Sincronizacion", result.get("message", "Operacion completada"), parent=self)
        self.refresh()

    def open_map(self):
        import webbrowser
        try:
            webbrowser.open("http://localhost:5173")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el mapa: {e}", parent=self)

    def submit(self):
        try:
            id_deuda = int(self.id_deuda_entry.get().strip())
        except ValueError:
            messagebox.showerror("Validacion", "El ID de deuda debe ser un numero valido.", parent=self)
            return

        direccion = self.direccion_entry.get().strip()
        if not direccion:
            messagebox.showerror("Validacion", "La direccion es obligatoria.", parent=self)
            return

        persona = self.persona_entry.get().strip()
        parentesco = self.parentesco_entry.get().strip()
        id_estado = int(self.estado_cb.get().split(" - ")[0])

        try:
            result = self.controller.registrar_notificacion(id_deuda, direccion, persona, parentesco, id_estado)
            if result.get("success"):
                redis_info = " (Redis: OK)" if result.get("redis_published") else ""
                sync_info = f" [Sincronizacion: {result.get('sync_status', '?')}]"
                estado_texto = self.estado_cb.get().split(" - ")[1] if " - " in self.estado_cb.get() else self.estado_cb.get()
                summary = f"Visita registrada exitosamente.\n\nResumen:\n- Deuda ID: {id_deuda}\n- Persona: {persona} ({parentesco})\n- Resultado: {estado_texto}\n\n{result.get('message', '')}{redis_info}{sync_info}"
                messagebox.showinfo("Visita Registrada", summary, parent=self)
                for entry in [self.id_deuda_entry, self.direccion_entry, self.persona_entry, self.parentesco_entry]:
                    entry.delete(0, tk.END)
            else:
                messagebox.showerror("Error", f"No fue posible registrar la visita.\n\n{result.get('message', 'Error desconocido')}", parent=self)
        except Exception as exc:
            messagebox.showerror("Error", f"No fue posible registrar la visita.\n\nDetalle: {exc}", parent=self)

    def close(self):
        try:
            self.controller.close()
        except Exception:
            pass
