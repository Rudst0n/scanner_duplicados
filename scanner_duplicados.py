import os
import hashlib
import threading
import shutil
import subprocess
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


class ScannerDuplicadosApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Scanner de Arquivos Duplicados")
        self.root.geometry("1450x850")
        self.root.minsize(1250, 720)
        self.root.configure(bg="#eef2f7")

        self.pasta_selecionada = tk.StringVar()
        self.status_texto = tk.StringVar(value="Selecione uma pasta para iniciar.")
        self.contador_texto = tk.StringVar(value="Arquivos verificados: 0")
        self.espaco_texto = tk.StringVar(value="Espaço em duplicados: 0 B")
        self.resumo_texto = tk.StringVar(value="Grupos duplicados: 0 | Arquivos nos grupos: 0")

        self.duplicados = {}
        self.pasta_revisao = ""
        self.cancelar_evento = threading.Event()
        self.total_verificados = 0
        self.total_espaco_duplicado = 0
        self.ultimo_log_progresso = 0

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

    def criar_botao(self, parent, texto, comando, largura, bg, fg="#ffffff", state="normal"):
        return tk.Button(
            parent,
            text=texto,
            command=comando,
            width=largura,
            bg=bg,
            fg=fg,
            relief="flat",
            bd=0,
            activebackground=bg,
            activeforeground=fg,
            font=("Segoe UI", 10, "bold"),
            padx=10,
            pady=8,
            state=state,
            cursor="hand2"
        )

    def criar_card(self, parent, titulo, variavel):
        frame = tk.Frame(
            parent,
            bg="#ffffff",
            bd=0,
            highlightthickness=1,
            highlightbackground="#d7dee8"
        )
        frame.pack(side="left", fill="x", expand=True, padx=6)

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
            font=("Segoe UI", 11),
            anchor="w"
        )
        label_valor.pack(fill="x", padx=14, pady=(0, 12))

    def criar_interface(self):
        frame_principal = tk.Frame(self.root, bg="#eef2f7", padx=16, pady=16)
        frame_principal.pack(fill="both", expand=True)

        frame_topo = tk.Frame(
            frame_principal,
            bg="#ffffff",
            bd=0,
            highlightthickness=1,
            highlightbackground="#d7dee8"
        )
        frame_topo.pack(fill="x", pady=(0, 12))

        titulo = tk.Label(
            frame_topo,
            text="Scanner de Arquivos Duplicados",
            bg="#ffffff",
            fg="#111827",
            font=("Segoe UI", 20, "bold")
        )
        titulo.pack(anchor="w", padx=18, pady=(16, 4))

        subtitulo = tk.Label(
            frame_topo,
            text="Analise uma pasta, encontre arquivos duplicados pelo conteúdo e mova os repetidos para revisão.",
            bg="#ffffff",
            fg="#4b5563",
            font=("Segoe UI", 10)
        )
        subtitulo.pack(anchor="w", padx=18, pady=(0, 16))

        frame_pasta = tk.Frame(frame_principal, bg="#eef2f7")
        frame_pasta.pack(fill="x", pady=(0, 12))

        entrada_container = tk.Frame(
            frame_pasta,
            bg="#ffffff",
            bd=0,
            highlightthickness=1,
            highlightbackground="#d7dee8"
        )
        entrada_container.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.entrada_pasta = tk.Entry(
            entrada_container,
            textvariable=self.pasta_selecionada,
            font=("Segoe UI", 10),
            relief="flat",
            bd=0,
            bg="#ffffff",
            fg="#111827"
        )
        self.entrada_pasta.pack(fill="x", padx=12, pady=12)

        self.botao_escolher = self.criar_botao(
            frame_pasta,
            "Escolher pasta",
            self.escolher_pasta,
            16,
            "#2563eb"
        )
        self.botao_escolher.pack(side="left")

        frame_botoes = tk.Frame(frame_principal, bg="#eef2f7")
        frame_botoes.pack(fill="x", pady=(0, 12))

        self.botao_scan = self.criar_botao(
            frame_botoes,
            "Analisar",
            self.iniciar_scanner,
            12,
            "#2563eb"
        )
        self.botao_scan.pack(side="left", padx=(0, 8))

        self.botao_atualizar = self.criar_botao(
            frame_botoes,
            "Atualizar análise",
            self.atualizar_analise,
            16,
            "#0f766e"
        )
        self.botao_atualizar.pack(side="left", padx=(0, 8))

        self.botao_cancelar = self.criar_botao(
            frame_botoes,
            "Cancelar",
            self.cancelar_scanner,
            12,
            "#6b7280",
            state="disabled"
        )
        self.botao_cancelar.pack(side="left", padx=(0, 8))

        self.botao_abrir_local = self.criar_botao(
            frame_botoes,
            "Abrir local",
            self.abrir_local_arquivo,
            12,
            "#4f46e5",
            state="disabled"
        )
        self.botao_abrir_local.pack(side="left", padx=(0, 8))

        self.botao_mover_selecionado = self.criar_botao(
            frame_botoes,
            "Mover selecionado",
            self.mover_selecionado,
            18,
            "#b91c1c",
            state="disabled"
        )
        self.botao_mover_selecionado.pack(side="left", padx=(0, 8))

        self.botao_mover_todos = self.criar_botao(
            frame_botoes,
            "Mover todos",
            self.mover_todos_duplicados,
            14,
            "#92400e",
            state="disabled"
        )
        self.botao_mover_todos.pack(side="left", padx=(0, 8))

        self.botao_revisao = self.criar_botao(
            frame_botoes,
            "Ver revisão",
            self.abrir_pasta_revisao,
            12,
            "#1d4ed8",
            state="disabled"
        )
        self.botao_revisao.pack(side="left", padx=(0, 8))

        self.botao_relatorio = self.criar_botao(
            frame_botoes,
            "Relatório",
            self.salvar_relatorio,
            12,
            "#374151",
            state="disabled"
        )
        self.botao_relatorio.pack(side="left", padx=(0, 8))

        self.botao_limpar = self.criar_botao(
            frame_botoes,
            "Limpar",
            self.limpar_resultados,
            10,
            "#475569"
        )
        self.botao_limpar.pack(side="left")

        self.progress_bar = ttk.Progressbar(frame_principal, mode="indeterminate")
        self.progress_bar.pack(fill="x", pady=(0, 12))

        frame_cards = tk.Frame(frame_principal, bg="#eef2f7")
        frame_cards.pack(fill="x", pady=(0, 12))

        self.criar_card(frame_cards, "Status", self.status_texto)
        self.criar_card(frame_cards, "Verificados", self.contador_texto)
        self.criar_card(frame_cards, "Espaço", self.espaco_texto)
        self.criar_card(frame_cards, "Resumo", self.resumo_texto)

        frame_tabela_container = tk.Frame(
            frame_principal,
            bg="#ffffff",
            bd=0,
            highlightthickness=1,
            highlightbackground="#d7dee8"
        )
        frame_tabela_container.pack(fill="both", expand=True, pady=(0, 12))

        label_tabela = tk.Label(
            frame_tabela_container,
            text="Arquivos encontrados",
            bg="#ffffff",
            fg="#111827",
            font=("Segoe UI", 12, "bold")
        )
        label_tabela.pack(anchor="w", padx=14, pady=(14, 8))

        frame_resultado = tk.Frame(frame_tabela_container, bg="#ffffff")
        frame_resultado.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        colunas = ("grupo", "acao", "arquivo", "tamanho", "modificado", "caminho")

        self.tabela = ttk.Treeview(
            frame_resultado,
            columns=colunas,
            show="headings",
            selectmode="browse"
        )

        self.tabela.heading("grupo", text="Grupo")
        self.tabela.heading("acao", text="Ação")
        self.tabela.heading("arquivo", text="Arquivo")
        self.tabela.heading("tamanho", text="Tamanho")
        self.tabela.heading("modificado", text="Modificado em")
        self.tabela.heading("caminho", text="Caminho")

        self.tabela.column("grupo", width=70, anchor="center")
        self.tabela.column("acao", width=100, anchor="center")
        self.tabela.column("arquivo", width=260)
        self.tabela.column("tamanho", width=110, anchor="center")
        self.tabela.column("modificado", width=150, anchor="center")
        self.tabela.column("caminho", width=760)

        self.tabela.tag_configure("manter", background="#ecfdf5", foreground="#065f46")
        self.tabela.tag_configure("mover", background="#fef2f2", foreground="#991b1b")

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

        frame_visor_container = tk.Frame(
            frame_principal,
            bg="#ffffff",
            bd=0,
            highlightthickness=1,
            highlightbackground="#d7dee8"
        )
        frame_visor_container.pack(fill="both")

        label_visor = tk.Label(
            frame_visor_container,
            text="Atividade",
            bg="#ffffff",
            fg="#111827",
            font=("Segoe UI", 12, "bold")
        )
        label_visor.pack(anchor="w", padx=14, pady=(14, 8))

        frame_visor = tk.Frame(frame_visor_container, bg="#ffffff")
        frame_visor.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        self.visor = tk.Text(
            frame_visor,
            height=7,
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
        grupos = len(self.duplicados)
        total_arquivos = sum(len(arquivos) for arquivos in self.duplicados.values())
        texto = f"Grupos duplicados: {grupos} | Arquivos nos grupos: {total_arquivos}"
        self.root.after(0, lambda: self.resumo_texto.set(texto))

    def ao_selecionar_item(self, event=None):
        if self.tabela.selection():
            self.botao_abrir_local.config(state="normal")
        else:
            self.botao_abrir_local.config(state="disabled")

    def escolher_pasta(self):
        pasta = filedialog.askdirectory(title="Selecione a pasta para analisar")

        if not pasta:
            return

        self.pasta_selecionada.set(pasta)
        self.pasta_revisao = os.path.join(pasta, "_duplicados_para_revisar")
        self.status_texto.set("Pasta selecionada. Clique em Analisar.")
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

        self.limpar_tabela()
        self.limpar_visor()

        self.duplicados = {}
        self.total_verificados = 0
        self.total_espaco_duplicado = 0
        self.ultimo_log_progresso = 0
        self.cancelar_evento.clear()
        self.pasta_revisao = os.path.join(pasta, "_duplicados_para_revisar")

        self.atualizar_contador()
        self.atualizar_espaco()
        self.atualizar_resumo()

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

        thread = threading.Thread(target=self.executar_scanner, args=(pasta,), daemon=True)
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

            self.root.after(0, self.finalizar_scanner)

        except Exception as erro:
            self.root.after(0, lambda: self.erro_scanner(str(erro)))

    def agrupar_por_tamanho(self, pasta):
        arquivos_por_tamanho = {}
        self.escrever_visor("Lendo pastas e organizando arquivos por tamanho.")

        for raiz, pastas, arquivos in os.walk(pasta):
            if self.cancelar_evento.is_set():
                return None

            pastas[:] = [p for p in pastas if p != "_duplicados_para_revisar"]

            self.escrever_visor(f"Entrando em: {raiz}")

            for nome_arquivo in arquivos:
                if self.cancelar_evento.is_set():
                    return None

                caminho_completo = os.path.join(raiz, nome_arquivo)

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
                        self.escrever_visor(f"Progresso: {self.total_verificados} arquivos verificados.")

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
                self.escrever_visor(f"Grupo duplicado encontrado com {len(arquivos_ordenados)} arquivos.")

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

        if mensagem:
            self.status_texto.set(mensagem)
        else:
            self.status_texto.set(
                f"{grupos} grupos duplicados encontrados. {total_para_mover} arquivos podem ser movidos."
            )

        self.botao_mover_selecionado.config(state="normal")
        self.botao_mover_todos.config(state="normal")
        self.botao_relatorio.config(state="normal")

        if not self.tabela.selection():
            self.botao_abrir_local.config(state="disabled")

    def preencher_tabela(self):
        self.limpar_tabela()

        grupo = 1

        for arquivos in self.duplicados.values():
            for indice, caminho in enumerate(arquivos):
                try:
                    tamanho = self.formatar_tamanho(os.path.getsize(caminho))
                except OSError:
                    tamanho = "Indisponível"

                nome = os.path.basename(caminho)
                acao = "Manter" if indice == 0 else "Mover"
                modificado = self.obter_data_modificacao(caminho)
                tag = "manter" if indice == 0 else "mover"

                self.tabela.insert(
                    "",
                    "end",
                    values=(grupo, acao, nome, tamanho, modificado, caminho),
                    tags=(tag,)
                )

            grupo += 1

    def obter_data_modificacao(self, caminho):
        try:
            timestamp = os.path.getmtime(caminho)
            return datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y %H:%M")
        except OSError:
            return "Indisponível"

    def obter_item_selecionado(self):
        item_selecionado = self.tabela.selection()

        if not item_selecionado:
            return None

        return item_selecionado[0]

    def obter_caminho_selecionado(self):
        item = self.obter_item_selecionado()

        if not item:
            return None

        valores = self.tabela.item(item, "values")

        if not valores or len(valores) < 6:
            return None

        return valores[5]

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
                    messagebox.showerror("Erro", f"Não foi possível abrir a pasta.\n\n{erro}")
                    return

            messagebox.showwarning("Atenção", "O arquivo selecionado não existe mais no local original.")
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
                messagebox.showerror("Erro", f"Não foi possível abrir o local do arquivo.\n\n{erro}")

    def mover_selecionado(self):
        item = self.obter_item_selecionado()

        if not item:
            messagebox.showwarning("Atenção", "Selecione um arquivo na tabela.")
            return

        valores = self.tabela.item(item, "values")

        if not valores or len(valores) < 6:
            return

        acao = valores[1]
        caminho = valores[5]

        if acao == "Manter":
            confirmar_manter = messagebox.askyesno(
                "Arquivo marcado para manter",
                "Esse arquivo está marcado como Manter.\n\nDeseja mover mesmo assim?"
            )

            if not confirmar_manter:
                return

        confirmar = messagebox.askyesno(
            "Confirmar movimentação",
            f"Deseja mover este arquivo para a pasta de revisão?\n\n{caminho}"
        )

        if not confirmar:
            return

        try:
            destino = self.criar_destino_seguro(caminho)
            shutil.move(caminho, destino)

            self.remover_caminho_dos_duplicados(caminho)
            self.total_espaco_duplicado = self.calcular_espaco_duplicado()

            self.preencher_tabela()
            self.atualizar_espaco()
            self.atualizar_resumo()
            self.atualizar_botao_revisao()
            self.atualizar_painel_resultado("Arquivo movido para revisão.")

            self.escrever_visor(f"Arquivo movido: {caminho}")
            self.escrever_visor(f"Destino: {destino}")

            messagebox.showinfo("Sucesso", "Arquivo movido para a pasta de revisão.")

        except Exception as erro:
            self.escrever_visor(f"Erro ao mover: {caminho}")
            self.escrever_visor(str(erro))
            messagebox.showerror("Erro", f"Não foi possível mover o arquivo.\n\n{erro}")

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

        if erros:
            self.status_texto.set(f"{movidos} arquivos foram movidos. Alguns não puderam ser movidos.")
            messagebox.showwarning(
                "Concluído com avisos",
                f"{movidos} arquivos foram movidos para revisão.\n\nAlguns arquivos não puderam ser movidos."
            )
            return

        self.status_texto.set(f"{movidos} arquivos foram movidos para revisão.")
        messagebox.showinfo("Concluído", f"{movidos} arquivos foram movidos para a pasta de revisão.")

    def abrir_pasta_revisao(self):
        if not self.pasta_revisao:
            pasta = self.pasta_selecionada.get().strip()

            if not pasta:
                messagebox.showwarning("Atenção", "Selecione uma pasta primeiro.")
                return

            self.pasta_revisao = os.path.join(pasta, "_duplicados_para_revisar")

        if not os.path.exists(self.pasta_revisao):
            messagebox.showwarning("Atenção", "A pasta de revisão ainda não existe.")
            return

        try:
            os.startfile(self.pasta_revisao)
            self.escrever_visor(f"Pasta de revisão aberta: {self.pasta_revisao}")
        except Exception as erro:
            messagebox.showerror("Erro", f"Não foi possível abrir a pasta de revisão.\n\n{erro}")

    def criar_destino_seguro(self, caminho_origem):
        os.makedirs(self.pasta_revisao, exist_ok=True)

        nome_arquivo = os.path.basename(caminho_origem)
        destino = os.path.join(self.pasta_revisao, nome_arquivo)

        if not os.path.exists(destino):
            return destino

        nome, extensao = os.path.splitext(nome_arquivo)
        contador = 1

        while True:
            novo_nome = f"{nome}_duplicado_{contador}{extensao}"
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

    def limpar_tabela(self):
        for item in self.tabela.get_children():
            self.tabela.delete(item)

    def limpar_resultados(self):
        self.limpar_tabela()
        self.limpar_visor()

        self.duplicados = {}
        self.total_verificados = 0
        self.total_espaco_duplicado = 0
        self.ultimo_log_progresso = 0
        self.cancelar_evento.clear()

        self.atualizar_contador()
        self.atualizar_espaco()
        self.atualizar_resumo()
        self.atualizar_botao_revisao()

        self.botao_cancelar.config(state="disabled")
        self.botao_abrir_local.config(state="disabled")
        self.botao_mover_selecionado.config(state="disabled")
        self.botao_mover_todos.config(state="disabled")
        self.botao_relatorio.config(state="disabled")
        self.botao_scan.config(state="normal")
        self.botao_atualizar.config(state="normal")

        self.status_texto.set("Resultados limpos.")
        self.escrever_visor("Resultados limpos.")

    def salvar_relatorio(self):
        if not self.duplicados:
            messagebox.showwarning("Atenção", "Não há duplicados para salvar.")
            return

        caminho_relatorio = filedialog.asksaveasfilename(
            title="Salvar relatório",
            defaultextension=".txt",
            filetypes=[("Arquivo de texto", "*.txt")]
        )

        if not caminho_relatorio:
            return

        try:
            grupos = len(self.duplicados)
            total_arquivos = sum(len(arquivos) for arquivos in self.duplicados.values())
            total_para_mover = total_arquivos - grupos

            with open(caminho_relatorio, "w", encoding="utf-8") as relatorio:
                relatorio.write("Relatório de Arquivos Duplicados\n")
                relatorio.write("=" * 50 + "\n\n")
                relatorio.write(f"Data do relatório: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
                relatorio.write(f"Pasta analisada: {self.pasta_selecionada.get()}\n")
                relatorio.write(f"Arquivos verificados: {self.total_verificados}\n")
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

                        try:
                            tamanho = self.formatar_tamanho(os.path.getsize(caminho))
                        except OSError:
                            tamanho = "Indisponível"

                        relatorio.write(f"Ação: {acao}\n")
                        relatorio.write(f"Arquivo: {os.path.basename(caminho)}\n")
                        relatorio.write(f"Tamanho: {tamanho}\n")
                        relatorio.write(f"Modificado em: {self.obter_data_modificacao(caminho)}\n")
                        relatorio.write(f"Caminho: {caminho}\n\n")

                    relatorio.write("\n")
                    grupo += 1

            self.escrever_visor(f"Relatório salvo: {caminho_relatorio}")
            messagebox.showinfo("Sucesso", "Relatório salvo com sucesso.")

        except Exception as erro:
            self.escrever_visor(f"Erro ao salvar relatório: {erro}")
            messagebox.showerror("Erro", f"Não foi possível salvar o relatório.\n\n{erro}")

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