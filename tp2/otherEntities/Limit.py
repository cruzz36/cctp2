class Limit:
    """
    Classe que define limites e configurações para os protocolos de comunicação.
    Armazena o tamanho do buffer e o timeout para operações de rede.
    """
    def __init__(self,buffersize = 1024):
        """
        Inicializa os limites do protocolo.
        
        Args:
            buffersize (int, optional): Tamanho máximo do buffer em bytes. Defaults to 1024.
                                       Este valor define o tamanho máximo de dados que podem ser
                                       enviados num único pacote UDP ou chunk TCP.
        
        Atributos criados:
            self.buffersize (int): Tamanho do buffer em bytes (fixo em 1024, independente do parâmetro)
            self.timeout (int): Timeout em segundos para operações de rede (2 segundos)
        
        NOTA: O parâmetro buffersize é ignorado - o valor é sempre fixo em 1024.
              Isto pode ser um bug - deveria usar self.buffersize = buffersize
        """
        self.buffersize = 1024  # Tamanho fixo do buffer (ignora o parâmetro)
        self.timeout = 2        # Timeout de 2 segundos para operações de rede