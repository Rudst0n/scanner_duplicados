import os
import hashlib
import threading
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


class ScannerDuplicadosApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Scanner de Arquivos Duplicados")
        self.root.geometry("1150x760")
        self.root.minsize(1000, 650)

        self.pasta_selecionada = tk.StringVar()
        self.status_texto = tk.StringVar(value="Selecione uma pasta para iniciar.")
        self.duplicados = {}
        self.pasta_revisao = ""

        self.criar_interface()

    def criar_interface(self):
        frame_principal = tk.Frame(self.root, padx=15, pady=15)
        frame_principal.pack(fill="both", expand=True)

        titulo = tk.Label(
            frame_principal,
            text="Scanner de Arquivos Duplicados",
            font=("Segoe UI", 18, "bold")
        )
        titulo.pack(anchor="w")

        subtitulo = tk.Label(
            frame_principal,
            text="Localize arquivos duplicados pelo conteúdo e mova os repetidos para revisão.",
            font=("Segoe UI", 10)
        )
        subtitulo.pack(anchor="w", pady=(0, 15))

        frame_pasta = tk.Frame(frame_principal)
        frame_pasta.pack(fill="x", pady=(0, 10))

        entrada_pasta = tk.Entry(
            frame_pasta,
            textvariable=self.pasta_selecionada,
            font=("Segoe UI", 10)
        )
        entrada_pasta.pack(side="left", fill="x", expand=True, padx=(0, 10))

        botao_pasta = tk.Button(
            frame_pasta,
            text="Escolher pasta",
            command=self.escolher_pasta,
            width=16
        )
        botao_pasta.pack(side="left")

        frame_botoes = tk.Frame(frame_principal)
        frame_botoes.pack(fill="x", pady=(0, 10))

        self.botao_scan = tk.Button(
            frame_botoes,
            text="Iniciar scanner",
            command=self.iniciar_scanner,
            width=18,
            bg="#1f6feb",
            fg="white"
        )
        self.botao_scan.pack(side="left", padx=(0, 10))

        self.botao_mover_selecionado = tk.Button(
            frame_botoes,
            text="Mover selecionado",
            command=self.mover_selecionado,
            width=18,
            bg="#b42318",
            fg="white",
            state="disabled"
        )
        self.botao_mover_selecionado.pack(side="left", padx=(0, 10))

        self.botao_mover_todos = tk.Button(
            frame_botoes,
            text="Mover duplicados",
            command=self.mover_todos_duplicados,
            width=18,
            bg="#7a271a",
            fg="white",
            state="disabled"
        )
        self.botao_mover_todos.pack(side="left", padx=(0, 10))

        self.botao_relatorio = tk.Button(
            frame_botoes,
            text="Salvar relatório",
            command=self.salvar_relatorio,
            width=18,
            state="disabled"
        )
        self.botao_relatorio.pack(side="left", padx=(0, 10))

        self.botao_limpar = tk.Button(
            frame_botoes,
            text="Limpar",
            command=self.limpar_resultados,
            width=12
        )
        self.botao_limpar.pack(side="left")

        self.progress_bar = ttk.Progressbar(
            frame_principal,
            mode="indeterminate"
        )
        self.progress_bar.pack(fill="x", pady=(5, 10))

        label_status = tk.Label(
            frame_principal,
            textvariable=self.status_texto,
            font=("Segoe UI", 10)
        )
        label_status.pack(anchor="w", pady=(0, 10))

        frame_resultado = tk.Frame(frame_principal)
        frame_resultado.pack(fill="both", expand=True)

        colunas = ("grupo", "acao", "arquivo", "tamanho", "caminho")

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
        self.tabela.heading("caminho", text="Caminho")

        self.tabela.column("grupo", width=70, anchor="center")
        self.tabela.column("acao", width=120, anchor="center")
        self.tabela.column("arquivo", width=260)
        self.tabela.column("tamanho", width=110, anchor="center")
        self.tabela.column("caminho", width=620)

        scroll_y = ttk.Scrollbar(
            frame_resultado,
            orient="vertical",
            command=self.tabela.yview
        )

        scroll_x = ttk.Scrollbar(
            frame_resultado,
            orient="horizontal",
            command=self.tabela.xview
        )

        self.tabela.configure(
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set
        )

        self.tabela.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")

        frame_resultado.grid_rowconfigure(0, weight=1)
        frame_resultado.grid_columnconfigure(0, weight=1)

        frame_visor = tk.LabelFrame(
            frame_principal,
            text="Atividade do scanner",
            padx=8,
            pady=8
        )
        frame_visor.pack(fill="both", expand=False, pady=(12, 0))

        self.visor = tk.Text(
            frame_visor,
            height=8,
            font=("Consolas", 9),
            wrap="none",
            state="disabled"
        )
        self.visor.pack(side="left", fill="both", expand=True)

        scroll_visor = ttk.Scrollbar(
            frame_visor,
            orient="vertical",
            command=self.visor.yview
        )
        scroll_visor.pack(side="right", fill="y")

        self.visor.configure(yscrollcommand=scroll_visor.set)

    def escrever_visor(self, texto):
        self.root.after(0, lambda: self.atualizar_visor(texto))

    def atualizar_visor(self, texto):
        self.visor.config(state="normal")
        self.visor.insert("end", texto + "\n")
        self.visor.see("end")
        self.visor.config(state="disabled")

    def limpar_visor(self):
        self.visor.config(state="normal")
        self.visor.delete("1.0", "end")
        self.visor.config(state="disabled")

    def escolher_pasta(self):
        pasta = filedialog.askdirectory(title="Selecione a pasta para escanear")

        if pasta:
            self.pasta_selecionada.set(pasta)
            self.pasta_revisao = os.path.join(pasta, "_duplicados_para_revisar")
            self.status_texto.set("Pasta selecionada. Clique em Iniciar scanner.")
            self.limpar_visor()
            self.escrever_visor(f"Pasta selecionada: {pasta}")

    def iniciar_scanner(self):
        pasta = self.pasta_selecionada.get().strip()

        if not pasta:
            messagebox.showwarning("Atenção", "Selecione uma pasta antes de iniciar.")
            return

        if not os.path.exists(pasta):
            messagebox.showerror("Erro", "A pasta selecionada não existe.")
            return

        self.limpar_tabela()
        self.limpar_visor()
        self.duplicados = {}
        self.pasta_revisao = os.path.join(pasta, "_duplicados_para_revisar")

        self.botao_scan.config(state="disabled")
        self.botao_mover_selecionado.config(state="disabled")
        self.botao_mover_todos.config(state="disabled")
        self.botao_relatorio.config(state="disabled")

        self.progress_bar.start(10)
        self.status_texto.set("Escaneando arquivos. Aguarde...")
        self.escrever_visor("Scanner iniciado.")
        self.escrever_visor(f"Pasta analisada: {pasta}")

        thread = threading.Thread(target=self.executar_scanner, args=(pasta,))
        thread.daemon = True
        thread.start()

    def executar_scanner(self, pasta):
        try:
            arquivos_por_tamanho = self.agrupar_por_tamanho(pasta)
            duplicados_encontrados = self.encontrar_duplicados(arquivos_por_tamanho)

            self.duplicados = duplicados_encontrados

            self.root.after(0, self.finalizar_scanner)

        except Exception as erro:
            self.root.after(0, lambda: self.erro_scanner(str(erro)))

    def agrupar_por_tamanho(self, pasta):
        arquivos_por_tamanho = {}
        total_lidos = 0

        self.escrever_visor("Verificando pastas e tamanhos dos arquivos.")

        for raiz, pastas, arquivos in os.walk(pasta):
            pastas[:] = [p for p in pastas if p != "_duplicados_para_revisar"]

            self.escrever_visor(f"Entrando na pasta: {raiz}")

            for nome_arquivo in arquivos:
                caminho_completo = os.path.join(raiz, nome_arquivo)

                try:
                    tamanho = os.path.getsize(caminho_completo)

                    if tamanho == 0:
                        self.escrever_visor(f"Ignorado arquivo vazio: {caminho_completo}")
                        continue

                    if tamanho not in arquivos_por_tamanho:
                        arquivos_por_tamanho[tamanho] = []

                    arquivos_por_tamanho[tamanho].append(caminho_completo)
                    total_lidos += 1

                    self.escrever_visor(f"Lido: {caminho_completo}")

                except PermissionError:
                    self.escrever_visor(f"Sem permissão: {caminho_completo}")
                except FileNotFoundError:
                    self.escrever_visor(f"Arquivo não encontrado: {caminho_completo}")
                except OSError:
                    self.escrever_visor(f"Não foi possível acessar: {caminho_completo}")

        self.escrever_visor(f"Arquivos verificados: {total_lidos}")

        return arquivos_por_tamanho

    def encontrar_duplicados(self, arquivos_por_tamanho):
        hashes = {}

        self.escrever_visor("Calculando assinatura dos arquivos com mesmo tamanho.")

        for tamanho, arquivos in arquivos_por_tamanho.items():
            if len(arquivos) < 2:
                continue

            self.escrever_visor(f"Analisando grupo de tamanho igual: {self.formatar_tamanho(tamanho)}")

            for caminho in arquivos:
                self.escrever_visor(f"Calculando assinatura: {caminho}")
                hash_arquivo = self.calcular_hash(caminho)

                if not hash_arquivo:
                    self.escrever_visor(f"Assinatura não calculada: {caminho}")
                    continue

                if hash_arquivo not in hashes:
                    hashes[hash_arquivo] = []

                hashes[hash_arquivo].append(caminho)

        duplicados = {}

        for hash_arquivo, arquivos in hashes.items():
            if len(arquivos) > 1:
                duplicados[hash_arquivo] = sorted(arquivos)
                self.escrever_visor(f"Duplicado encontrado: {len(arquivos)} arquivos iguais.")

        return duplicados

    def calcular_hash(self, caminho):
        sha256 = hashlib.sha256()

        try:
            with open(caminho, "rb") as arquivo:
                while True:
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

    def finalizar_scanner(self):
        self.progress_bar.stop()
        self.botao_scan.config(state="normal")

        self.preencher_tabela()

        total_grupos = len(self.duplicados)
        total_arquivos = sum(len(arquivos) for arquivos in self.duplicados.values())
        total_para_mover = total_arquivos - total_grupos

        if total_grupos == 0:
            self.status_texto.set("Nenhum arquivo duplicado encontrado.")
            self.botao_mover_selecionado.config(state="disabled")
            self.botao_mover_todos.config(state="disabled")
            self.botao_relatorio.config(state="disabled")
            self.escrever_visor("Scanner finalizado. Nenhum duplicado encontrado.")
            messagebox.showinfo("Resultado", "Nenhum arquivo duplicado foi encontrado.")
        else:
            self.status_texto.set(
                f"Foram encontrados {total_grupos} grupos de duplicados, totalizando {total_arquivos} arquivos. "
                f"{total_para_mover} podem ser movidos para revisão."
            )
            self.botao_mover_selecionado.config(state="normal")
            self.botao_mover_todos.config(state="normal")
            self.botao_relatorio.config(state="normal")
            self.escrever_visor("Scanner finalizado.")
            self.escrever_visor(f"Grupos de duplicados: {total_grupos}")
            self.escrever_visor(f"Arquivos duplicados no total: {total_arquivos}")
            self.escrever_visor(f"Arquivos que podem ser movidos: {total_para_mover}")

    def erro_scanner(self, mensagem):
        self.progress_bar.stop()
        self.botao_scan.config(state="normal")
        self.botao_mover_selecionado.config(state="disabled")
        self.botao_mover_todos.config(state="disabled")
        self.botao_relatorio.config(state="disabled")
        self.status_texto.set("Erro ao executar o scanner.")
        self.escrever_visor(f"Erro: {mensagem}")
        messagebox.showerror("Erro", mensagem)

    def preencher_tabela(self):
        self.limpar_tabela()

        grupo = 1

        for _, arquivos in self.duplicados.items():
            for indice, caminho in enumerate(arquivos):
                try:
                    tamanho = self.formatar_tamanho(os.path.getsize(caminho))
                except OSError:
                    tamanho = "Indisponível"

                nome = os.path.basename(caminho)
                acao = "Manter" if indice == 0 else "Mover"

                self.tabela.insert(
                    "",
                    "end",
                    values=(grupo, acao, nome, tamanho, caminho)
                )

            grupo += 1

    def mover_selecionado(self):
        item_selecionado = self.tabela.selection()

        if not item_selecionado:
            messagebox.showwarning("Atenção", "Selecione um arquivo na tabela.")
            return

        item = item_selecionado[0]
        valores = self.tabela.item(item, "values")

        if not valores:
            return

        acao = valores[1]
        caminho = valores[4]

        if acao == "Manter":
            confirmar_manter = messagebox.askyesno(
                "Arquivo marcado para manter",
                "Este arquivo está marcado como Manter.\n\nDeseja mover mesmo assim?"
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
            self.tabela.delete(item)
            self.status_texto.set(f"Arquivo movido para revisão: {destino}")
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

        total_grupos = len(self.duplicados)
        total_arquivos = sum(len(arquivos) for arquivos in self.duplicados.values())
        total_para_mover = total_arquivos - total_grupos

        confirmar = messagebox.askyesno(
            "Confirmar movimentação",
            f"O sistema vai manter o primeiro arquivo de cada grupo e mover os demais para revisão.\n\n"
            f"Grupos: {total_grupos}\n"
            f"Arquivos que serão movidos: {total_para_mover}\n\n"
            f"Deseja continuar?"
        )

        if not confirmar:
            return

        movidos = 0
        erros = []

        self.escrever_visor("Movimentação dos duplicados iniciada.")

        for _, arquivos in self.duplicados.items():
            arquivos_para_mover = arquivos[1:]

            for caminho in arquivos_para_mover:
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
        self.limpar_tabela()
        self.botao_mover_selecionado.config(state="disabled")
        self.botao_mover_todos.config(state="disabled")
        self.botao_relatorio.config(state="disabled")

        if erros:
            self.status_texto.set(
                f"{movidos} arquivos foram movidos para revisão. Alguns arquivos não puderam ser movidos."
            )
            self.escrever_visor("Movimentação finalizada com avisos.")
            messagebox.showwarning(
                "Concluído com avisos",
                f"{movidos} arquivos foram movidos para revisão.\n\n"
                f"Alguns arquivos não puderam ser movidos."
            )
        else:
            self.status_texto.set(
                f"{movidos} arquivos foram movidos para a pasta de revisão."
            )
            self.escrever_visor("Movimentação finalizada com sucesso.")
            messagebox.showinfo(
                "Concluído",
                f"{movidos} arquivos foram movidos para a pasta de revisão."
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
            novo_nome = f"{nome}_duplicado_{contador}{extensao}"
            novo_destino = os.path.join(self.pasta_revisao, novo_nome)

            if not os.path.exists(novo_destino):
                return novo_destino

            contador += 1

    def limpar_tabela(self):
        for item in self.tabela.get_children():
            self.tabela.delete(item)

    def limpar_resultados(self):
        self.limpar_tabela()
        self.limpar_visor()
        self.duplicados = {}
        self.botao_mover_selecionado.config(state="disabled")
        self.botao_mover_todos.config(state="disabled")
        self.botao_relatorio.config(state="disabled")
        self.status_texto.set("Resultados limpos. Selecione uma pasta para iniciar.")

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
            with open(caminho_relatorio, "w", encoding="utf-8") as relatorio:
                relatorio.write("Relatório de Arquivos Duplicados\n")
                relatorio.write("=" * 40 + "\n\n")
                relatorio.write("O primeiro arquivo de cada grupo foi marcado como Manter.\n")
                relatorio.write("Os demais foram marcados como Mover.\n\n")

                grupo = 1

                for _, arquivos in self.duplicados.items():
                    relatorio.write(f"Grupo {grupo}\n")
                    relatorio.write("-" * 30 + "\n")

                    for indice, caminho in enumerate(arquivos):
                        try:
                            tamanho = self.formatar_tamanho(os.path.getsize(caminho))
                        except OSError:
                            tamanho = "Indisponível"

                        acao = "Manter" if indice == 0 else "Mover"

                        relatorio.write(f"Ação: {acao}\n")
                        relatorio.write(f"Arquivo: {os.path.basename(caminho)}\n")
                        relatorio.write(f"Tamanho: {tamanho}\n")
                        relatorio.write(f"Caminho: {caminho}\n\n")

                    relatorio.write("\n")
                    grupo += 1

            self.escrever_visor(f"Relatório salvo: {caminho_relatorio}")
            messagebox.showinfo("Sucesso", "Relatório salvo com sucesso.")

        except Exception as erro:
            self.escrever_visor(f"Erro ao salvar relatório: {erro}")
            messagebox.showerror(
                "Erro",
                f"Não foi possível salvar o relatório.\n\n{erro}"
            )

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