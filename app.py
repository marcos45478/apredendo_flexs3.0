from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session  # flash para mensagens de feedback
import json
import os
import uuid  # usado para gerar IDs únicos (uuid4)
import re
from werkzeug.security import generate_password_hash, check_password_hash
from models.usuario import Usuario
from models.sessao_usuario import SessaoUsuario

app = Flask(__name__)
# chave necessária para utilizar `flash` e sessões
app.secret_key = "chave-super-secreta"

def carregar_usuarios():
    # Verifica se o arquivo 'usuarios.json' existe e carrega os dados
    try:
        if os.path.exists("usuarios.json"):
            with open("usuarios.json", "r", encoding="utf-8") as arquivo:
                return json.load(arquivo)
        else:
            return []  # Retorna uma lista vazia se o arquivo não existir
    except:
        return []  # Retorna uma lista vazia se ocorrer algum erro ao ler o arquivo
   
def salvar_usuario(usuario):
    # Carrega os usuários existentes
    usuarios = carregar_usuarios()

    try:
        # Adiciona o novo usuário à lista
        usuarios.append(usuario)

        # Salva a lista atualizada de usuários no arquivo 'usuarios.json'
        with open("usuarios.json", "w", encoding="utf-8") as arquivo:
            json.dump(usuarios, arquivo, indent=4)

        return True  # Retorna True se o salvamento for bem-sucedido
    except:
        return False  # Retorna False se ocorrer um erro ao salvar

def atualizar_usuario(cpf, dados_atualizados):
    # Carrega os usuários existentes
    usuarios = carregar_usuarios()

    try:
        # Encontra e atualiza o usuário
        for i, usuario in enumerate(usuarios):
            if usuario["cpf"] == cpf:
                usuarios[i].update(dados_atualizados)
                break

        # Salva a lista atualizada de usuários no arquivo 'usuarios.json'
        with open("usuarios.json", "w", encoding="utf-8") as arquivo:
            json.dump(usuarios, arquivo, indent=4)

        return True
    except:
        return False

@app.route("/")
def home():
    # Renderiza a página inicial com o formulário de cadastro
    return render_template("home.html")

@app.route("/tela-login")
def tela_login():
    return render_template("login.html")
   
@app.route("/cadastro-usuario")
def tela_cadastro():
    return render_template("cadastro-usuarios.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        cpf_digitado = request.form.get("cpf")
        senha_digitada = request.form.get("senha")

        # Limpa o CPF digitado para ficar igual ao salvo no JSON (apenas números)
        if cpf_digitado:
            cpf_limpo = re.sub(r'\D', '', cpf_digitado)
        else:
            cpf_limpo = ""

        usuarios = carregar_usuarios()

        # Procura o usuário com o CPF e valida a senha
        for usuario in usuarios:
            if usuario["cpf"] == cpf_limpo and check_password_hash(usuario["senha"], senha_digitada):
                # Cria a sessão usando a classe apropriada
                sess = SessaoUsuario(session)
                sess.login(usuario)

                flash("Login realizado com sucesso", "sucesso")
                return redirect(url_for("buscar_usuarios"))
        
        flash("CPF ou senha inválidos.", "erro")
        return redirect(url_for("tela_login"))
    
    return render_template("login.html")
@app.route("/cadastro-usuario", methods=["POST"])
def cadastrar_usuario():
    # Recupera os dados
    nome = request.form.get("nome")
    cpf_digitado = request.form.get("cpf") # Recebe o CPF com a máscara do JS
    email = request.form.get("email")
    idade = request.form.get("idade")
    senha = request.form.get("senha")
    
    # Validação básica
    if not all([nome, cpf_digitado, email, idade, senha]):
        flash("Todos os campos são obrigatórios.", "erro")
        return redirect(url_for("tela_cadastro"))

    # Validação do formato de CPF
    padrao_cpf = r"^\d{3}\.\d{3}\.\d{3}-\d{2}$"
    if not re.match(padrao_cpf, cpf_digitado):
        flash("Formato de CPF inválido. Use o padrão 000.000.000-00", "erro")
        return redirect(url_for("tela_cadastro"))
    
    # Sanitiza o CPF (remove caracteres especiais)
    cpf_limpo = re.sub(r'\D', '', cpf_digitado)
    
    # Carrega usuários para verificar unicidade
    usuarios = carregar_usuarios()
    
    # Verifica se CPF já está cadastrado
    if any(u.get("cpf") == cpf_limpo for u in usuarios):
        flash("CPF já cadastrado no sistema.", "erro")
        return redirect(url_for("tela_cadastro"))
    
    # Valida a idade
    try:
        idade_int = int(idade)
        if idade_int < 18:
            flash("Idade mínima para cadastro é de 18 anos.", "erro")
            return redirect(url_for("tela_cadastro"))
    except ValueError:
        flash("Idade deve ser um número válido.", "erro")
        return redirect(url_for("tela_cadastro"))

    # Define o perfil (admin ou comum)
    if cpf_limpo == "11725411083":
        perfil = "admin"
    else:
        perfil = "comum"

    # Criptografa a senha
    senha_hash = generate_password_hash(senha)

    # Cria o novo usuário
    novo_usuario = Usuario(nome, cpf_limpo, email, idade, senha_hash, perfil)

    # Salva o usuário no JSON
    status = salvar_usuario(novo_usuario.to_dict())

    if status:
        flash("Usuário cadastrado com sucesso.", "sucesso")
        return redirect(url_for('buscar_usuarios'))
    else:
        flash("Não foi possível cadastrar o usuário.", "erro")
        return redirect(url_for('tela_cadastro'))



@app.route("/usuarios/json", methods=["GET"])
def buscar_usuarios_json():
    usuarios = carregar_usuarios()
    return jsonify(usuarios)

#busca usuario

@app.route("/usuarios", methods=["GET"])
def buscar_usuarios():
    # Verifica se o usuário está logado
    if "usuario_cpf" not in session:
        flash("Você precisa estar logado para acessar essa página", "erro")
        return redirect(url_for("tela_login"))

    cpf_busca = request.args.get("cpf")
    ordem = request.args.get("ordem")
    #Carrega todos
    usuarios = carregar_usuarios()

    if cpf_busca:
        usuarios = [u for u in usuarios if u.get("cpf") == cpf_busca]

    if ordem == "crescente":
        usuarios = sorted(usuarios, key=lambda x: int(x["idade"]))

    elif ordem == "decrescente":
        usuarios = sorted(usuarios, key=lambda x: int(x["idade"]), reverse=True)

    #Calcula o total e vai renderiza a página
    total = len(usuarios)
    return render_template("usuarios.html", usuarios=usuarios, total=total, session=session)




@app.route("/usuarios/deletar", methods=["POST"])
def deletar_usuario():
    # Verifica se o usuário está logado
    sessao = SessaoUsuario(session)
    if not sessao.esta_logado():
        flash("Você precisa estar logado", "erro")
        return redirect(url_for("tela_login"))
    
    # Verifica se é admin
    if not sessao.eh_admin():
        flash("Apenas administradores podem excluir usuários", "erro")
        return redirect(url_for("buscar_usuarios"))

    cpf = request.form.get("cpf")
    
    # Validação adicional - admin não pode deletar a si mesmo
    if cpf == session.get("usuario_cpf"):
        flash("Você não pode deletar sua própria conta", "erro")
        return redirect(url_for("buscar_usuarios"))

    usuarios = carregar_usuarios()

    novos = [u for u in usuarios if u.get("cpf") != cpf]

    with open("usuarios.json", "w", encoding="utf-8") as arquivo:
        json.dump(novos, arquivo, indent=4)

    flash("Usuário removido", "sucesso")

    return redirect(url_for("buscar_usuarios"))

@app.route("/logout")
def logout():
    sess = SessaoUsuario(session)
    sess.logout()
    flash("Logout realizado com sucesso", "sucesso")
    return redirect(url_for("home"))

@app.route("/editar-perfil", methods=["GET", "POST"])
def editar_perfil():
    # Verifica se o usuário está logado
    sessao = SessaoUsuario(session)

    if not sessao.esta_logado():
        flash("Você precisa estar logado para editar seu perfil", "erro")
        return redirect(url_for("tela_login"))
    
    cpf_usuario = sessao.cpf()
    usuarios = carregar_usuarios()
    
    # Encontra o usuário atual
    usuario_atual = None
    for u in usuarios:
        if u["cpf"] == cpf_usuario:
            usuario_atual = u
            break
    
    if not usuario_atual:
        flash("Usuário não encontrado", "erro")
        return redirect(url_for("buscar_usuarios"))
    
    if request.method == "POST":
        nome = request.form.get("nome")
        email = request.form.get("email")
        idade = request.form.get("idade")
        senha_atual = request.form.get("senha_atual")
        senha_nova = request.form.get("senha_nova")
        
        # Validação básica
        if not all([nome, email, idade]):
            flash("Nome, email e idade são obrigatórios.", "erro")
            return redirect(url_for("editar_perfil"))
        
        # Valida idade
        try:
            idade_int = int(idade)
            if idade_int < 18:
                flash("Idade mínima é 18 anos.", "erro")
                return redirect(url_for("editar_perfil"))
        except ValueError:
            flash("Idade deve ser um número válido.", "erro")
            return redirect(url_for("editar_perfil"))
        
        # Se quer mudar senha, verifica a senha atual
        if senha_nova and senha_nova.strip():
            if not senha_atual or not senha_atual.strip():
                flash("Você deve fornecer a senha atual para mudar a senha.", "erro")
                return redirect(url_for("editar_perfil"))
            
            if not check_password_hash(usuario_atual["senha"], senha_atual):
                flash("Senha atual incorreta.", "erro")
                return redirect(url_for("editar_perfil"))
            
            if len(senha_nova) < 6:
                flash("A nova senha deve ter no mínimo 6 caracteres.", "erro")
                return redirect(url_for("editar_perfil"))
            
            senha_hash = generate_password_hash(senha_nova)
        else:
            senha_hash = usuario_atual["senha"]
        
        # Atualiza os dados
        dados_atualizados = {
            "nome": nome,
            "email": email,
            "idade": idade,
            "senha": senha_hash
        }
        
        if atualizar_usuario(cpf_usuario, dados_atualizados):
            # Atualiza os dados na sessão também
            session["usuario_nome"] = nome
            flash("Perfil atualizado com sucesso!", "sucesso")
            return redirect(url_for("buscar_usuarios"))
        else:
            flash("Erro ao atualizar perfil.", "erro")
            return redirect(url_for("editar_perfil"))
    
    return render_template("editar-perfil.html", usuario=usuario_atual)

if __name__== '__main__':
    app.run(debug=True, port=5001)