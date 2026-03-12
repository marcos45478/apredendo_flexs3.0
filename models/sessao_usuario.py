from flask import session


class SessaoUsuario:
    def __init__(self, sessao=None):
        # allow passing in a different session-like dict for testing if needed
        self.sessao = sessao or session

    def login(self, usuario):
        # usuario can be a dict (loaded from JSON) or an object with attributes
        if isinstance(usuario, dict):
            self.sessao['usuario_id'] = usuario.get('id')
            self.sessao['usuario_nome'] = usuario.get('nome')
            self.sessao['usuario_perfil'] = usuario.get('perfil', 'comum')
            self.sessao['usuario_cpf'] = usuario.get('cpf')
        else:
            self.sessao['usuario_id'] = getattr(usuario, 'id', None)
            self.sessao['usuario_nome'] = getattr(usuario, 'nome', None)
            self.sessao['usuario_perfil'] = getattr(usuario, 'perfil', 'comum')
            self.sessao['usuario_cpf'] = getattr(usuario, 'cpf', None)

    def logout(self):
        self.sessao.clear()

    def esta_logado(self):
        return 'usuario_cpf' in self.sessao

    def eh_admin(self):
        return self.sessao.get('usuario_perfil') == 'admin'

    def cpf(self):
        return self.sessao.get('usuario_cpf')

    def nome(self):
        return self.sessao.get('usuario_nome')
