import os
import hashlib
import threading
import shutil
import subprocess
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


class ScannerDuplicadosApp:
    EXTENSOES_PDF = {".pdf"}

    EXTENSOES_WORD = {
        ".doc", ".docx", ".dot", ".dotx", ".rtf"
    }

    EXTENSOES_EXCEL = {
        ".xls", ".xlsx", ".xlsm", ".xlsb", ".csv"
    }

    EXTENSOES_MIDIA = {
        ".mp3", ".mp4", ".wav", ".avi", ".mkv", ".mov",
        ".wmv", ".flv", ".webm", ".m4a", ".aac", ".ogg",
        ".3gp", ".mpeg", ".mpg", ".flac", ".wma"
    }

    EXTENSOES_IMAGEM = {
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp",
        ".tif", ".tiff", ".svg", ".ico", ".heic"
    }

    def __init__(self, root):
        self.root = root
        self.root.title("Scanner e Organizador de Arquivos")
        self.root.geometry("1480x860")
        self.root.minsize(1250, 720)
        self.root.configure(bg="#eef2f7")

        self.pasta_selecionada = tk.StringVar()
        self.status_texto = tk.StringVar(value="Selecione uma pasta para iniciar.")
        self.contador_texto = tk.StringVar(value="Arquivos verificados: 0")
        self.espaco_texto = tk.StringVar(value="Espaço em duplicados: 0 B")
        self.resumo_texto = tk.StringVar(value="Nenhuma análise realizada.")
        self.detalhes_texto = tk.StringVar(value="Selecione um arquivo na tabela para ver os detalhes.")

        self.modo_analise = tk.StringVar(value="duplicados")

        self.filtro_pdf = tk.BooleanVar(value=True)
        self.filtro_word = tk.BooleanVar(value=True)
        self.filtro_excel = tk.BooleanVar(value=True)
        self.filtro_midia = tk.BooleanVar(value=True)
        self.filtro_imagem = tk.BooleanVar(value=True)
        self.filtro_outros = tk.BooleanVar(value=True)

        self.duplicados = {}
        self.arquivos_listados = []
        self.pasta_revisao = ""
        self.cancelar_evento = threading.Event()
        self.total_verificados = 0
        self.total_espaco_duplicado = 0
        self.ultimo_log_progresso = 0

        self.ordem_colunas = {
            "tamanho": False,
            "modificado": False
        }

        self.criar_estilos()
        self.criar_interface()

    def criar_estilos(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")

        self.style.configure(
            "Treeview",
            background="#ffffff",
            fieldbackground="#ffffff",
            foreground="#1f2937",
            rowheight=30,
            borderwidth=0,
            font=("Segoe UI", 10)
        )

        self.style.configure(
            "Treeview.Heading",
            background="#dbe4f0",
            foreground="#111827",
            font=("Segoe UI", 10, "bold"),
            relief="flat"
        )

        self.style.map(
            "Treeview",
            background=[("selected", "#dbeafe")],
            foreground=[("selected", "#111827")]
        )

        self.style.configure(
            "TProgressbar",
            troughcolor="#dfe7f2",
            background="#2563eb",
            borderwidth=0
        )

    def criar_botao(self, parent, texto, comando, bg, state="normal"):
        return tk.Button(
            parent,
            text=texto,
            command=comando,
            bg=bg,
            fg="#ffffff",
            disabledforeground="#d1d5db",
            relief="flat",
            bd=0,
            activebackground=bg,
            activeforeground="#ffffff",
            font=("Segoe UI", 10, "bold"),
            padx=10,
            pady=9,
            state=state,
            cursor="hand2",
            anchor="center"
        )

    def criar_checkbutton(self, parent, texto, variavel):
        return tk.Checkbutton(
            parent,
            text=texto,
            variable=variavel,
            bg="#ffffff",
            fg="#111827",
            activebackground="#ffffff",
            activeforeground="#111827",
            selectcolor="#ffffff",
            font=("Segoe UI", 10),
            cursor="hand2",
            anchor="w"
        )

    def criar_card(self, parent, titulo, variavel):
        frame = tk.Frame(
            parent,
            bg="#ffffff",
            bd=0,
            highlightthickness=1,
            highlightbackground="#d7dee8"
        )
        frame.pack(side="left", fill="both", expand=True, padx=6)

        label_titulo = tk.Label(
            frame,
            text=titulo,
            bg="#ffffff",
            fg="#6b7280",
            font=("Segoe UI", 10, "bold"),
            anchor="w"
        )
        label_titulo.pack(fill="x", padx=14, pady=(12, 4))

        label_valor = tk.Label(
            frame,
            textvariable=variavel,
            bg="#ffffff",
            fg="#111827",
            font=("Segoe UI", 10),
            anchor="w",
            justify="left",
            wraplength=250
        )
        label_valor.pack(fill="x", padx=14, pady=(0, 12))

    def criar_interface(self):
        frame_geral = tk.Frame(self.root, bg="#eef2f7")
        frame_geral.pack(fill="both", expand=True)

        self.sidebar = tk.Frame(
            frame_geral,
            bg="#ffffff",
            width=360,
            bd=0,
            highlightthickness=1,
            highlightbackground="#d7dee8"
        )
        self.sidebar.pack(side="left", fill="y", padx=(16, 8), pady=16)
        self.sidebar.pack_propagate(False)

        self.conteudo = tk.Frame(frame_geral, bg="#eef2f7")
        self.conteudo.pack(side="right", fill="both", expand=True, padx=(8, 16), pady=16)

        self.montar_sidebar()
        self.montar_conteudo()

    def montar_sidebar(self):
        titulo = tk.Label(
            self.sidebar,
            text="Scanner de Arquivos",
            bg="#ffffff",
            fg="#111827",
            font=("Segoe UI", 18, "bold"),
            anchor="w"
        )
        titulo.pack(fill="x", padx=18, pady=(18, 4))

        subtitulo = tk.Label(
            self.sidebar,
            text="Escolha a pasta, defina o modo e execute a análise.",
            bg="#ffffff",
            fg="#4b5563",
            font=("Segoe UI", 10),
            anchor="w",
            justify="left",
            wraplength=290
        )
        subtitulo.pack(fill="x", padx=18, pady=(0, 18))

        label_pasta = tk.Label(
            self.sidebar,
            text="Pasta",
            bg="#ffffff",
            fg="#111827",
            font=("Segoe UI", 10, "bold"),
            anchor="w"
        )
        label_pasta.pack(fill="x", padx=18, pady=(0, 6))

        entrada_container = tk.Frame(
            self.sidebar,
            bg="#f8fafc",
            bd=0,
            highlightthickness=1,
            highlightbackground="#d7dee8"
        )
        entrada_container.pack(fill="x", padx=18, pady=(0, 8))

        self.entrada_pasta = tk.Entry(
            entrada_container,
            textvariable=self.pasta_selecionada,
            font=("Segoe UI", 9),
            relief="flat",
            bd=0,
            bg="#f8fafc",
            fg="#111827"
        )
        self.entrada_pasta.pack(fill="x", padx=10, pady=10)

        self.botao_escolher = self.criar_botao(
            self.sidebar,
            "Escolher pasta",
            self.escolher_pasta,
            "#2563eb"
        )
        self.botao_escolher.pack(fill="x", padx=18, pady=(0, 18))

        separador_1 = tk.Frame(self.sidebar, bg="#e5e7eb", height=1)
        separador_1.pack(fill="x", padx=18, pady=(0, 16))

        label_modo = tk.Label(
            self.sidebar,
            text="Modo de análise",
            bg="#ffffff",
            fg="#111827",
            font=("Segoe UI", 10, "bold"),
            anchor="w"
        )
        label_modo.pack(fill="x", padx=18, pady=(0, 6))

        radio_duplicados = tk.Radiobutton(
            self.sidebar,
            text="Buscar duplicados",
            variable=self.modo_analise,
            value="duplicados",
            bg="#ffffff",
            fg="#111827",
            activebackground="#ffffff",
            selectcolor="#ffffff",
            font=("Segoe UI", 10),
            anchor="w"
        )
        radio_duplicados.pack(fill="x", padx=18)

        radio_listar = tk.Radiobutton(
            self.sidebar,
            text="Listar arquivos por tipo",
            variable=self.modo_analise,
            value="listar",
            bg="#ffffff",
            fg="#111827",
            activebackground="#ffffff",
            selectcolor="#ffffff",
            font=("Segoe UI", 10),
            anchor="w"
        )
        radio_listar.pack(fill="x", padx=18, pady=(0, 16))

        label_filtros = tk.Label(
            self.sidebar,
            text="Tipos de arquivo",
            bg="#ffffff",
            fg="#111827",
            font=("Segoe UI", 10, "bold"),
            anchor="w"
        )
        label_filtros.pack(fill="x", padx=18, pady=(0, 6))

        frame_filtros = tk.Frame(self.sidebar, bg="#ffffff")
        frame_filtros.pack(fill="x", padx=18, pady=(0, 16))

        self.check_pdf = self.criar_checkbutton(frame_filtros, "PDF", self.filtro_pdf)
        self.check_pdf.grid(row=0, column=0, sticky="w", pady=2)

        self.check_word = self.criar_checkbutton(frame_filtros, "Word", self.filtro_word)
        self.check_word.grid(row=0, column=1, sticky="w", pady=2, padx=(18, 0))

        self.check_excel = self.criar_checkbutton(frame_filtros, "Excel", self.filtro_excel)
        self.check_excel.grid(row=1, column=0, sticky="w", pady=2)

        self.check_midia = self.criar_checkbutton(frame_filtros, "Mídia", self.filtro_midia)
        self.check_midia.grid(row=1, column=1, sticky="w", pady=2, padx=(18, 0))

        self.check_imagem = self.criar_checkbutton(frame_filtros, "Imagens", self.filtro_imagem)
        self.check_imagem.grid(row=2, column=0, sticky="w", pady=2)

        self.check_outros = self.criar_checkbutton(frame_filtros, "Outros", self.filtro_outros)
        self.check_outros.grid(row=2, column=1, sticky="w", pady=2, padx=(18, 0))

        frame_filtros.grid_columnconfigure(0, weight=1)
        frame_filtros.grid_columnconfigure(1, weight=1)

        separador_2 = tk.Frame(self.sidebar, bg="#e5e7eb", height=1)
        separador_2.pack(fill="x", padx=18, pady=(0, 16))

        label_acoes = tk.Label(
            self.sidebar,
            text="Ações",
            bg="#ffffff",
            fg="#111827",
            font=("Segoe UI", 10, "bold"),
            anchor="w"
        )
        label_acoes.pack(fill="x", padx=18, pady=(0, 8))

        frame_acoes_topo = tk.Frame(self.sidebar, bg="#ffffff")
        frame_acoes_topo.pack(fill="x", padx=18, pady=(0, 8))

        self.botao_scan = self.criar_botao(
            frame_acoes_topo,
            "Analisar",
            self.iniciar_scanner,
            "#2563eb"
        )
        self.botao_scan.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.botao_atualizar = self.criar_botao(
            frame_acoes_topo,
            "Atualizar",
            self.atualizar_analise,
            "#0f766e"
        )
        self.botao_atualizar.pack(side="left", fill="x", expand=True, padx=(4, 0))

        frame_cancelar = tk.Frame(self.sidebar, bg="#ffffff")
        frame_cancelar.pack(fill="x", padx=18, pady=(0, 8))

        self.botao_cancelar = self.criar_botao(
            frame_cancelar,
            "Cancelar",
            self.cancelar_scanner,
            "#6b7280",
            state="disabled"
        )
        self.botao_cancelar.pack(fill="x", padx=54)

        self.botao_abrir_local = self.criar_botao(
            self.sidebar,
            "Abrir local do arquivo",
            self.abrir_local_arquivo,
            "#4f46e5",
            state="disabled"
        )
        self.botao_abrir_local.pack(fill="x", padx=18, pady=(0, 8))

        self.botao_mover_selecionado = self.criar_botao(
            self.sidebar,
            "Mover selecionado",
            self.mover_selecionado,
            "#b91c1c",
            state="disabled"
        )
        self.botao_mover_selecionado.pack(fill="x", padx=18, pady=(0, 8))

        self.botao_mover_todos = self.criar_botao(
            self.sidebar,
            "Mover todos os duplicados",
            self.mover_todos_duplicados,
            "#92400e",
            state="disabled"
        )
        self.botao_mover_todos.pack(fill="x", padx=18, pady=(0, 8))

        self.botao_revisao = self.criar_botao(
            self.sidebar,
            "Ver revisão",
            self.abrir_pasta_revisao,
            "#1d4ed8",
            state="disabled"
        )
        self.botao_revisao.pack(fill="x", padx=18, pady=(0, 8))

        self.botao_relatorio = self.criar_botao(
            self.sidebar,
            "Salvar relatório",
            self.salvar_relatorio,
            "#374151",
            state="disabled"
        )
        self.botao_relatorio.pack(fill="x", padx=18, pady=(0, 8))

        self.botao_limpar = self.criar_botao(
            self.sidebar,
            "Limpar resultados",
            self.limpar_resultados,
            "#475569"
        )
        self.botao_limpar.pack(fill="x", padx=18, pady=(0, 18))

    def montar_conteudo(self):
        frame_topo = tk.Frame(
            self.conteudo,
            bg="#ffffff",
            bd=0,
            highlightthickness=1,
            highlightbackground="#d7dee8"
        )
        frame_topo.pack(fill="x", pady=(0, 12))

        titulo = tk.Label(
            frame_topo,
            text="Arquivos e resumo da análise",
            bg="#ffffff",
            fg="#111827",
            font=("Segoe UI", 18, "bold"),
            anchor="w"
        )
        titulo.pack(fill="x", padx=18, pady=(14, 4))

        subtitulo = tk.Label(
            frame_topo,
            text="Use a tabela para conferir os arquivos, abrir o local original e mover itens para revisão.",
            bg="#ffffff",
            fg="#4b5563",
            font=("Segoe UI", 10),
            anchor="w"
        )
        subtitulo.pack(fill="x", padx=18, pady=(0, 14))

        self.progress_bar = ttk.Progressbar(self.conteudo, mode="indeterminate")
        self.progress_bar.pack(fill="x", pady=(0, 12))

        frame_cards = tk.Frame(self.conteudo, bg="#eef2f7")
        frame_cards.pack(fill="x", pady=(0, 12))

        self.criar_card(frame_cards, "Status", self.status_texto)
        self.criar_card(frame_cards, "Verificados", self.contador_texto)
        self.criar_card(frame_cards, "Espaço", self.espaco_texto)
        self.criar_card(frame_cards, "Resumo", self.resumo_texto)

        frame_tabela_container = tk.Frame(
            self.conteudo,
            bg="#ffffff",
            bd=0,
            highlightthickness=1,
            highlightbackground="#d7dee8"
        )
        frame_tabela_container.pack(fill="both", expand=True, pady=(0, 12))

        label_tabela = tk.Label(
            frame_tabela_container,
            text="Resultado",
            bg="#ffffff",
            fg="#111827",
            font=("Segoe UI", 12, "bold"),
            anchor="w"
        )
        label_tabela.pack(fill="x", padx=14, pady=(14, 8))

        frame_resultado = tk.Frame(frame_tabela_container, bg="#ffffff")
        frame_resultado.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        colunas = ("grupo", "acao", "tipo", "arquivo", "tamanho", "modificado", "caminho")

        self.tabela = ttk.Treeview(
            frame_resultado,
            columns=colunas,
            show="headings",
            selectmode="browse"
        )

        self.tabela.heading("grupo", text="Grupo")
        self.tabela.heading("acao", text="Ação")
        self.tabela.heading("tipo", text="Tipo")
        self.tabela.heading("arquivo", text="Arquivo")
        self.tabela.heading(
            "tamanho",
            text="Tamanho",
            command=lambda: self.ordenar_tabela("tamanho")
        )
        self.tabela.heading(
            "modificado",
            text="Modificado em",
            command=lambda: self.ordenar_tabela("modificado")
        )
        self.tabela.heading("caminho", text="Caminho")

        self.tabela.column("grupo", width=70, anchor="center")
        self.tabela.column("acao", width=110, anchor="center")
        self.tabela.column("tipo", width=100, anchor="center")
        self.tabela.column("arquivo", width=260)
        self.tabela.column("tamanho", width=120, anchor="center")
        self.tabela.column("modificado", width=160, anchor="center")
        self.tabela.column("caminho", width=760)

        self.tabela.tag_configure("manter", background="#ecfdf5", foreground="#065f46")
        self.tabela.tag_configure("mover", background="#fef2f2", foreground="#991b1b")
        self.tabela.tag_configure("listar", background="#f8fafc", foreground="#1f2937")

        self.tabela.bind("<<TreeviewSelect>>", self.ao_selecionar_item)

        scroll_y = ttk.Scrollbar(frame_resultado, orient="vertical", command=self.tabela.yview)
        scroll_x = ttk.Scrollbar(frame_resultado, orient="horizontal", command=self.tabela.xview)

        self.tabela.configure(
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set
        )

        self.tabela.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")

        frame_resultado.grid_rowconfigure(0, weight=1)
        frame_resultado.grid_columnconfigure(0, weight=1)

        frame_inferior = tk.Frame(self.conteudo, bg="#eef2f7")
        frame_inferior.pack(fill="both")

        frame_detalhes = tk.Frame(
            frame_inferior,
            bg="#ffffff",
            bd=0,
            highlightthickness=1,
            highlightbackground="#d7dee8"
        )
        frame_detalhes.pack(side="left", fill="both", expand=True, padx=(0, 8))

        label_detalhes = tk.Label(
            frame_detalhes,
            text="Arquivo selecionado",
            bg="#ffffff",
            fg="#111827",
            font=("Segoe UI", 12, "bold"),
            anchor="w"
        )
        label_detalhes.pack(fill="x", padx=14, pady=(14, 8))

        detalhes = tk.Label(
            frame_detalhes,
            textvariable=self.detalhes_texto,
            bg="#ffffff",
            fg="#1f2937",
            font=("Segoe UI", 10),
            anchor="nw",
            justify="left",
            wraplength=560
        )
        detalhes.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        frame_visor_container = tk.Frame(
            frame_inferior,
            bg="#ffffff",
            bd=0,
            highlightthickness=1,
            highlightbackground="#d7dee8"
        )
        frame_visor_container.pack(side="right", fill="both", expand=True, padx=(8, 0))

        label_visor = tk.Label(
            frame_visor_container,
            text="Atividade",
            bg="#ffffff",
            fg="#111827",
            font=("Segoe UI", 12, "bold"),
            anchor="w"
        )
        label_visor.pack(fill="x", padx=14, pady=(14, 8))

        frame_visor = tk.Frame(frame_visor_container, bg="#ffffff")
        frame_visor.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        self.visor = tk.Text(
            frame_visor,
            height=8,
            font=("Consolas", 9),
            wrap="none",
            state="disabled",
            relief="flat",
            bd=0,
            bg="#f8fafc",
            fg="#111827",
            insertbackground="#111827"
        )
        self.visor.pack(side="left", fill="both", expand=True)

        scroll_visor = ttk.Scrollbar(frame_visor, orient="vertical", command=self.visor.yview)
        scroll_visor.pack(side="right", fill="y")

        self.visor.configure(yscrollcommand=scroll_visor.set)

    def algum_filtro_marcado(self):
        return (
            self.filtro_pdf.get()
            or self.filtro_word.get()
            or self.filtro_excel.get()
            or self.filtro_midia.get()
            or self.filtro_imagem.get()
            or self.filtro_outros.get()
        )

    def arquivo_permitido(self, caminho):
        extensao = os.path.splitext(caminho)[1].lower()

        if extensao in self.EXTENSOES_PDF:
            return self.filtro_pdf.get()

        if extensao in self.EXTENSOES_WORD:
            return self.filtro_word.get()

        if extensao in self.EXTENSOES_EXCEL:
            return self.filtro_excel.get()

        if extensao in self.EXTENSOES_MIDIA:
            return self.filtro_midia.get()

        if extensao in self.EXTENSOES_IMAGEM:
            return self.filtro_imagem.get()

        return self.filtro_outros.get()

    def obter_tipo_arquivo(self, caminho):
        extensao = os.path.splitext(caminho)[1].lower()

        if extensao in self.EXTENSOES_PDF:
            return "PDF"

        if extensao in self.EXTENSOES_WORD:
            return "Word"

        if extensao in self.EXTENSOES_EXCEL:
            return "Excel"

        if extensao in self.EXTENSOES_MIDIA:
            return "Mídia"

        if extensao in self.EXTENSOES_IMAGEM:
            return "Imagem"

        return "Outros"

    def descrever_filtros(self):
        filtros = []

        if self.filtro_pdf.get():
            filtros.append("PDF")

        if self.filtro_word.get():
            filtros.append("Word")

        if self.filtro_excel.get():
            filtros.append("Excel")

        if self.filtro_midia.get():
            filtros.append("Mídia")

        if self.filtro_imagem.get():
            filtros.append("Imagens")

        if self.filtro_outros.get():
            filtros.append("Outros")

        return ", ".join(filtros)

    def escrever_visor(self, texto):
        self.root.after(0, lambda: self.atualizar_visor(texto))

    def atualizar_visor(self, texto):
        hora = datetime.now().strftime("%H:%M:%S")
        self.visor.config(state="normal")
        self.visor.insert("end", f"[{hora}] {texto}\n")
        self.visor.see("end")
        self.visor.config(state="disabled")

    def limpar_visor(self):
        self.visor.config(state="normal")
        self.visor.delete("1.0", "end")
        self.visor.config(state="disabled")

    def atualizar_contador(self):
        self.root.after(
            0,
            lambda: self.contador_texto.set(f"Arquivos verificados: {self.total_verificados}")
        )

    def atualizar_espaco(self):
        texto = f"Espaço em duplicados: {self.formatar_tamanho(self.total_espaco_duplicado)}"
        self.root.after(0, lambda: self.espaco_texto.set(texto))

    def atualizar_resumo(self):
        if self.modo_analise.get() == "duplicados":
            grupos = len(self.duplicados)
            total_arquivos = sum(len(arquivos) for arquivos in self.duplicados.values())
            texto = f"Grupos duplicados: {grupos} | Arquivos nos grupos: {total_arquivos}"
        else:
            texto = f"Arquivos listados: {len(self.arquivos_listados)}"

        self.root.after(0, lambda: self.resumo_texto.set(texto))

    def escolher_pasta(self):
        pasta = filedialog.askdirectory(title="Selecione a pasta para analisar")

        if not pasta:
            return

        self.pasta_selecionada.set(pasta)
        self.pasta_revisao = os.path.join(pasta, "_arquivos_para_revisar")
        self.status_texto.set("Pasta selecionada. Clique em Analisar.")
        self.detalhes_texto.set("Selecione um arquivo na tabela para ver os detalhes.")
        self.limpar_visor()
        self.escrever_visor(f"Pasta selecionada: {pasta}")
        self.atualizar_botao_revisao()

    def atualizar_botao_revisao(self):
        if self.pasta_revisao and os.path.exists(self.pasta_revisao):
            self.botao_revisao.config(state="normal")
        else:
            self.botao_revisao.config(state="disabled")

    def iniciar_scanner(self):
        pasta = self.pasta_selecionada.get().strip()

        if not pasta:
            messagebox.showwarning("Atenção", "Selecione uma pasta antes de analisar.")
            return

        if not os.path.exists(pasta):
            messagebox.showerror("Erro", "A pasta selecionada não existe.")
            return

        if not self.algum_filtro_marcado():
            messagebox.showwarning("Atenção", "Marque pelo menos um tipo de arquivo para analisar.")
            return

        self.limpar_tabela()
        self.limpar_visor()

        self.duplicados = {}
        self.arquivos_listados = []
        self.total_verificados = 0
        self.total_espaco_duplicado = 0
        self.ultimo_log_progresso = 0
        self.cancelar_evento.clear()
        self.pasta_revisao = os.path.join(pasta, "_arquivos_para_revisar")
        self.detalhes_texto.set("Selecione um arquivo na tabela para ver os detalhes.")

        self.atualizar_contador()
        self.atualizar_espaco()
        self.atualizar_resumo()
        self.resetar_setas_ordenacao()

        self.botao_scan.config(state="disabled")
        self.botao_atualizar.config(state="disabled")
        self.botao_cancelar.config(state="normal")
        self.botao_abrir_local.config(state="disabled")
        self.botao_mover_selecionado.config(state="disabled")
        self.botao_mover_todos.config(state="disabled")
        self.botao_relatorio.config(state="disabled")
        self.atualizar_botao_revisao()

        self.progress_bar.start(10)
        self.status_texto.set("Analisando arquivos...")
        self.escrever_visor("Análise iniciada.")
        self.escrever_visor(f"Pasta em análise: {pasta}")
        self.escrever_visor(f"Modo: {self.obter_nome_modo()}")
        self.escrever_visor(f"Filtros ativos: {self.descrever_filtros()}")

        thread = threading.Thread(
            target=self.executar_scanner,
            args=(pasta,),
            daemon=True
        )
        thread.start()

    def atualizar_analise(self):
        pasta = self.pasta_selecionada.get().strip()

        if not pasta:
            messagebox.showwarning("Atenção", "Selecione uma pasta primeiro.")
            return

        self.iniciar_scanner()

    def cancelar_scanner(self):
        self.cancelar_evento.set()
        self.botao_cancelar.config(state="disabled")
        self.status_texto.set("Cancelando análise...")
        self.escrever_visor("Cancelamento solicitado.")

    def executar_scanner(self, pasta):
        try:
            if self.modo_analise.get() == "duplicados":
                arquivos_por_tamanho = self.agrupar_por_tamanho(pasta)

                if self.cancelar_evento.is_set() or arquivos_por_tamanho is None:
                    self.root.after(0, self.finalizar_cancelamento)
                    return

                duplicados_encontrados = self.encontrar_duplicados(arquivos_por_tamanho)

                if self.cancelar_evento.is_set() or duplicados_encontrados is None:
                    self.root.after(0, self.finalizar_cancelamento)
                    return

                self.duplicados = duplicados_encontrados
                self.total_espaco_duplicado = self.calcular_espaco_duplicado()
            else:
                arquivos = self.listar_arquivos_por_tipo(pasta)

                if self.cancelar_evento.is_set() or arquivos is None:
                    self.root.after(0, self.finalizar_cancelamento)
                    return

                self.arquivos_listados = arquivos
                self.total_espaco_duplicado = 0

            self.root.after(0, self.finalizar_scanner)

        except Exception as erro:
            self.root.after(0, lambda: self.erro_scanner(str(erro)))

    def listar_arquivos_por_tipo(self, pasta):
        arquivos_encontrados = []

        self.escrever_visor("Listando arquivos conforme os filtros selecionados.")

        for raiz, pastas, arquivos in os.walk(pasta):
            if self.cancelar_evento.is_set():
                return None

            pastas[:] = [p for p in pastas if p != "_arquivos_para_revisar"]

            self.escrever_visor(f"Entrando em: {raiz}")

            for nome_arquivo in arquivos:
                if self.cancelar_evento.is_set():
                    return None

                caminho_completo = os.path.join(raiz, nome_arquivo)

                if not self.arquivo_permitido(caminho_completo):
                    continue

                try:
                    if os.path.getsize(caminho_completo) == 0:
                        continue

                    arquivos_encontrados.append(caminho_completo)
                    self.total_verificados += 1
                    self.atualizar_contador()

                    if self.total_verificados - self.ultimo_log_progresso >= 50:
                        self.ultimo_log_progresso = self.total_verificados
                        self.escrever_visor(
                            f"Progresso: {self.total_verificados} arquivos listados."
                        )

                except PermissionError:
                    self.escrever_visor(f"Sem permissão: {caminho_completo}")
                except FileNotFoundError:
                    pass
                except OSError:
                    self.escrever_visor(f"Não foi possível acessar: {caminho_completo}")

        self.escrever_visor(f"Listagem concluída. Total listado: {self.total_verificados}")
        return sorted(arquivos_encontrados)

    def agrupar_por_tamanho(self, pasta):
        arquivos_por_tamanho = {}
        self.escrever_visor("Lendo pastas e organizando arquivos por tamanho.")

        for raiz, pastas, arquivos in os.walk(pasta):
            if self.cancelar_evento.is_set():
                return None

            pastas[:] = [p for p in pastas if p != "_arquivos_para_revisar"]

            self.escrever_visor(f"Entrando em: {raiz}")

            for nome_arquivo in arquivos:
                if self.cancelar_evento.is_set():
                    return None

                caminho_completo = os.path.join(raiz, nome_arquivo)

                if not self.arquivo_permitido(caminho_completo):
                    continue

                try:
                    tamanho = os.path.getsize(caminho_completo)

                    if tamanho == 0:
                        continue

                    if tamanho not in arquivos_por_tamanho:
                        arquivos_por_tamanho[tamanho] = []

                    arquivos_por_tamanho[tamanho].append(caminho_completo)

                    self.total_verificados += 1
                    self.atualizar_contador()

                    if self.total_verificados - self.ultimo_log_progresso >= 50:
                        self.ultimo_log_progresso = self.total_verificados
                        self.escrever_visor(
                            f"Progresso: {self.total_verificados} arquivos verificados."
                        )

                except PermissionError:
                    self.escrever_visor(f"Sem permissão: {caminho_completo}")
                except FileNotFoundError:
                    pass
                except OSError:
                    self.escrever_visor(f"Não foi possível acessar: {caminho_completo}")

        self.escrever_visor(f"Leitura concluída. Total verificado: {self.total_verificados}")
        return arquivos_por_tamanho

    def encontrar_duplicados(self, arquivos_por_tamanho):
        hashes = {}
        self.escrever_visor("Comparando conteúdo dos arquivos com mesmo tamanho.")

        for _, arquivos in arquivos_por_tamanho.items():
            if self.cancelar_evento.is_set():
                return None

            if len(arquivos) < 2:
                continue

            for caminho in arquivos:
                if self.cancelar_evento.is_set():
                    return None

                hash_arquivo = self.calcular_hash(caminho)

                if self.cancelar_evento.is_set():
                    return None

                if not hash_arquivo:
                    continue

                if hash_arquivo not in hashes:
                    hashes[hash_arquivo] = []

                hashes[hash_arquivo].append(caminho)

        duplicados = {}

        for hash_arquivo, arquivos in hashes.items():
            if self.cancelar_evento.is_set():
                return None

            if len(arquivos) > 1:
                arquivos_ordenados = sorted(arquivos)
                duplicados[hash_arquivo] = arquivos_ordenados
                self.escrever_visor(
                    f"Grupo duplicado encontrado com {len(arquivos_ordenados)} arquivos."
                )

        return duplicados

    def calcular_hash(self, caminho):
        sha256 = hashlib.sha256()

        try:
            with open(caminho, "rb") as arquivo:
                while True:
                    if self.cancelar_evento.is_set():
                        return None

                    bloco = arquivo.read(1024 * 1024)

                    if not bloco:
                        break

                    sha256.update(bloco)

            return sha256.hexdigest()

        except PermissionError:
            return None
        except FileNotFoundError:
            return None
        except OSError:
            return None

    def calcular_espaco_duplicado(self):
        total = 0

        for arquivos in self.duplicados.values():
            for caminho in arquivos[1:]:
                try:
                    if os.path.exists(caminho):
                        total += os.path.getsize(caminho)
                except OSError:
                    pass

        return total

    def finalizar_cancelamento(self):
        self.progress_bar.stop()
        self.botao_scan.config(state="normal")
        self.botao_atualizar.config(state="normal")
        self.botao_cancelar.config(state="disabled")
        self.botao_abrir_local.config(state="disabled")
        self.botao_mover_selecionado.config(state="disabled")
        self.botao_mover_todos.config(state="disabled")
        self.botao_relatorio.config(state="disabled")

        self.duplicados = {}
        self.arquivos_listados = []
        self.total_espaco_duplicado = 0

        self.atualizar_espaco()
        self.atualizar_resumo()
        self.atualizar_botao_revisao()

        self.status_texto.set("Análise cancelada.")
        self.escrever_visor("Análise cancelada pelo usuário.")

    def finalizar_scanner(self):
        self.progress_bar.stop()
        self.botao_scan.config(state="normal")
        self.botao_atualizar.config(state="normal")
        self.botao_cancelar.config(state="disabled")

        self.preencher_tabela()
        self.atualizar_espaco()
        self.atualizar_resumo()
        self.atualizar_painel_resultado()
        self.atualizar_botao_revisao()

        self.escrever_visor("Análise concluída.")

    def erro_scanner(self, mensagem):
        self.progress_bar.stop()
        self.botao_scan.config(state="normal")
        self.botao_atualizar.config(state="normal")
        self.botao_cancelar.config(state="disabled")
        self.botao_abrir_local.config(state="disabled")
        self.botao_mover_selecionado.config(state="disabled")
        self.botao_mover_todos.config(state="disabled")
        self.botao_relatorio.config(state="disabled")

        self.status_texto.set("Erro ao executar a análise.")
        self.escrever_visor(f"Erro: {mensagem}")
        messagebox.showerror("Erro", mensagem)
        self.atualizar_botao_revisao()

    def atualizar_painel_resultado(self, mensagem=None):
        if self.modo_analise.get() == "duplicados":
            grupos = len(self.duplicados)
            total_arquivos = sum(len(arquivos) for arquivos in self.duplicados.values())
            total_para_mover = max(0, total_arquivos - grupos)

            if grupos == 0:
                self.status_texto.set("Nenhum arquivo duplicado encontrado.")
                self.botao_mover_selecionado.config(state="disabled")
                self.botao_mover_todos.config(state="disabled")
                self.botao_relatorio.config(state="disabled")
                self.botao_abrir_local.config(state="disabled")
                return

            self.status_texto.set(
                mensagem or f"{grupos} grupos duplicados encontrados. {total_para_mover} arquivos podem ser movidos."
            )

            self.botao_mover_selecionado.config(state="normal")
            self.botao_mover_todos.config(state="normal")
            self.botao_relatorio.config(state="normal")
        else:
            total = len(self.arquivos_listados)

            if total == 0:
                self.status_texto.set("Nenhum arquivo encontrado com os filtros selecionados.")
                self.botao_mover_selecionado.config(state="disabled")
                self.botao_mover_todos.config(state="disabled")
                self.botao_relatorio.config(state="disabled")
                self.botao_abrir_local.config(state="disabled")
                return

            self.status_texto.set(mensagem or f"{total} arquivos encontrados conforme os filtros.")
            self.botao_mover_selecionado.config(state="normal")
            self.botao_mover_todos.config(state="disabled")
            self.botao_relatorio.config(state="normal")

        if not self.tabela.selection():
            self.botao_abrir_local.config(state="disabled")

    def preencher_tabela(self):
        self.limpar_tabela()

        if self.modo_analise.get() == "duplicados":
            grupo = 1

            for arquivos in self.duplicados.values():
                for indice, caminho in enumerate(arquivos):
                    self.inserir_linha_tabela(
                        grupo=grupo,
                        acao="Manter" if indice == 0 else "Mover",
                        caminho=caminho,
                        tag="manter" if indice == 0 else "mover"
                    )

                grupo += 1
        else:
            for caminho in self.arquivos_listados:
                self.inserir_linha_tabela(
                    grupo="-",
                    acao="Arquivo",
                    caminho=caminho,
                    tag="listar"
                )

    def inserir_linha_tabela(self, grupo, acao, caminho, tag):
        try:
            tamanho = self.formatar_tamanho(os.path.getsize(caminho))
        except OSError:
            tamanho = "Indisponível"

        nome = os.path.basename(caminho)
        tipo = self.obter_tipo_arquivo(caminho)
        modificado = self.obter_data_modificacao(caminho)

        self.tabela.insert(
            "",
            "end",
            values=(grupo, acao, tipo, nome, tamanho, modificado, caminho),
            tags=(tag,)
        )

    def obter_data_modificacao(self, caminho):
        try:
            timestamp = os.path.getmtime(caminho)
            return datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y %H:%M")
        except OSError:
            return "Indisponível"

    def obter_nome_modo(self):
        if self.modo_analise.get() == "duplicados":
            return "Buscar duplicados"

        return "Listar arquivos por tipo"

    def obter_item_selecionado(self):
        item_selecionado = self.tabela.selection()

        if not item_selecionado:
            return None

        return item_selecionado[0]

    def obter_valores_selecionados(self):
        item = self.obter_item_selecionado()

        if not item:
            return None

        valores = self.tabela.item(item, "values")

        if not valores or len(valores) < 7:
            return None

        return valores

    def obter_caminho_selecionado(self):
        valores = self.obter_valores_selecionados()

        if not valores:
            return None

        return valores[6]

    def ao_selecionar_item(self, event=None):
        valores = self.obter_valores_selecionados()

        if not valores:
            self.botao_abrir_local.config(state="disabled")
            self.detalhes_texto.set("Selecione um arquivo na tabela para ver os detalhes.")
            return

        grupo, acao, tipo, arquivo, tamanho, modificado, caminho = valores

        self.botao_abrir_local.config(state="normal")

        self.detalhes_texto.set(
            f"Arquivo: {arquivo}\n"
            f"Tipo: {tipo}\n"
            f"Ação: {acao}\n"
            f"Grupo: {grupo}\n"
            f"Tamanho: {tamanho}\n"
            f"Modificado em: {modificado}\n"
            f"Caminho: {caminho}"
        )

    def abrir_local_arquivo(self):
        caminho = self.obter_caminho_selecionado()

        if not caminho:
            messagebox.showwarning("Atenção", "Selecione um arquivo na tabela.")
            return

        caminho = os.path.normpath(caminho)

        if not os.path.exists(caminho):
            pasta = os.path.dirname(caminho)

            if os.path.exists(pasta):
                try:
                    os.startfile(pasta)
                    self.escrever_visor(f"Pasta aberta: {pasta}")
                    return
                except Exception as erro:
                    messagebox.showerror(
                        "Erro",
                        f"Não foi possível abrir a pasta.\n\n{erro}"
                    )
                    return

            messagebox.showwarning(
                "Atenção",
                "O arquivo selecionado não existe mais no local original."
            )
            return

        try:
            comando = f'explorer /select,"{caminho}"'
            subprocess.Popen(comando, shell=True)
            self.escrever_visor(f"Local aberto: {caminho}")
        except Exception:
            try:
                os.startfile(os.path.dirname(caminho))
                self.escrever_visor(f"Pasta aberta: {os.path.dirname(caminho)}")
            except Exception as erro:
                messagebox.showerror(
                    "Erro",
                    f"Não foi possível abrir o local do arquivo.\n\n{erro}"
                )

    def mover_selecionado(self):
        valores = self.obter_valores_selecionados()

        if not valores:
            messagebox.showwarning("Atenção", "Selecione um arquivo na tabela.")
            return

        grupo, acao, tipo, arquivo, tamanho, modificado, caminho = valores

        if self.modo_analise.get() == "duplicados" and acao == "Manter":
            confirmar_manter = messagebox.askyesno(
                "Arquivo marcado para manter",
                "Esse arquivo está marcado como Manter.\n\nDeseja mover mesmo assim?"
            )

            if not confirmar_manter:
                return

        if self.modo_analise.get() == "listar":
            confirmar = messagebox.askyesno(
                "Confirmar movimentação",
                f"Este arquivo não foi identificado como duplicado.\n\n"
                f"Ele será movido para a pasta de revisão.\n\n"
                f"Arquivo: {arquivo}\n"
                f"Caminho: {caminho}\n\n"
                f"Deseja continuar?"
            )
        else:
            confirmar = messagebox.askyesno(
                "Confirmar movimentação",
                f"Deseja mover este arquivo para a pasta de revisão?\n\n{caminho}"
            )

        if not confirmar:
            return

        try:
            destino = self.criar_destino_seguro(caminho)
            shutil.move(caminho, destino)

            if self.modo_analise.get() == "duplicados":
                self.remover_caminho_dos_duplicados(caminho)
                self.total_espaco_duplicado = self.calcular_espaco_duplicado()
            else:
                self.remover_caminho_da_listagem(caminho)

            self.preencher_tabela()
            self.atualizar_espaco()
            self.atualizar_resumo()
            self.atualizar_botao_revisao()
            self.atualizar_painel_resultado("Arquivo movido para revisão.")

            self.botao_abrir_local.config(state="disabled")
            self.detalhes_texto.set("Arquivo movido para revisão.")
            self.escrever_visor(f"Arquivo movido: {caminho}")
            self.escrever_visor(f"Destino: {destino}")

            messagebox.showinfo("Sucesso", "Arquivo movido para a pasta de revisão.")

        except Exception as erro:
            self.escrever_visor(f"Erro ao mover: {caminho}")
            self.escrever_visor(str(erro))
            messagebox.showerror(
                "Erro",
                f"Não foi possível mover o arquivo.\n\n{erro}"
            )

    def mover_todos_duplicados(self):
        if not self.duplicados:
            messagebox.showwarning("Atenção", "Não há duplicados para mover.")
            return

        grupos = len(self.duplicados)
        total_arquivos = sum(len(arquivos) for arquivos in self.duplicados.values())
        total_para_mover = total_arquivos - grupos
        espaco = self.formatar_tamanho(self.total_espaco_duplicado)

        confirmar = messagebox.askyesno(
            "Confirmar movimentação",
            f"O sistema vai manter o primeiro arquivo de cada grupo e mover os demais para revisão.\n\n"
            f"Grupos: {grupos}\n"
            f"Arquivos que serão movidos: {total_para_mover}\n"
            f"Espaço em duplicados: {espaco}\n\n"
            f"Deseja continuar?"
        )

        if not confirmar:
            return

        movidos = 0
        erros = []

        self.escrever_visor("Movimentação dos duplicados iniciada.")

        for arquivos in list(self.duplicados.values()):
            for caminho in arquivos[1:]:
                try:
                    if os.path.exists(caminho):
                        destino = self.criar_destino_seguro(caminho)
                        shutil.move(caminho, destino)
                        movidos += 1
                        self.escrever_visor(f"Movido: {caminho}")
                        self.escrever_visor(f"Destino: {destino}")
                except Exception as erro:
                    erros.append(f"{caminho} | {erro}")
                    self.escrever_visor(f"Erro ao mover: {caminho}")
                    self.escrever_visor(str(erro))

        self.duplicados = {}
        self.total_espaco_duplicado = 0

        self.limpar_tabela()
        self.atualizar_espaco()
        self.atualizar_resumo()
        self.atualizar_botao_revisao()

        self.botao_abrir_local.config(state="disabled")
        self.botao_mover_selecionado.config(state="disabled")
        self.botao_mover_todos.config(state="disabled")
        self.botao_relatorio.config(state="disabled")
        self.detalhes_texto.set("Arquivos movidos para revisão.")

        if erros:
            self.status_texto.set(f"{movidos} arquivos foram movidos. Alguns não puderam ser movidos.")
            messagebox.showwarning(
                "Concluído com avisos",
                f"{movidos} arquivos foram movidos para revisão.\n\nAlguns arquivos não puderam ser movidos."
            )
            return

        self.status_texto.set(f"{movidos} arquivos foram movidos para revisão.")
        messagebox.showinfo(
            "Concluído",
            f"{movidos} arquivos foram movidos para a pasta de revisão."
        )

    def abrir_pasta_revisao(self):
        if not self.pasta_revisao:
            pasta = self.pasta_selecionada.get().strip()

            if not pasta:
                messagebox.showwarning("Atenção", "Selecione uma pasta primeiro.")
                return

            self.pasta_revisao = os.path.join(pasta, "_arquivos_para_revisar")

        if not os.path.exists(self.pasta_revisao):
            messagebox.showwarning("Atenção", "A pasta de revisão ainda não existe.")
            return

        try:
            os.startfile(self.pasta_revisao)
            self.escrever_visor(f"Pasta de revisão aberta: {self.pasta_revisao}")
        except Exception as erro:
            messagebox.showerror(
                "Erro",
                f"Não foi possível abrir a pasta de revisão.\n\n{erro}"
            )

    def criar_destino_seguro(self, caminho_origem):
        os.makedirs(self.pasta_revisao, exist_ok=True)

        nome_arquivo = os.path.basename(caminho_origem)
        destino = os.path.join(self.pasta_revisao, nome_arquivo)

        if not os.path.exists(destino):
            return destino

        nome, extensao = os.path.splitext(nome_arquivo)
        contador = 1

        while True:
            novo_nome = f"{nome}_revisao_{contador}{extensao}"
            novo_destino = os.path.join(self.pasta_revisao, novo_nome)

            if not os.path.exists(novo_destino):
                return novo_destino

            contador += 1

    def remover_caminho_dos_duplicados(self, caminho):
        chaves_para_remover = []

        for chave, arquivos in self.duplicados.items():
            if caminho in arquivos:
                arquivos.remove(caminho)

            if len(arquivos) < 2:
                chaves_para_remover.append(chave)

        for chave in chaves_para_remover:
            del self.duplicados[chave]

    def remover_caminho_da_listagem(self, caminho):
        self.arquivos_listados = [
            arquivo for arquivo in self.arquivos_listados if arquivo != caminho
        ]

    def limpar_tabela(self):
        for item in self.tabela.get_children():
            self.tabela.delete(item)

    def limpar_resultados(self):
        self.limpar_tabela()
        self.limpar_visor()

        self.duplicados = {}
        self.arquivos_listados = []
        self.total_verificados = 0
        self.total_espaco_duplicado = 0
        self.ultimo_log_progresso = 0
        self.cancelar_evento.clear()

        self.atualizar_contador()
        self.atualizar_espaco()
        self.atualizar_resumo()
        self.atualizar_botao_revisao()
        self.resetar_setas_ordenacao()

        self.botao_cancelar.config(state="disabled")
        self.botao_abrir_local.config(state="disabled")
        self.botao_mover_selecionado.config(state="disabled")
        self.botao_mover_todos.config(state="disabled")
        self.botao_relatorio.config(state="disabled")
        self.botao_scan.config(state="normal")
        self.botao_atualizar.config(state="normal")

        self.status_texto.set("Resultados limpos.")
        self.detalhes_texto.set("Selecione um arquivo na tabela para ver os detalhes.")
        self.escrever_visor("Resultados limpos.")

    def salvar_relatorio(self):
        tem_dados = bool(self.duplicados) or bool(self.arquivos_listados)

        if not tem_dados:
            messagebox.showwarning("Atenção", "Não há dados para salvar.")
            return

        caminho_relatorio = filedialog.asksaveasfilename(
            title="Salvar relatório",
            defaultextension=".txt",
            filetypes=[("Arquivo de texto", "*.txt")]
        )

        if not caminho_relatorio:
            return

        try:
            with open(caminho_relatorio, "w", encoding="utf-8") as relatorio:
                relatorio.write("Relatório de Arquivos\n")
                relatorio.write("=" * 50 + "\n\n")
                relatorio.write(f"Data do relatório: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
                relatorio.write(f"Pasta analisada: {self.pasta_selecionada.get()}\n")
                relatorio.write(f"Modo: {self.obter_nome_modo()}\n")
                relatorio.write(f"Filtros usados: {self.descrever_filtros()}\n")
                relatorio.write(f"Arquivos verificados: {self.total_verificados}\n")

                if self.modo_analise.get() == "duplicados":
                    grupos = len(self.duplicados)
                    total_arquivos = sum(len(arquivos) for arquivos in self.duplicados.values())
                    total_para_mover = total_arquivos - grupos

                    relatorio.write(f"Grupos duplicados: {grupos}\n")
                    relatorio.write(f"Arquivos nos grupos: {total_arquivos}\n")
                    relatorio.write(f"Arquivos que podem ser movidos: {total_para_mover}\n")
                    relatorio.write(f"Espaço em duplicados: {self.formatar_tamanho(self.total_espaco_duplicado)}\n\n")

                    grupo = 1

                    for arquivos in self.duplicados.values():
                        relatorio.write(f"Grupo {grupo}\n")
                        relatorio.write("-" * 30 + "\n")

                        for indice, caminho in enumerate(arquivos):
                            acao = "Manter" if indice == 0 else "Mover"
                            self.escrever_linha_relatorio(relatorio, acao, caminho)

                        relatorio.write("\n")
                        grupo += 1
                else:
                    relatorio.write(f"Arquivos listados: {len(self.arquivos_listados)}\n\n")

                    for caminho in self.arquivos_listados:
                        self.escrever_linha_relatorio(relatorio, "Arquivo", caminho)

            self.escrever_visor(f"Relatório salvo: {caminho_relatorio}")
            messagebox.showinfo("Sucesso", "Relatório salvo com sucesso.")

        except Exception as erro:
            self.escrever_visor(f"Erro ao salvar relatório: {erro}")
            messagebox.showerror(
                "Erro",
                f"Não foi possível salvar o relatório.\n\n{erro}"
            )

    def escrever_linha_relatorio(self, relatorio, acao, caminho):
        try:
            tamanho = self.formatar_tamanho(os.path.getsize(caminho))
        except OSError:
            tamanho = "Indisponível"

        relatorio.write(f"Ação: {acao}\n")
        relatorio.write(f"Tipo: {self.obter_tipo_arquivo(caminho)}\n")
        relatorio.write(f"Arquivo: {os.path.basename(caminho)}\n")
        relatorio.write(f"Tamanho: {tamanho}\n")
        relatorio.write(f"Modificado em: {self.obter_data_modificacao(caminho)}\n")
        relatorio.write(f"Caminho: {caminho}\n\n")

    def ordenar_tabela(self, coluna):
        crescente = not self.ordem_colunas.get(coluna, False)
        self.ordem_colunas[coluna] = crescente

        itens = list(self.tabela.get_children())

        if coluna == "tamanho":
            indice = 4
            chave = lambda item: self.converter_tamanho_para_bytes(
                self.tabela.item(item, "values")[indice]
            )
        elif coluna == "modificado":
            indice = 5
            chave = lambda item: self.converter_data_para_ordenacao(
                self.tabela.item(item, "values")[indice]
            )
        else:
            return

        itens_ordenados = sorted(
            itens,
            key=chave,
            reverse=not crescente
        )

        for posicao, item in enumerate(itens_ordenados):
            self.tabela.move(item, "", posicao)

        self.atualizar_setas_ordenacao(coluna, crescente)

    def atualizar_setas_ordenacao(self, coluna, crescente):
        self.tabela.heading(
            "tamanho",
            text="Tamanho",
            command=lambda: self.ordenar_tabela("tamanho")
        )

        self.tabela.heading(
            "modificado",
            text="Modificado em",
            command=lambda: self.ordenar_tabela("modificado")
        )

        seta = "▲" if crescente else "▼"

        if coluna == "tamanho":
            self.tabela.heading(
                "tamanho",
                text=f"Tamanho {seta}",
                command=lambda: self.ordenar_tabela("tamanho")
            )

        if coluna == "modificado":
            self.tabela.heading(
                "modificado",
                text=f"Modificado em {seta}",
                command=lambda: self.ordenar_tabela("modificado")
            )

    def resetar_setas_ordenacao(self):
        self.ordem_colunas = {
            "tamanho": False,
            "modificado": False
        }

        if hasattr(self, "tabela"):
            self.tabela.heading(
                "tamanho",
                text="Tamanho",
                command=lambda: self.ordenar_tabela("tamanho")
            )

            self.tabela.heading(
                "modificado",
                text="Modificado em",
                command=lambda: self.ordenar_tabela("modificado")
            )

    def converter_tamanho_para_bytes(self, valor):
        if not valor or valor == "Indisponível":
            return 0

        partes = valor.split()

        if len(partes) != 2:
            return 0

        try:
            numero = float(partes[0].replace(",", "."))
        except ValueError:
            return 0

        unidade = partes[1].upper()

        multiplicadores = {
            "B": 1,
            "KB": 1024,
            "MB": 1024 ** 2,
            "GB": 1024 ** 3,
            "TB": 1024 ** 4,
            "PB": 1024 ** 5
        }

        return numero * multiplicadores.get(unidade, 1)

    def converter_data_para_ordenacao(self, valor):
        if not valor or valor == "Indisponível":
            return datetime.min

        try:
            return datetime.strptime(valor, "%d/%m/%Y %H:%M")
        except ValueError:
            return datetime.min

    def formatar_tamanho(self, tamanho_bytes):
        for unidade in ["B", "KB", "MB", "GB", "TB"]:
            if tamanho_bytes < 1024:
                return f"{tamanho_bytes:.2f} {unidade}"

            tamanho_bytes /= 1024

        return f"{tamanho_bytes:.2f} PB"


if __name__ == "__main__":
    root = tk.Tk()
    app = ScannerDuplicadosApp(root)
    root.mainloop()