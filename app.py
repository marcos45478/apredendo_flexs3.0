from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session  # flash para mensagens de feedback
import json
import os
import uuid  # usado para gerar IDs únicos (uuid4)
import re
from werkzeug.security import generate_password_hash, check_password_hash
from models.usuario import Usuario

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

@app.route("/")
def home():
    # Renderiza a página inicial com o formulário de cadastro
    return render_template("home.html")
   
@app.route("/cadastro-usuario")
def tela_cadastro():
    return render_template("cadastro-usuarios.html")

@app.route("/login")
def tela_login():
     return render_template("login.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        cpf_digitado = request.form.get("cpf")
        senha_digitada = request.form.get("senha")

        # 1. Limpa o CPF digitado para ficar igual ao salvo no JSON (apenas números)
        if cpf_digitado:
            cpf_limpo = re.sub(r'\D', '', cpf_digitado)
        else:
            cpf_limpo = ""

        usuarios = carregar_usuarios()

        # 2. Loop corrigido (agora só tem um)
        for usuario in usuarios:
            
            # 3. Compara usando o cpf_limpo
            if usuario["cpf"] == cpf_limpo and check_password_hash(usuario["senha"], senha_digitada):
                
                # Cria a sessão
                session["usuario_id"] = usuario["id"]
                session["usuario_nome"] = usuario["nome"]
                session["usuario_cpf"] = usuario["cpf"]
                
                flash("Login realizado com sucesso", "sucesso")

                return redirect(url_for("buscar_usuarios"))
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
        return redirect(url_for("cadastrar_usuario"))

    # --- INÍCIO DA VALIDAÇÃO E SANITIZAÇÃO ---
    

    padrao_cpf = r"^\d{3}\.\d{3}\.\d{3}-\d{2}$"
    if not re.match(padrao_cpf, cpf_digitado):
        flash("Formato de CPF inválido. Use o padrão 000.000.000-00", "erro")
        return redirect(url_for("cadastrar_usuario"))
        
    
    cpf_limpo = re.sub(r'\D', '', cpf_digitado) 
    
    # codigo de adm novo

    if cpf_limpo == "11725411083":
        perfil = "admin"
    else:
        perfil = "comum"

    senha_hash = generate_password_hash(senha)

    novo_usuario = Usuario(nome, cpf_limpo, email, idade, senha_hash, perfil)

    status = salvar_usuario(novo_usuario.to_dict())

    # --- FIM DA VALIDAÇÃO DO CPF ---

    senha_hash = generate_password_hash(senha)
    usuario = usuario(nome, cpf_digitado, email, idade, senha_hash  )
    # vai verifica ser unicidade 
    if any(u.get("cpf") == cpf_limpo for u in usuarios):
        flash("CPF já cadastrado no sistema.", "erro")
        return redirect(url_for("cadastrar_usuario"))
    
    if int(idade) < 18:
        flash("Idade mínima para cadastro é de 18 anos.", "erro")
        return redirect(url_for("cadastrar_usuario"))

    #Salva o usuário no JSON com o CPF já sanitizado
    

    status = salvar_usuario(usuario)

    if status:
        flash("Usuário cadastrado com sucesso.", "sucesso")
        return redirect(url_for('buscar_usuarios'))
    else:
        flash("Não foi possível cadastrar o usuário.", "erro")
        return redirect(url_for('home'))



@app.route("/usuarios/json", methods=["GET"])
def buscar_usuarios_json():
    usuarios = carregar_usuarios()
    return jsonify(usuarios)

#busca usuario

@app.route("/usuarios", methods=["GET"])
def buscar_usuarios():

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
    return render_template("usuarios.html", usuarios=usuarios, total=total)




@app.route("/usuarios/deletar", methods=["POST"])
def deletar_usuario():

    if session.get("perfil") != "admin":
        flash("Apenas administradores podem excluir usuários", "erro")
        return redirect(url_for("buscar_usuarios"))

    cpf = request.form.get("cpf")

    usuarios = carregar_usuarios()

    novos = [u for u in usuarios if u.get("cpf") != cpf]

    with open("usuarios.json", "w", encoding="utf-8") as arquivo:
        json.dump(novos, arquivo, indent=4)

    flash("Usuário removido", "sucesso")

    return redirect(url_for("buscar_usuarios"))

if __name__== '__main__':
    app.run(debug=True, port=5001)