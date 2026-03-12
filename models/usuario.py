import uuid

class Usuario:

    def __init__(self, nome, cpf, email, idade, senha, perfil="comum"):
        self.id = str(uuid.uuid4())
        self.nome = nome
        self.cpf = cpf
        self.email = email
        self.idade = idade
        self.senha = senha
        self.perfil = perfil

    def eh_maior_de_idade(self):
        return int(self.idade) >= 18

    def eh_admin(self):
        return self.perfil == "admin"

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "cpf": self.cpf,
            "email": self.email,
            "idade": self.idade,
            "senha": self.senha,
            "perfil": self.perfil
        }
