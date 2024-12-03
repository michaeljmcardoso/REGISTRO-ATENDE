import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import matplotlib.pyplot as plt
from datetime import datetime

# Função para hash de senha
def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

# Inicializar banco de dados
def iniciar_banco_de_dados():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Tabela para atendimentos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS atendimentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            atendente TEXT,
            interessado TEXT,
            comunidade TEXT,
            municipio TEXT,
            telefone TEXT,
            email TEXT,
            protocolo TEXT,
            data DATE,
            motivo TEXT
        )
    ''')
    
    # Tabela para usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE,
            senha TEXT
        )
    ''')
    
    # Adicionar um usuário administrador (somente na primeira execução)
    cursor.execute('SELECT COUNT(*) FROM usuarios')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO usuarios (usuario, senha) VALUES (?, ?)', 
                       ('admin', hash_senha('admin123')))
        st.info("Usuário administrador criado.")
    
    conn.commit()
    conn.close()

def obter_todos_os_registros():
    conn = sqlite3.connect('database.db')
    df = pd.read_sql_query('SELECT * FROM atendimentos', conn)
    conn.close()
    return df

def obter_registro_por_id(item_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM atendimentos WHERE id = ?", (item_id,))
    registro = cursor.fetchone()
    conn.close()
    return registro

# Verificar credenciais
def verificar_credenciais(usuario, senha):
    conn = sqlite3.connect('database.db')  # Corrigido para usar o mesmo banco de dados
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM usuarios WHERE usuario = ? AND senha = ?', (usuario, hash_senha(senha)))
    dados = cursor.fetchone()
    conn.close()
    return dados is not None

# Inicializar banco de dados
iniciar_banco_de_dados()

# Tela de login
def tela_login():
    st.markdown('<h2 style="color: "#1f77b4";">Login</h2>', unsafe_allow_html=True)
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    
    if st.button("Entrar"):
        if verificar_credenciais(usuario, senha):
            st.session_state['usuario_logado'] = usuario
            st.success(f"Bem-vindo, {usuario}!")
            st.experimental_rerun()
        else:
            st.error("Credenciais inválidas.")

# Página inicial (após login)
def pagina_inicial():
    st.markdown('<h1 style="color: "#1f77b4";">Registro de Atendimentos</h1>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        atendente = st.text_input("Nome do Atendente", max_chars=50, key="atendente", help="Preencha os campos")
        interessado = st.text_input("Nome do Interessado", max_chars=50, key="nome_interessado")
        telefone = st.text_input("Telefone", max_chars=13, key="fone", placeholder="DDD + numero do telefone")
        protocolo = st.text_input("Protocolo SEI", max_chars=22, key="protocolo", placeholder="Nº do Documento ou Processo SEI")

    with col2:
        comunidade = st.text_input("Comunidade")
        municipio = st.text_input("Município")
        email = st.text_input("Email", placeholder="exemplo@email.com")
        data = st.date_input("Data", datetime.today())

    motivo = st.text_area("Motivo do Atendimento", height=100, help="Digite o motivo do atendimento")

    if st.button("Salvar"):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        if atendente:
            cursor.execute('''INSERT INTO atendimentos (atendente, interessado, comunidade, municipio, telefone, email, protocolo, data, motivo)
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                           (atendente, interessado, comunidade, municipio, telefone, email, protocolo, data, motivo))
            conn.commit()
            st.success(f"Obrigado, {atendente}. Os dados foram salvos com sucesso!")
        else:
            st.error("Por favor, preencha o campo 'Nome'.")
        conn.close()

    st.subheader("Registros Salvos")
    df = obter_todos_os_registros()
    if not df.empty:
        if 'id' in df.columns:
            df = df.drop(columns=['id'])
            df.index = df.index + 1
            st.dataframe(df)

    if st.button("Exportar para Excel"):
        df.to_excel('atendimentos.xlsx', index=False)
        st.success("Dados exportados com sucesso para atendimentos.xlsx")
        with open("atendimentos.xlsx", "rb") as file:
            st.download_button(
                label="Baixar Excel",
                data=file,
                file_name="atendimentos.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# Página de Edição: Atualização de registros existentes
def pagina_editar():
    st.header("Editar Registro")

    st.subheader("Registros Salvos")
    df = obter_todos_os_registros()
    if not df.empty:
        if 'id' in df.columns:
            df = df.drop(columns=['id'])  # Remove a coluna 'id'
            df.index = df.index + 1  # Ajusta o índice para começar em 1
            st.dataframe(df)

        item_id = st.number_input("Digite o ID do Registro para Editar", min_value=1, step=1)
        registro = obter_registro_por_id(item_id)

        if registro:
            st.subheader("Atualizar Registro")

            col1, col2 = st.columns(2)
            with col1:
                new_atendente = st.text_input("Nome do Atendente", value=registro[1])
                new_interessado = st.text_input("Nome do Interessado", value=registro[2])
                new_comunidade = st.text_input("Comunidade", value=registro[3])
                new_municipio = st.text_input("Município", value=registro[4])

            with col2:
                new_telefone = st.text_input("Telefone", value=registro[5])
                new_email = st.text_input("Email", value=registro[6])
                new_protocolo = st.text_input("Protocolo SEI", value=registro[7])
                new_data = st.date_input("Data", datetime.strptime(registro[8], '%Y-%m-%d'))

            new_motivo = st.text_area("Motivo do Atendimento", value=registro[9], height=100)

            if st.button("Atualizar"):
                conn = sqlite3.connect('database.db')
                cursor = conn.cursor()
                cursor.execute('''
                UPDATE atendimentos
                SET atendente = ?, interessado = ?, comunidade = ?, municipio = ?, telefone = ?, email = ?, protocolo = ?, data = ?, motivo = ?
                WHERE id = ?
                ''', (new_atendente, new_interessado, new_comunidade, new_municipio, new_telefone, new_email, new_protocolo, new_data, new_motivo, item_id))
                conn.commit()
                st.success(f"Obrigado, {new_atendente}. Registro atualizado com sucesso!")
                
                # Atualizar a exibição da tabela
                df = obter_todos_os_registros()
                if 'id' in df.columns:
                    df = df.drop(columns=['id'])
                    df.index = df.index + 1
                    st.dataframe(df)
        else:
            st.warning("ID inválido. Por favor, selecione um ID existente.")

# Função para gráfico de atendimentos por município
def grafico_atendimentos_por_municipio(df):
    municipio_counts = df['municipio'].value_counts()
    fig, ax = plt.subplots(figsize=(10, 5))
    municipio_counts.plot(kind='bar', color='skyblue', ax=ax)
    ax.set_xlabel("Município")
    ax.set_ylabel("Número de Atendimentos")
    ax.set_title("Atendimentos por Município")
    st.pyplot(fig)

# Função para gráfico de atendimentos por data
def grafico_atendimentos_por_data(df):
    df['data'] = pd.to_datetime(df['data'], format='%Y-%m-%d')
    df.sort_values(by='data', inplace=True)
    df['contador'] = 1
    df_acumulado = df.groupby('data').contador.sum().cumsum().reset_index()
    
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df_acumulado['data'], df_acumulado['contador'], marker='o', color='blue')

    for i in range(len(df_acumulado)):
        ax.text(df_acumulado['data'][i], df_acumulado['contador'][i], 
                str(df_acumulado['contador'][i]), 
                ha='center', va='bottom', fontsize=10)

    ax.set_xlabel("Data")
    ax.set_ylabel("Atendimentos Acumulados")
    ax.set_title("Atendimentos por Data (Série Temporal)")
    ax.grid(True)
    plt.xticks(rotation=45)
    st.pyplot(fig)

# Função para Página de Visualizações
def pagina_visualizacoes():
    st.subheader("Visualizações de Dados")
    
    # Recarregar os registros
    if 'atualizar' in st.experimental_get_query_params():
        st.experimental_set_query_params()  # Limpa os parâmetros de atualização

    df = obter_todos_os_registros()

    if not df.empty:
        st.write("Tabela de Atendimentos")
        if 'id' in df.columns:
            df = df.drop(columns=['id'])
            df.index = df.index + 1  # Ajusta o índice para começar em 1

            st.dataframe(df)

        # Menu para selecionar visualização
        opcao = st.selectbox(
            "Escolha a visualização",
            ["Selecione...", "Atendimentos por Município", "Atendimentos por Data"]
        )

        if opcao == "Atendimentos por Município":
            st.write("Gráfico de Atendimentos por Município")
            grafico_atendimentos_por_municipio(df)

        elif opcao == "Atendimentos por Data":
            st.write("Gráfico de Atendimentos por Data de Abertura")
            grafico_atendimentos_por_data(df)
        
# Função para Página Sobre
def pagina_about():
    st.subheader("Sobre o Projeto")
    st.write("""
        Sistema de registro de atendimentos.
        Projeto experimental focado em otimizar o registro, visualização e consulta dos atendimentos realizados.
        Desenvolvido por **Michael JM Cardoso**.
    """)

# Adicionar novos usuários ao banco de dados
def adicionar_usuario(usuario, senha):
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO usuarios (usuario, senha) VALUES (?, ?)', 
                       (usuario, hash_senha(senha)))
        conn.commit()
        conn.close()
        return True, f"Usuário '{usuario}' adicionado com sucesso!"
    except sqlite3.IntegrityError:
        return False, f"Usuário '{usuario}' já existe."
    except Exception as e:
        return False, f"Erro ao adicionar usuário: {str(e)}"


if 'usuario_logado' not in st.session_state:
    tela_login()
else:
    # Menu de navegação
    st.sidebar.title(f"Bem-vindo, {st.session_state['usuario_logado']}")
    if st.sidebar.button("Sair"):
        del st.session_state['usuario_logado']
        st.experimental_rerun()
    
    # Adicionar "Gerenciar Usuários" apenas para o admin
    opcoes_paginas = ["Página Inicial", "Editar Registro", "Visualizações", "Sobre"]
    if st.session_state['usuario_logado'] == "admin":
        opcoes_paginas.insert(3, "Gerenciar Usuários")  # Insere antes da página "Sobre"

    pagina_selecionada = st.sidebar.radio("Selecione uma Página", opcoes_paginas)

    # Função para gerenciar usuários (acessível apenas pelo admin)
    def gerenciar_usuarios():
        st.header("Gerenciar Usuários")
        st.subheader("Adicionar Novo Usuário")

        col1, col2 = st.columns(2)
        with col1:
            novo_usuario = st.text_input("Novo Usuário")
        with col2:
            nova_senha = st.text_input("Senha", type="password")

        if st.button("Adicionar Usuário"):
            if novo_usuario and nova_senha:
                sucesso, mensagem = adicionar_usuario(novo_usuario, nova_senha)
                if sucesso:
                    st.success(mensagem)
                else:
                    st.error(mensagem)
            else:
                st.warning("Por favor, preencha todos os campos.")

        st.subheader("Usuários Cadastrados")
        conn = sqlite3.connect('database.db')
        usuarios = pd.read_sql_query("SELECT id, usuario FROM usuarios", conn)
        conn.close()

        if not usuarios.empty:
            usuarios = usuarios.rename(columns={"id": "ID", "usuario": "Usuário"})
            st.dataframe(usuarios, use_container_width=True)

    # Redirecionamento de páginas
    if pagina_selecionada == "Página Inicial":
        pagina_inicial()
    elif pagina_selecionada == "Editar Registro":
        pagina_editar()
    elif pagina_selecionada == "Visualizações":
        pagina_visualizacoes()
    elif pagina_selecionada == "Gerenciar Usuários":
        if st.session_state['usuario_logado'] == "admin":
            gerenciar_usuarios()
        else:
            st.error("Você não tem permissão para acessar esta página.")
    elif pagina_selecionada == "Sobre":
        pagina_about()
